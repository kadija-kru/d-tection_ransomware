import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

class QNetwork(nn.Module):
    def __init__(self, input_dim, hidden_dims=(256,128), n_actions=2):
        super().__init__()
        layers = []
        prev = input_dim
        for h in hidden_dims:
            layers.append(nn.Linear(prev, h))
            layers.append(nn.ReLU())
            prev = h
        layers.append(nn.Linear(prev, n_actions))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


class DeepSARSA:
    def __init__(
        self,
        input_dim,
        n_actions=2,
        hidden_dims=(256,128),
        lr=1e-3,
        gamma=0.99,
        epsilon_start=0.3,
        epsilon_end=0.01,
        epsilon_decay=0.9995,
        device=None,
        weight_decay=0.0
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.n_actions = n_actions
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay

        self.model = QNetwork(input_dim, hidden_dims, n_actions).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr, weight_decay=weight_decay)
        self.loss_fn = nn.MSELoss()

    def select_action(self, state):
        """
        epsilon-greedy. state: numpy array (1D)
        returns action int
        """
        if np.random.rand() < self.epsilon:
            return int(np.random.randint(0, self.n_actions))
        self.model.eval()
        with torch.no_grad():
            s = torch.tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
            q = self.model(s)  # shape [1, n_actions]
            a = int(torch.argmax(q, dim=1).item())
        return a

    def update(self, s_vec, action, reward, s_next_vec, next_action, done):
        """
        Perform one SARSA update step (online). All inputs are raw numpy arrays / scalars.
        s_vec: current state vector (1D)
        action: int
        reward: float
        s_next_vec: next state vector or None if terminal
        next_action: int or None if terminal
        done: bool
        """
        self.model.train()
        s = torch.tensor(s_vec, dtype=torch.float32, device=self.device).unsqueeze(0)  # [1, D]
        q_vals = self.model(s)  # [1, A]
        q_sa = q_vals[0, action]

        if done or s_next_vec is None:
            target_val = torch.tensor(reward, dtype=torch.float32, device=self.device)
        else:
            s_next = torch.tensor(s_next_vec, dtype=torch.float32, device=self.device).unsqueeze(0)
            with torch.no_grad():
                q_next = self.model(s_next)  # [1, A]
                q_snext_anext = q_next[0, next_action]
            target_val = torch.tensor(reward, dtype=torch.float32, device=self.device) + self.gamma * q_snext_anext

        loss = self.loss_fn(q_sa, target_val)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # decay epsilon
        if self.epsilon > self.epsilon_end:
            self.epsilon *= self.epsilon_decay

        return loss.item()

    def save(self, path="models/sarsa_net.pth"):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        torch.save({
            "model_state": self.model.state_dict(),
            "optimizer_state": self.optimizer.state_dict(),
            "epsilon": self.epsilon,
            "gamma": self.gamma
        }, path)

    def load(self, path="models/sarsa_net.pth"):
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state"])
        self.epsilon = checkpoint.get("epsilon", self.epsilon)
        self.gamma = checkpoint.get("gamma", self.gamma)
