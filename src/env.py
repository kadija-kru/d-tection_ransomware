import numpy as np
import pandas as pd
import joblib
from sklearn.utils import shuffle

class RansomwareEnv:
    """
    Reinforcement-learning environment simulating
    sequential netflow decisions.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        feature_cols: list,
        pipeline_path: str,
        group_by: str = "SeedAddress",
        drop_cols: list = None
    ):
        self.df = df.copy()

        # Group flows into episodes
        self.group_by = group_by
        self.episodes = [
            g for _, g in df.groupby(group_by)
        ]
        self.num_episodes = len(self.episodes)
        self.feature_cols = feature_cols

        # Load preprocessing pipeline
        self.pipeline = joblib.load(pipeline_path)

        # drop columns
        self.drop_cols = drop_cols or []
        
        # RL internals
        self.current_episode = None
        self.t = 0

        # Actions: 0=allow, 1=block
        self.action_space = [0, 1]

    def reset(self):
        """Start a new episode"""
        # choose random episode
        self.current_episode = shuffle(self.episodes)[0].reset_index(drop=True)
        self.t = 0
        return self._get_state(self.current_episode.iloc[self.t])

    def _get_state(self, row):
        """Transform raw → processed feature vector"""
        raw = row[self.feature_cols]
        processed = self.pipeline.transform(pd.DataFrame([raw]))
        return processed.flatten()

    def step(self, action):
        """Return next_state, reward, done, info"""

        row = self.current_episode.iloc[self.t]

        # GT label
        label = row["risk"]  # 0 good, 1 ransomware

        # reward
        reward = +1 if (label == action) else -1

        # move forward
        self.t += 1
        done = self.t >= len(self.current_episode)

        if not done:
            next_state = self._get_state(self.current_episode.iloc[self.t])
        else:
            next_state = np.zeros_like(self._get_state(row))

        info = {"label": label}
        return next_state, reward, done, info

    def get_action_space(self):
        return self.action_space

    def get_observation_shape(self):
        # one row processed
        sample = self._get_state(self.current_episode.iloc[0])
        return sample.shape
