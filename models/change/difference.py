"""
SatQuery AI — Change Enhancement & Magnitude (Person C)

Computes explicit feature difference |F1 - F2| and passes it through a learnable block,
and provides a scalar change magnitude metric.
"""

import torch
import torch.nn as nn


class ChangeEnhancement(nn.Module):
    """Processes absolute feature difference to emphasize change signals."""

    def __init__(self, in_channels: int = 512):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
        )

    def forward(self, f1: torch.Tensor, f2: torch.Tensor) -> torch.Tensor:
        abs_diff = torch.abs(f1 - f2)
        return self.block(abs_diff)


def compute_change_magnitude(f1: torch.Tensor, f2: torch.Tensor) -> float:
    """
    Return a scalar change magnitude in range [0.0, 1.0].
    Computes mean absolute difference across feature maps normalized by feature norm.
    """
    with torch.no_grad():
        abs_diff = torch.abs(f1 - f2)
        mean_diff = float(torch.mean(abs_diff).item())
        norm = float((torch.mean(torch.abs(f1)) + torch.mean(torch.abs(f2))).item() / 2.0 + 1e-6)
        normalized_val = min(1.0, mean_diff / (norm * 1.5))
        return round(normalized_val, 4)
