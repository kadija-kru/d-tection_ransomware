
import os
import numpy as np
import pandas as pd
import joblib
from collections import defaultdict
from typing import List, Dict, Any, Optional

class RansomwareEnv:
    """
    A simple Gym-like environment for offline ransomware detection using dataset rows as steps.
    Episodes are sequences of rows grouped by `group_by` column (SeedAddress or Clusters).
    State returned is the preprocessed feature vector (pipeline.transform) for the current row,
    enriched with optionally computed "recent" aggregation features computed only from past rows
    of the same episode (no future peeking).
    """

    def __init__(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        pipeline_path: str = "/content/d-tection_ransomware/models/feature_pipeline.pkl",
        group_by: str = "SeedAddress",
        min_episode_length: int = 1,
        reward_config: Optional[Dict[str, float]] = None,
        time_window_sec: int = 60,
        time_col: str = "Time",
        label_col: str = "risk",
        drop_cols: Optional[List[str]] = None,
        shuffle_episodes: bool = True,
        random_state: int = 42
    ):
        """
        Args:
            df: raw dataframe (must include feature_cols, group_by, time_col, label_col)
            feature_cols: list of columns (raw) that the saved pipeline expects (in same order)
            pipeline_path: path to the saved preprocessing pipeline (joblib file)
            group_by: column name to group episodes by, e.g. "SeedAddress" or "Clusters"
            min_episode_length: drop episodes shorter than this
            reward_config: mapping for reward shaping (see defaults below)
            time_window_sec: window in seconds to compute "recent_count" features (uses time_col)
            time_col: name of time column in df
            label_col: binary label column ("risk"), 1=ransomware, 0=benign
            drop_cols: columns to drop from state if present
            shuffle_episodes: if True, episodes are shuffled on reset for training variability
            random_state: RNG seed for shuffling
        """

        self.df_raw = df.copy().reset_index(drop=True)
        self.feature_cols = feature_cols
        self.time_col = time_col
        self.label_col = label_col
        self.group_by = group_by
        self.time_window = time_window_sec
        self.drop_cols = drop_cols or []
        self.random_state = random_state

        # Default reward config (you can override)
        default_reward = {
            "allow_benign": 1.0,
            "block_benign": -1.0,
            "block_ransom": 2.0,
            "allow_ransom": -5.0,
            "step_penalty": 0.0
        }
        if reward_config is None:
            self.reward_config = default_reward
        else:
            rc = default_reward.copy()
            rc.update(reward_config)
            self.reward_config = rc

        # Load preprocessing pipeline
        if not os.path.exists(pipeline_path):
            raise FileNotFoundError(f"Preprocessing pipeline not found at {pipeline_path}")
        self.pipeline = joblib.load(pipeline_path)

        # Build episodes
        self.episodes = self._build_episodes(min_episode_length=min_episode_length, shuffle=shuffle_episodes)

        # State of current episode
        self.current_episode_idx = None
        self.current_step_idx = None
        self.current_episode = None
        self.rng = np.random.RandomState(self.random_state)

        # Action space info
        self.action_space = [0, 1]  # 0: allow, 1: block

        # Observation shape placeholder (filled on reset)
        self.observation_shape = None

    def _build_episodes(self, min_episode_length=1, shuffle=True):
        """
        Group rows by self.group_by and produce a list of lists of row indices,
        sorted by time within each group. Drops short episodes.
        """
        if self.group_by not in self.df_raw.columns:
            # fallback to Clusters
            if "Clusters" in self.df_raw.columns:
                self.group_by = "Clusters"
            else:
                raise ValueError(f"Group by column {self.group_by} not found in dataframe")

        groups = self.df_raw.groupby(self.group_by)
        episodes = []
        for key, grp in groups:
            grp_sorted = grp.sort_values(by=self.time_col)
            idxs = grp_sorted.index.to_list()
            if len(idxs) >= min_episode_length:
                episodes.append(idxs)

        if shuffle:
            rng = np.random.RandomState(self.random_state)
            rng.shuffle(episodes)

        return episodes

    def _compute_recent_counts(self, indices: List[int], current_pos: int):
        """
        Compute aggregation features only using past rows within the same episode.
        Example: count rows in [t - time_window, t)
        Returns dict of additional features that do NOT peek into future.
        """
        idx_now = indices[current_pos]
        t_now = self.df_raw.at[idx_now, self.time_col]
        # Count previous events in the same episode within time window
        count = 0
        bytes_sum = 0
        for j in range(0, current_pos):
            idx_prev = indices[j]
            t_prev = self.df_raw.at[idx_prev, self.time_col]
            if t_now - t_prev <= self.time_window:
                count += 1
                bytes_sum += self.df_raw.at[idx_prev, "Netflow_Bytes"]
        avg_bytes_past = bytes_sum / (count + 1e-9) if count > 0 else 0.0
        return {"recent_count": count, "recent_avg_bytes": avg_bytes_past}

    def reset(self, episode_index: Optional[int] = None):
        """
        Reset environment to a new episode.
        If episode_index is None -> pick a random episode.
        Returns initial state (processed vector).
        """
        if episode_index is None:
            self.current_episode_idx = self.rng.randint(0, len(self.episodes))
        else:
            self.current_episode_idx = episode_index % len(self.episodes)

        self.current_episode = self.episodes[self.current_episode_idx]
        self.current_step_idx = 0

        # Build initial state using the row at position 0 (no future peeking)
        state = self._get_state(self.current_step_idx)
        return state

    def _get_state(self, step_pos: int):
        """
        Build raw-state for the row at step_pos of current_episode, then apply pipeline.transform
        Returns numpy vector
        """
        idx = self.current_episode[step_pos]
        row = self.df_raw.loc[idx].copy()

        # Compute recent aggregation features (from past rows only)
        agg = self._compute_recent_counts(self.current_episode, step_pos)
        # Add aggregations to row (these must be included in pipeline or appended to vector)
        # If pipeline doesn't expect these, we'll append them after pipeline transform.
        row["recent_count"] = agg["recent_count"]
        row["recent_avg_bytes"] = agg["recent_avg_bytes"]

        # Drop any columns not expected
        for c in self.drop_cols:
            if c in row:
                row = row.drop(labels=[c])

        # Prepare DataFrame with required feature_cols (the pipeline expects these)
        # If pipeline was trained without recent_count etc., we handle them separately.
        # We'll attempt to transform the expected columns and then append the recent features.

        raw_input_df = pd.DataFrame([row[self.feature_cols]])
        # Use pipeline to transform
        processed = self.pipeline.transform(raw_input_df)  # sparse matrix or ndarray

        # Convert to dense numpy array
        if hasattr(processed, "toarray"):
            processed = processed.toarray()

        processed = np.asarray(processed).reshape(-1)  # 1D vector

        # Append aggregation features (standardize? pipeline doesn't include them)
        # To be safe, append raw aggregation features (small magnitude) - optionally scale later.
        processed = np.concatenate([processed, np.array([agg["recent_count"], agg["recent_avg_bytes"]])])

        # Save observation shape on first use
        if self.observation_shape is None:
            self.observation_shape = processed.shape

        return processed

    def step(self, action: int):
        """
        Apply action at current step, return (next_state, reward, done, info)
        - action: 0=allow, 1=block
        """
        assert action in self.action_space, f"Invalid action {action}"

        idx = self.current_episode[self.current_step_idx]
        true_label = int(self.df_raw.at[idx, self.label_col])  # 1 = ransomware

        # Reward calculation
        reward = self._calc_reward(action, true_label)

        # Optionally add step/time penalty
        reward += self.reward_config.get("step_penalty", 0.0)

        # Move to next position
        self.current_step_idx += 1
        done = False
        info = {"idx": idx, "label": true_label}

        if self.current_step_idx >= len(self.current_episode):
            next_state = None
            done = True
        else:
            next_state = self._get_state(self.current_step_idx)

        return next_state, reward, done, info

    def _calc_reward(self, action: int, true_label: int) -> float:
        """
        Reward mapping:
        action=0 allow, action=1 block
        true_label: 0 benign, 1 ransomware
        """
        if action == 0 and true_label == 0:
            return float(self.reward_config["allow_benign"])
        if action == 1 and true_label == 0:
            return float(self.reward_config["block_benign"])
        if action == 1 and true_label == 1:
            return float(self.reward_config["block_ransom"])
        if action == 0 and true_label == 1:
            return float(self.reward_config["allow_ransom"])
        return 0.0

    def render(self, mode="human"):
        """
        Optional: print simple status
        """
        if self.current_episode is None:
            print("Env not initialized. Call reset() first.")
            return
        pos = self.current_step_idx
        total = len(self.current_episode)
        print(f"Episode {self.current_episode_idx} pos {pos}/{total}")

    def get_action_space(self):
        return self.action_space

    def get_observation_shape(self):
        return self.observation_shape

    def num_episodes(self):
        return len(self.episodes)


