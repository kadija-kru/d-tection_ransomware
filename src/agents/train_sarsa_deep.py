import os
import numpy as np
import pandas as pd
import time
import sys

# Add the parent directory of src to the Python path
sys.path.append("/content/d-tection_ransomware")

from src.env import RansomwareEnv
from src.agents.sarsa import DeepSARSA # Corrected import

# ---- Config ----
DATA_CSV = "/content/d-tection_ransomware/data/UGRansome_Dataset_2024.csv"
PIPELINE_PATH = "/content/d-tection_ransomware/models/feature_pipeline.pkl"
MODEL_SAVE_PATH = "models/sarsa_deep.pth"
HISTORY_CSV = "models/sarsa_deep_history.csv"

feature_cols = ["Protocol", "Flag", "Family", "netflow_bucket",
                "Time", "Clusters", "BTC", "USD", "Netflow_Bytes",
                "bytes_per_second", "port_risk", "btc_flag", "usd_flag", "threat_score", "Port"]

# Hyperparams
n_episodes = 50
log_every = 20
max_steps_per_episode = None  # use full episode length
lr = 1e-3
gamma = 0.99
epsilon_start = 0.4
epsilon_end = 0.02
epsilon_decay = 0.999
hidden_dims = (256, 128)

# ---- Load data + ensure engineered features exist ----
df = pd.read_csv(DATA_CSV)

# -----------------------------
# Create binary target (duplicate from previous cell for self-contained)
# -----------------------------
df["risk"] = df["Prediction"].apply(lambda x: 0 if x == "A" else 1)

# -----------------------------
# Feature engineering (duplicate from previous cell for self-contained)
# -----------------------------
# Bytes per second
df["bytes_per_second"] = df["Netflow_Bytes"] / (df["Time"] + 1)

# Netflow bucket
df["netflow_bucket"] = pd.qcut(df["bytes_per_second"], q=3, labels=["low","medium","high"], duplicates='drop') # Added duplicates='drop'

# Port risk
risky_ports = [5061, 5062, 5063]  # example, adjust based on domain knowledge
df["port_risk"] = df["Port"].apply(lambda x: 1 if x in risky_ports else 0)

# BTC / USD flags
df["btc_flag"] = (df["BTC"] > 0).astype(int)
df["usd_flag"] = (df["USD"] > 0).astype(int)

# Threat score (example mapping — adjust based on dataset)
# Handle potential missing values in 'Threats' before mapping
df['Threats'] = df['Threats'].fillna('Unknown') # Impute missing threats
threat_mapping = {"Botnet":2, "Malware":2, "Normal":0, "Unknown": 0}  # adjust according to your Threats column
df["threat_score"] = df["Threats"].map(threat_mapping)

required_cols = ["netflow_bucket","bytes_per_second","port_risk","btc_flag","usd_flag","threat_score"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise RuntimeError(f"Missing engineered features: {missing}. Run src/preprocess.py first.")

# ---- Create environment ----
env = RansomwareEnv(
    df=df,
    feature_cols=feature_cols,
    pipeline_path=PIPELINE_PATH,
    group_by="SeedAddress",
    time_window_sec=60,
    drop_cols=["Prediction","IPaddress","SeedAddress","ExpAddress"],
    shuffle_episodes=True
)

# get example state to infer input_dim
s0 = env.reset()
input_dim = s0.shape[0]
env.render()
print("Observation dim:", input_dim)

# ---- Create agent ----
agent = DeepSARSA(
    input_dim=input_dim,
    n_actions=2,
    hidden_dims=hidden_dims,
    lr=lr,
    gamma=gamma,
    epsilon_start=epsilon_start,
    epsilon_end=epsilon_end,
    epsilon_decay=epsilon_decay
)

# ---- Training loop ----
history = []
start_time = time.time()
for ep in range(1, n_episodes+1):
    state = env.reset()
    done = False
    total_reward = 0.0

    # initial action (SARSA requires initial a)
    action = agent.select_action(state)
    losses = []
    tp = fp = tn = fn = 0
    steps = 0

    while not done:
        next_state, reward, done, info = env.step(action)
        total_reward += reward

        # classification mapping: action==1 => predict ransomware
        predicted = 1 if action == 1 else 0
        true_label = info["label"]
        if predicted == 1 and true_label == 1:
            tp += 1
        elif predicted == 1 and true_label == 0:
            fp += 1
        elif predicted == 0 and true_label == 0:
            tn += 1
        elif predicted == 0 and true_label == 1:
            fn += 1

        steps += 1

        # choose next action
        if not done:
            next_action = agent.select_action(next_state)
        else:
            next_action = None

        # update agent (SARSA)
        loss = agent.update(state, action, reward, next_state, next_action, done)
        if loss is not None:
            losses.append(loss)

        # move
        state = next_state
        action = next_action

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr_per_1000 = (fp / (steps if steps>0 else 1)) * 1000

    history.append({
        "episode": ep,
        "total_reward": total_reward,
        "steps": steps,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": precision, "recall": recall, "fpr_per_1000": fpr_per_1000,
        "epsilon": agent.epsilon,
        "loss_mean": np.mean(losses) if losses else 0.0,
        "loss_std": np.std(losses) if losses else 0.0
    })

    if ep % log_every == 0 or ep == 1:
        row = history[-1]
        print(f"[{ep}/{n_episodes}] reward={row['total_reward']:.2f} steps={row['steps']} "
              f"recall={row['recall']:.3f} prec={row['precision']:.3f} fpr/1k={row['fpr_per_1000']:.2f} eps={row['epsilon']:.3f} loss={row['loss_mean']:.4f}")

# ---- Save model and history ----
agent.save(MODEL_SAVE_PATH)
pd.DataFrame(history).to_csv(HISTORY_CSV, index=False)
print("Training done. Model saved to", MODEL_SAVE_PATH)
print("History saved to", HISTORY_CSV)
print("Elapsed time (s):", time.time() - start_time)
