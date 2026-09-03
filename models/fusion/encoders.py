"""
SatQuery AI — Independent Optical & SAR Encoders (Person D - Part 2)

Maintains SEPARATE encoder weights for optical (reflectance) vs SAR (backscatter).
"""

import torch
import torch.nn as nn
import torchvision.transforms as T
from PIL import Image


class OpticalEncoder(nn.Module):
    """Encoder for optical imagery (3-band RGB / multispectral reflectance)."""

    def __init__(self):
        super().__init__()
        import torchvision.models as models
        resnet = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        self.backbone = nn.Sequential(*list(resnet.children())[:-2])
        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def preprocess(self, pil_img: Image.Image) -> torch.Tensor:
        return self.transform(pil_img.convert("RGB")).unsqueeze(0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


class SAREncoder(nn.Module):
    """
    Encoder for SAR imagery (backscatter intensity).
    Maintains independent weights from OpticalEncoder.
    """

    def __init__(self):
        super().__init__()
        import torchvision.models as models
        # Independent ResNet18 instance
        resnet = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        self.backbone = nn.Sequential(*list(resnet.children())[:-2])
        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ])

    def preprocess(self, pil_img: Image.Image) -> torch.Tensor:
        # Simple median despeckling heuristic could be applied here
        return self.transform(pil_img.convert("RGB")).unsqueeze(0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)
