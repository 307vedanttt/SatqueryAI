"""
Siamese encoder for bi-temporal change detection.
Shared-weight ResNet18 backbone — the SAME instance processes both images.
"""
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as T
from PIL import Image
import numpy as np

class SiameseEncoder(nn.Module):
    """
    SiameseEncoder model.
    The SAME backbone instance processes both images. This is the key architectural invariant of Siamese networks for change detection.
    """
    def __init__(self):
        super().__init__()
        # Load torchvision resnet18(pretrained=True).
        # Remove the final FC layer.
        resnet = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])
        
    def forward(self, img1_tensor: torch.Tensor, img2_tensor: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        features1 = self.backbone(img1_tensor)
        features2 = self.backbone(img2_tensor)
        return features1.squeeze(), features2.squeeze()
        
    @classmethod
    def get_preprocess(cls) -> T.Compose:
        return T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
    @staticmethod
    def preprocess_image(img_path: str) -> torch.Tensor:
        """Loads and preprocesses an image from a path."""
        img = Image.open(img_path).convert("RGB")
        preprocess = SiameseEncoder.get_preprocess()
        img_tensor = preprocess(img)
        return img_tensor.unsqueeze(0)
