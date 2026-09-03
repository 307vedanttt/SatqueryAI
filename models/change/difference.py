"""
Difference computation for change detection.
"""
import torch
import torch.nn as nn

class ChangeEnhancement(nn.Module):
    """Enhances change features between two feature vectors."""
    def __init__(self):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
        
    def forward(self, f1: torch.Tensor, f2: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        diff = torch.abs(f1 - f2)
        
        # pass diff through MLP
        x = diff
        for layer in list(self.mlp.children())[:-2]: # get to the 128 layer output
            x = layer(x)
        
        enhanced_features = x
        
        change_score = self.mlp(diff)
        
        return change_score, enhanced_features

def compute_change_magnitude(f1: torch.Tensor, f2: torch.Tensor) -> float:
    """
    Computes the change magnitude.
    This is a simple proxy for how much the features differ, used as a confidence signal before a fully trained classification head is available.
    """
    diff_mean = torch.mean(torch.abs(f1 - f2))
    sum_mean = torch.mean(torch.abs(f1)) + torch.mean(torch.abs(f2)) + 1e-8
    magnitude = float((diff_mean / sum_mean).item())
    return magnitude
