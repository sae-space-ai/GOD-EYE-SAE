"""
Linear Probe - Downstream evaluation with frozen backbone.

Attaches a single linear layer to the frozen encoder for evaluation.
"""

import torch
import torch.nn as nn
from typing import Dict
import logging

from .autoencoder import MultimodalAutoencoder

logger = logging.getLogger(__name__)


class LinearProbe(nn.Module):
    """
    Linear probe for downstream evaluation.
    
    Freezes the backbone and trains only a linear classification head.
    """
    
    def __init__(
        self,
        backbone: MultimodalAutoencoder,
        num_classes: int = 5,
        latent_dim: int = 256,
        use_common: bool = True
    ) -> None:
        """
        Args:
            backbone: Pretrained multimodal autoencoder
            num_classes: Number of output classes
            latent_dim: Latent dimension
            use_common: Use common representation (vs fused)
        """
        super().__init__()
        
        # Freeze backbone
        self.backbone = backbone
        for param in self.backbone.parameters():
            param.requires_grad = False
        
        self.use_common = use_common
        self.latent_dim = latent_dim
        
        # Linear classification head
        self.classifier = nn.Sequential(
            nn.Linear(latent_dim, latent_dim // 2),
            nn.ReLU(inplace=True),
            nn.Dropout(0.1),
            nn.Linear(latent_dim // 2, num_classes)
        )
        
        logger.info(
            f"Linear probe initialized: num_classes={num_classes}, "
            f"use_common={use_common}"
        )
    
    def forward(
        self,
        lidar_xyz: torch.Tensor,
        lidar_features: torch.Tensor | None,
        sar_image: torch.Tensor,
        lidar_mask: torch.Tensor | None = None
    ) -> torch.Tensor:
        """
        Forward pass with frozen backbone.
        
        Args:
            lidar_xyz: (B, N, 3) LiDAR points
            lidar_features: (B, N, C) LiDAR features
            sar_image: (B, 2, H, W) SAR SLC
            lidar_mask: (B, N) valid point mask
            
        Returns:
            logits: (B, num_classes) classification logits
        """
        with torch.no_grad():
            encoded = self.backbone.encode(
                lidar_xyz, lidar_features, sar_image, lidar_mask
            )
        
        # Select representation
        if self.use_common:
            z = encoded['z_common']
        else:
            z = (encoded['z_lidar'] + encoded['z_sar']) / 2
        
        # Classification
        logits = self.classifier(z)
        
        return logits
    
    def get_trainable_parameters(self) -> list[nn.Parameter]:
        """Return only trainable parameters (classifier head)."""
        return list(self.classifier.parameters())
