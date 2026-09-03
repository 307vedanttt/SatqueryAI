"""
SatQuery AI — Cross-Attention & Gated Fusion (Person D - Part 2)

Combines optical and SAR features via cross-attention (where optical features query SAR features)
with a learned sigmoid gating fallback mechanism.
"""

import logging
import torch
import torch.nn as nn

logger = logging.getLogger("satquery.models.fusion.fusion")


class CrossAttentionFusion(nn.Module):
    """
    Cross-attention and Gated Fusion module for combining Optical and SAR feature maps.
    Optical features query SAR features to resolve structural vs spectral ambiguities.
    """

    def __init__(self, embed_dim: int = 512, num_heads: int = 4):
        super().__init__()
        self.cross_attn = nn.MultiheadAttention(embed_dim=embed_dim, num_heads=num_heads, batch_first=True)
        # Learned gating parameter
        self.gate = nn.Sequential(
            nn.Conv2d(embed_dim * 2, embed_dim, kernel_size=1),
            nn.Sigmoid(),
        )

    def forward(self, f_opt: torch.Tensor, f_sar: torch.Tensor) -> torch.Tensor:
        """
        f_opt, f_sar: [B, C, H, W]
        Returns fused feature map [B, C, H, W].
        """
        b, c, h, w = f_opt.shape

        # Reshape to [B, H*W, C] for MultiheadAttention
        opt_flat = f_opt.view(b, c, h * w).permute(0, 2, 1)
        sar_flat = f_sar.view(b, c, h * w).permute(0, 2, 1)

        # Cross attention: Optical queries SAR
        attn_out, _ = self.cross_attn(query=opt_flat, key=sar_flat, value=sar_flat)
        attn_map = attn_out.permute(0, 2, 1).view(b, c, h, w)

        # Gated combination
        concat = torch.cat([f_opt, attn_map], dim=1)
        alpha = self.gate(concat)
        fused = alpha * f_opt + (1.0 - alpha) * attn_map

        return fused
