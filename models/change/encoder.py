"""
SatQuery AI — Siamese Encoder (Person C)

Uses a shared-weight PyTorch backbone (ResNet18) to extract feature maps
for both images in a bi-temporal pair.
"""

import torch
import torch.nn as nn
from PIL import Image
import torchvision.transforms as T


class SiameseEncoder(nn.Module):
    """Shared-weight Siamese Feature Extractor."""

    def __init__(self):
        super().__init__()
        import torchvision.models as models
        # Load pretrained ResNet18 backbone
        resnet = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        # Remove final FC and avgpool layer -> Output shape: [B, 512, H/32, W/32]
        self.backbone = nn.Sequential(*list(resnet.children())[:-2])
        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def preprocess_image(self, pil_img: Image.Image) -> torch.Tensor:
        """Preprocess PIL image into 4D tensor [1, 3, 224, 224]."""
        return self.transform(pil_img.convert("RGB")).unsqueeze(0)

    def forward(self, img1_tensor: torch.Tensor, img2_tensor: torch.Tensor):
        """
        Forward pass using IDENTICAL shared backbone weights.
        Returns (features1, features2).
        """
        f1 = self.backbone(img1_tensor)
        f2 = self.backbone(img2_tensor)
        return f1, f2
