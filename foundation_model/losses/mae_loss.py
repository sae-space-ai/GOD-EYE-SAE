"""
Cross-modal Masked Autoencoding (MAE) Loss.

Randomly masks portions of one modality and reconstructs from the other.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class CrossModalMAELoss(nn.Module):
    """
    Cross-modal masked autoencoding loss.
    
    Masks 75% of LiDAR points and 60% of SAR patches,
    reconstructs from the unmasked portion of the OTHER modality.
    """
    
    def __init__(
        self,
        lidar_mask_ratio: float = 0.75,
        sar_mask_ratio: float = 0.60
    ) -> None:
        """
        Args:
            lidar_mask_ratio: Fraction of LiDAR points to mask
            sar_mask_ratio: Fraction of SAR patches to mask
        """
        super().__init__()
        self.lidar_mask_ratio = lidar_mask_ratio
        self.sar_mask_ratio = sar_mask_ratio
        
        logger.info(
            f"MAE loss initialized: lidar_mask={lidar_mask_ratio}, "
            f"sar_mask={sar_mask_ratio}"
        )
    
    def generate_masks(
        self,
        lidar_shape: Tuple[int, int],
        sar_shape: Tuple[int, int, int, int]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Generate random masks for both modalities.
        
        Args:
            lidar_shape: (B, N) LiDAR shape
            sar_shape: (B, C, H, W) SAR shape
            
        Returns:
            lidar_mask: (B, N) boolean mask (True = keep)
            sar_mask: (B, H, W) boolean mask (True = keep)
        """
        B, N = lidar_shape
        B_s, _, H, W = sar_shape
        
        # LiDAR mask
        lidar_keep_ratio = 1.0 - self.lidar_mask_ratio
        lidar_mask = torch.rand(B, N, device='cuda') < lidar_keep_ratio
        
        # SAR mask (patch-level)
        sar_keep_ratio = 1.0 - self.sar_mask_ratio
        sar_mask = torch.rand(B, H, W, device='cuda') < sar_keep_ratio
        
        return lidar_mask, sar_mask
    
    def forward(
        self,
        lidar_pred: torch.Tensor,
        lidar_target: torch.Tensor,
        lidar_mask: torch.Tensor,
        sar_pred: torch.Tensor,
        sar_target: torch.Tensor,
        sar_mask: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Compute MAE reconstruction loss on masked regions.
        
        Args:
            lidar_pred: (B, N, 4) predicted LiDAR points
            lidar_target: (B, N, 4) target LiDAR points
            lidar_mask: (B, N) mask (True = unmasked, should NOT contribute to loss)
            sar_pred: (B, 2, H, W) predicted SAR
            sar_target: (B, 2, H, W) target SAR
            sar_mask: (B, H, W) mask (True = unmasked)
            
        Returns:
            lidar_loss: LiDAR MAE loss
            sar_loss: SAR MAE loss
        """
        # LiDAR: compute loss on MASKED points (where mask is False)
        lidar_masked = ~lidar_mask  # Invert: True = masked
        lidar_diff = F.l1_loss(lidar_pred, lidar_target, reduction='none')
        lidar_diff = lidar_diff.mean(dim=-1)  # (B, N)
        lidar_loss = (lidar_diff * lidar_masked.float()).sum() / (lidar_masked.sum() + 1e-8)
        
        # SAR: compute loss on MASKED patches
        sar_masked = ~sar_mask  # Invert
        sar_diff = F.l1_loss(sar_pred, sar_target, reduction='none')
        sar_diff = sar_diff.mean(dim=1)  # (B, H, W)
        sar_loss = (sar_diff * sar_masked.float()).sum() / (sar_masked.sum() + 1e-8)
        
        return lidar_loss, sar_loss
