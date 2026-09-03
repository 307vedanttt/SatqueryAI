"""Fusion mechanisms."""

import torch
import torch.nn as nn

class CrossAttentionFusion(nn.Module):
    """
    True cross-attention fusion mechanism.
    Optical features act as the Query (Q), and SAR features act as the Key (K) and Value (V).
    This allows the optical modality to query relevant structural features from the SAR modality.
    """
    def __init__(self, embed_dim: int = 512, num_heads: int = 8):
        super().__init__()
        # Use PyTorch's built-in MultiheadAttention
        self.cross_attn = nn.MultiheadAttention(embed_dim=embed_dim, num_heads=num_heads, batch_first=True)
        self.norm = nn.LayerNorm(embed_dim)
        
    def forward(self, optical_features: torch.Tensor, sar_features: torch.Tensor) -> torch.Tensor:
        """
        Fuse features from optical and SAR encoders.
        Both inputs should have shape (batch_size, 512).
        Returns fused features of shape (batch_size, 512).
        """
        # MultiheadAttention expects sequence dimension. Add a dummy sequence dimension.
        # Shape: (batch_size, 1, 512)
        opt_seq = optical_features.unsqueeze(1)
        sar_seq = sar_features.unsqueeze(1)
        
        # Cross-attention: Q=Optical, K=SAR, V=SAR
        attn_output, _ = self.cross_attn(query=opt_seq, key=sar_seq, value=sar_seq)
        
        # Residual connection and layer normalization
        fused_seq = self.norm(opt_seq + attn_output)
        
        # Remove dummy sequence dimension
        return fused_seq.squeeze(1)
