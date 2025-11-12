import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

class DeepSARSA(nn.Module):
    def __init__(self, input_dim, n_actions, hidden_dims=(256,128), lr=1e-3, gamma=0.99):
        super().__init__()
        self.gamma = gamma
        self.n_actions = n_actions
        self.epsilon = 0.2  # ε-greedy

        # Neural network
        layers = []
        last_dim = input_dim
        for h in hidden_dims:
            layers.append(nn.Linear(last_dim, h))
            layers.append(nn.ReLU())
            last_dim = h
        layers.append(nn.Linear(last_dim, n_actions))
        self.model = nn.Sequential(*layers)

        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self.loss_fn = nn.MSELoss()

    def forward(self, x):
        return self.model(torch.FloatTensor(x))

    def select_action(self, state):
        if np.random.rand() < self.epsilon:
            return np.random.choice(self.n_actions)
        q_values = self.forward(state).detach().numpy()
        return int(np.argmax(q_values))

    def update(self, s, a, r, s_next, a_next):
        q_sa = self.forward(s)[a]
        q_next = self.forward(s_next)[a_next]
        target = r + self.gamma * q_next
        loss = self.loss_fn(q_sa, target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        return loss.item()

    def save(self, path):
        torch.save(self.state_dict(), path)

    def load(self, path):
        self.load_state_dict(torch.load(path))
        self.eval()
