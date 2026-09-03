"""
SatQuery AI — Independent Optical & SAR Feature Encoders (Person D - Part 2)

Maintains SEPARATE encoder weights for optical (reflectance) vs SAR (backscatter intensity).
Optical and SAR imagery measure fundamentally different physical properties, so
they use independent weights to prevent domain interference.
"""

import logging
import torch
import torch.nn as nn
import torchvision.transforms as T
from PIL import Image

logger = logging.getLogger("satquery.models.fusion.encoders")


class OpticalEncoder(nn.Module):
    """Encoder for optical imagery (RGB / multispectral reflectance)."""

    def __init__(self):
        super().__init__()
        import torchvision.models as models
        resnet = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        # Remove average pooling and final FC layer -> Output: [B, 512, H/32, W/32]
        self.backbone = nn.Sequential(*list(resnet.children())[:-2])
        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def preprocess(self, pil_img: Image.Image) -> torch.Tensor:
        """Convert PIL Image to preprocessed 4D tensor [1, 3, 224, 224]."""
        return self.transform(pil_img.convert("RGB")).unsqueeze(0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


class SAREncoder(nn.Module):
    """
    Encoder for SAR radar imagery (backscatter intensity).
    Maintains INDEPENDENT weights from OpticalEncoder.
    """

    def __init__(self):
        super().__init__()
        import torchvision.models as models
        # Independent ResNet18 instance with separate weights
        resnet = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        self.backbone = nn.Sequential(*list(resnet.children())[:-2])
        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ])

    def preprocess(self, pil_img: Image.Image) -> torch.Tensor:
        """Convert PIL Image to preprocessed 4D tensor [1, 3, 224, 224]."""
        # Despeckling preprocessing filter could be inserted here
        return self.transform(pil_img.convert("RGB")).unsqueeze(0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)
