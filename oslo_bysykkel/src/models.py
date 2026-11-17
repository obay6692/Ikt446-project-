"""Fair Random Forest / PyTorch MLP comparison on identical calendar features."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import random

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


class DemandMLP(nn.Module):
    def __init__(self, input_size: int, hidden_sizes: list[int]):
        super().__init__()
        layers: list[nn.Module] = []
        in_dim = input_size
        for hidden in hidden_sizes:
            layers += [nn.Linear(in_dim, hidden), nn.ReLU()]
            in_dim = hidden
        layers.append(nn.Linear(in_dim, 1))
        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x).squeeze(-1)


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)


def fit_rf(X_train, y_train, parameters: dict, seed: int):
    model = RandomForestRegressor(random_state=seed, n_jobs=-1, **parameters)
    model.fit(X_train, y_train)
    return model


def predict_rf(model, X):
    return np.maximum(0, model.predict(X))


def fit_mlp(X_train, y_train, X_val, y_val, parameters: dict, seed: int):
    """Train with early stopping on validation. Scaling fits training ONLY."""
    seed_everything(seed)
    sx = StandardScaler()
    sy = StandardScaler()
    X_tr = sx.fit_transform(np.asarray(X_train, dtype=np.float32)).astype("float32")
    X_va = sx.transform(np.asarray(X_val, dtype=np.float32)).astype("float32")
    y_tr = sy.fit_transform(np.asarray(y_train, dtype=np.float32).reshape(-1, 1)).ravel()
    y_va = sy.transform(np.asarray(y_val, dtype=np.float32).reshape(-1, 1)).ravel()
    dataset = TensorDataset(torch.from_numpy(X_tr), torch.from_numpy(y_tr.astype("float32")))
    loader = DataLoader(dataset, batch_size=parameters["batch_size"], shuffle=True,
                        generator=torch.Generator().manual_seed(seed))
    model = DemandMLP(X_tr.shape[1], parameters["hidden_sizes"])
    optimizer = torch.optim.Adam(model.parameters(), lr=parameters["learning_rate"],
                                 weight_decay=parameters["weight_decay"])
    criterion = nn.MSELoss()
    x_val_t = torch.from_numpy(X_va)
    y_val_t = torch.from_numpy(y_va.astype("float32"))
    best = np.inf
    best_epoch = 0
    best_state = None
    history = []
    for epoch in range(1, parameters["max_epochs"] + 1):
        model.train()
        total_loss = 0.0
        total_samples = 0
        for xb, yb in loader:
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(xb)
            total_samples += len(xb)
        model.eval()
        with torch.no_grad():
            validation_loss = criterion(model(x_val_t), y_val_t).item()
        training_loss = total_loss / total_samples
        history.append({"epoch": epoch, "train_loss": training_loss, "val_loss": validation_loss})
        if validation_loss < best - 1e-6:
            best = validation_loss
            best_epoch = epoch
            best_state = deepcopy(model.state_dict())
        if epoch - best_epoch >= parameters["patience"]:
            break
    model.load_state_dict(best_state)
    return {"model": model, "scaler_x": sx, "scaler_y": sy,
            "history": history, "best_epoch": best_epoch,
            "hidden_sizes": parameters["hidden_sizes"]}


def predict_mlp(artifact: dict, X):
    model = artifact["model"]
    model.eval()
    transformed = artifact["scaler_x"].transform(np.asarray(X, dtype=np.float32)).astype("float32")
    with torch.no_grad():
        pred = model(torch.from_numpy(transformed)).cpu().numpy().reshape(-1, 1)
    unscaled = artifact["scaler_y"].inverse_transform(pred).ravel()
    return np.maximum(0, unscaled)


def save_mlp(artifact: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": artifact["model"].state_dict(),
                "hidden_sizes": artifact["hidden_sizes"],
                "input_size": artifact["model"].network[0].in_features,
                "scaler_x_mean": artifact["scaler_x"].mean_.tolist(),
                "scaler_x_scale": artifact["scaler_x"].scale_.tolist(),
                "scaler_y_mean": artifact["scaler_y"].mean_.tolist(),
                "scaler_y_scale": artifact["scaler_y"].scale_.tolist(),
                "best_epoch": artifact["best_epoch"]}, path)


def load_mlp(path: Path):
    payload = torch.load(path, map_location="cpu", weights_only=True)
    model = DemandMLP(payload["input_size"], payload["hidden_sizes"])
    model.load_state_dict(payload["state_dict"])
    return payload, model


def save_rf(model, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
