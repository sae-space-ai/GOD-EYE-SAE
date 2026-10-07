"""
Decoupling Loss - DeCUR adversarial discriminator.

Ensures common representation is modality-agnostic.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class ModalityDiscriminator(nn.Module):
    """Adversarial discriminator for modality classification."""
    
    def __init__(self, input_dim: int = 256, hidden_dim: int = 128) -> None:
        super().__init__()
        self.discriminator = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
    
    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """
        Args:
            z: (B, D) latent representation
            
        Returns:
            (B, 1) modality prediction (0=LiDAR, 1=SAR)
        """
        return self.discriminator(z)


class DecouplingLoss(nn.Module):
    """
    DeCUR-style decoupling loss.
    
    Uses adversarial training to ensure z_common is modality-agnostic.
    """
    
    def __init__(self, lambda_adv: float = 0.1) -> None:
        """
        Args:
            lambda_adv: Weight for adversarial loss
        """
        super().__init__()
        self.lambda_adv = lambda_adv
        self.discriminator = ModalityDiscriminator()
        
        logger.info(f"Decoupling loss initialized: lambda_adv={lambda_adv}")
    
    def forward(
        self,
        z_common: torch.Tensor,
        z_unique_lidar: torch.Tensor,
        z_unique_sar: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Compute decoupling loss.
        
        Args:
            z_common: (B, D) shared representation
            z_unique_lidar: (B, D) LiDAR-unique representation
            z_unique_sar: (B, D) SAR-unique representation
            
        Returns:
            adv_loss: Adversarial loss (discriminator)
            gen_loss: Generator loss (encoder)
        """
        B = z_common.shape[0]
        
        # Discriminator should NOT be able to tell modality from z_common
        # Labels: 0 for LiDAR, 1 for SAR
        labels = torch.cat([
            torch.zeros(B // 2, 1, device=z_common.device),
            torch.ones(B - B // 2, 1, device=z_common.device)
        ])
        
        # Discriminator loss
        pred_common = self.discriminator(z_common)
        adv_loss = F.binary_cross_entropy(pred_common, labels)
        
        # Generator loss (adversarial - wants to fool discriminator)
        gen_loss = -adv_loss
        
        # Unique representations should be distinguishable
        pred_unique_lidar = self.discriminator(z_unique_lidar)
        pred_unique_sar = self.discriminator(z_unique_sar)
        
        unique_loss = (
            F.binary_cross_entropy(pred_unique_lidar, torch.zeros_like(pred_unique_lidar)) +
            F.binary_cross_entropy(pred_unique_sar, torch.ones_like(pred_unique_sar))
        ) / 2
        
        total_loss = self.lambda_adv * adv_loss + unique_loss
        
        return total_loss, gen_loss
