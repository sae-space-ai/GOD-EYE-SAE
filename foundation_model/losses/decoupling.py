"""
Decoupling Loss - DeCUR adversarial discriminator with Gradient Reversal Layer.

Ensures common representation is modality-agnostic through adversarial training.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class GradientReversalLayer(torch.autograd.Function):
    """
    Gradient Reversal Layer for adversarial training.
    
    Forward: identity
    Backward: reverses and scales gradients by -lambda
    """
    
    @staticmethod
    def forward(ctx, x, lambda_):
        ctx.lambda_ = lambda_
        return x.view_as(x)
    
    @staticmethod
    def backward(ctx, grad_output):
        return -ctx.lambda_ * grad_output, None


def gradient_reversal(x: torch.Tensor, lambda_: float = 1.0) -> torch.Tensor:
    """Apply gradient reversal to tensor."""
    return GradientReversalLayer.apply(x, lambda_)


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
    DeCUR-style decoupling loss with Gradient Reversal Layer.
    
    Uses adversarial training to ensure z_common is modality-agnostic.
    The encoder receives gradients that MINIMIZE the discriminator's ability
    to classify modality from z_common.
    """
    
    def __init__(self, lambda_adv: float = 0.1) -> None:
        """
        Args:
            lambda_adv: Weight for adversarial loss (GRL scaling factor)
        """
        super().__init__()
        self.lambda_adv = lambda_adv
        self.discriminator = ModalityDiscriminator()
        
        logger.info(f"Decoupling loss initialized: lambda_adv={lambda_adv}")
    
    def forward(
        self,
        z_common: torch.Tensor,
        z_unique_lidar: torch.Tensor,
        z_unique_sar: torch.Tensor,
        modality_labels: torch.Tensor | None = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Compute decoupling loss with gradient reversal.
        
        Args:
            z_common: (B, D) shared representation
            z_unique_lidar: (B, D) LiDAR-unique representation
            z_unique_sar: (B, D) SAR-unique representation
            modality_labels: (B,) optional labels (0=LiDAR, 1=SAR)
                           If None, assumes first half is LiDAR, second is SAR
            
        Returns:
            disc_loss: Discriminator loss (minimize classification error)
            adv_loss: Adversarial loss for encoder (maximize classification error via GRL)
        """
        B = z_common.shape[0]
        
        # Generate labels if not provided
        if modality_labels is None:
            # Assume first half is LiDAR (0), second half is SAR (1)
            modality_labels = torch.cat([
                torch.zeros(B // 2, dtype=torch.long, device=z_common.device),
                torch.ones(B - B // 2, dtype=torch.long, device=z_common.device)
            ])
        
        labels_float = modality_labels.float().unsqueeze(1)  # (B, 1)
        
        # === DISCRIMINATOR LOSS ===
        # Discriminator tries to classify modality from z_common
        # Apply gradient reversal so encoder receives inverted gradients
        z_common_reversed = gradient_reversal(z_common, self.lambda_adv)
        pred_common_reversed = self.discriminator(z_common_reversed)
        
        # Discriminator loss: minimize BCE (wants to classify correctly)
        # But gradients are reversed, so encoder maximizes BCE (wants to fool discriminator)
        adv_loss = F.binary_cross_entropy(pred_common_reversed, labels_float)
        
        # For logging: actual discriminator loss (without reversal)
        with torch.no_grad():
            pred_common_normal = self.discriminator(z_common)
            disc_loss = F.binary_cross_entropy(pred_common_normal, labels_float)
        
        # === UNIQUE REPRESENTATIONS LOSS ===
        # Unique representations should be distinguishable by modality
        pred_unique_lidar = self.discriminator(z_unique_lidar)
        pred_unique_sar = self.discriminator(z_unique_sar)
        
        # LiDAR unique should be classified as LiDAR (0)
        # SAR unique should be classified as SAR (1)
        unique_loss = (
            F.binary_cross_entropy(pred_unique_lidar, torch.zeros_like(pred_unique_lidar)) +
            F.binary_cross_entropy(pred_unique_sar, torch.ones_like(pred_unique_sar))
        ) / 2
        
        # Total loss for discriminator optimization
        total_disc_loss = adv_loss + unique_loss
        
        return total_disc_loss, adv_loss
