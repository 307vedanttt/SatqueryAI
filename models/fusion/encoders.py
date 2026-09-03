"""Modality encoders for optical and SAR images."""

import torch
import torch.nn as nn
import torchvision.models as tv_models
from torchvision import transforms
from PIL import Image

class ModalityEncoder(nn.Module):
    """
    Encoder for a specific imaging modality based on ResNet18.
    """
    def __init__(self):
        super().__init__()
        resnet = tv_models.resnet18(pretrained=False)
        # Remove final FC
        self.features = nn.Sequential(*list(resnet.children())[:-1])
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        Returns: feature vector of shape (batch, 512)
        """
        x = self.features(x)
        return x.view(x.size(0), -1)

# optical_encoder and sar_encoder are deliberately separate instances with independent weights.
# Optical measures spectral reflectance; SAR measures backscatter — different physical properties
# require separately-learned encoders.
optical_encoder = ModalityEncoder()
sar_encoder = ModalityEncoder()

def preprocess_image(path: str) -> torch.Tensor:
    """
    Preprocess image for the encoder.
    TODO: Add SAR despeckling preprocessing (e.g., median filter via scipy/OpenCV) for SAR images before encoding.
    Currently skipped to prioritize end-to-end functionality.
    """
    img = Image.open(path).convert("RGB")
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    tensor = transform(img).unsqueeze(0)
    return tensor
