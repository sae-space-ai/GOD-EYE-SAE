"""
Reconstruction Losses - L1, angular, and Chamfer distance.

Combines multiple reconstruction objectives for both modalities.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


def chamfer_distance(
    pred: torch.Tensor,
    target: torch.Tensor,
    mask: torch.Tensor | None = None
) -> torch.Tensor:
    """
    Differentiable Chamfer distance between two point clouds.
    
    Args:
        pred: (B, N, 3) predicted points
        target: (B, M, 3) target points
        mask: (B, M) optional mask for target
        
    Returns:
        chamfer: scalar Chamfer distance
    """
    # Pairwise distances
    dist = torch.cdist(pred, target)  # (B, N, M)
    
    # Min distances
    min_dist_pred, _ = dist.min(dim=2)  # (B, N)
    min_dist_target, _ = dist.min(dim=1)  # (B, M)
    
    if mask is not None:
        min_dist_target = min_dist_target * mask.float()
        chamfer = min_dist_pred.mean() + (min_dist_target * mask.float()).sum() / (mask.sum() + 1e-8)
    else:
        chamfer = min_dist_pred.mean() + min_dist_target.mean()
    
    return chamfer


class ReconstructionLoss(nn.Module):
    """
    Combined reconstruction loss for LiDAR and SAR.
    
    LiDAR: L1 on coordinates + Chamfer distance
    SAR: L1 on amplitude + angular loss on phase
    """
    
    def __init__(
        self,
        lambda_lidar_l1: float = 1.0,
        lambda_lidar_chamfer: float = 1.0,
        lambda_sar_l1: float = 1.0,
        lambda_sar_phase: float = 0.5
    ) -> None:
        """
        Args:
            lambda_lidar_l1: Weight for LiDAR L1 loss
            lambda_lidar_chamfer: Weight for Chamfer distance
            lambda_sar_l1: Weight for SAR amplitude L1
            lambda_sar_phase: Weight for SAR phase angular loss
        """
        super().__init__()
        self.lambda_lidar_l1 = lambda_lidar_l1
        self.lambda_lidar_chamfer = lambda_lidar_chamfer
        self.lambda_sar_l1 = lambda_sar_l1
        self.lambda_sar_phase = lambda_sar_phase
        
        logger.info("Reconstruction loss initialized")
    
    def lidar_loss(
        self,
        pred_points: torch.Tensor,
        target_points: torch.Tensor,
        mask: torch.Tensor | None = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Compute LiDAR reconstruction loss.
        
        Args:
            pred_points: (B, N, 4) predicted (x, y, z, intensity)
            target_points: (B, N, 4) target points
            mask: (B, N) optional mask
            
        Returns:
            l1_loss: L1 coordinate loss
            chamfer_loss: Chamfer distance
        """
        # L1 on coordinates (x, y, z)
        l1_loss = F.l1_loss(
            pred_points[:, :, :3],
            target_points[:, :, :3],
            reduction='mean'
        )
        
        # Chamfer distance
        chamfer_loss = chamfer_distance(
            pred_points[:, :, :3],
            target_points[:, :, :3],
            mask
        )
        
        return l1_loss, chamfer_loss
    
    def sar_loss(
        self,
        pred_slc: torch.Tensor,
        target_slc: torch.Tensor
    ) -> dict:
        """
        Compute SAR reconstruction loss.
        
        Supports both 2-channel (single-pol amp/phase) and 4-channel
        (dual-pol VV/VH real/imag) representations.
        
        Args:
            pred_slc: (B, C, H, W) predicted SLC (C=2 or C=4)
            target_slc: (B, C, H, W) target SLC (C=2 or C=4)
            
        Returns:
            Dictionary with amplitude and phase losses per polarization
        """
        from ..utils.sar_polarization import dual_pol_reconstruction_loss, circular_phase_loss
        
        if pred_slc.shape[1] == 4:
            # Dual-pol real/imag representation
            return dual_pol_reconstruction_loss(pred_slc, target_slc)
        elif pred_slc.shape[1] == 2:
            # Single-pol amplitude/phase representation (legacy)
            amp_loss = F.l1_loss(pred_slc[:, 0], target_slc[:, 0])
            phase_loss = circular_phase_loss(pred_slc[:, 1], target_slc[:, 1])
            return {
                'vv_amplitude': amp_loss,
                'vv_phase': phase_loss,
                'vh_amplitude': torch.tensor(0.0, device=pred_slc.device),
                'vh_phase': torch.tensor(0.0, device=pred_slc.device),
                'total': amp_loss + phase_loss,
            }
        else:
            raise ValueError(f"Expected 2 or 4 SAR channels, got {pred_slc.shape[1]}")
    
    def forward(
        self,
        pred_lidar: torch.Tensor,
        target_lidar: torch.Tensor,
        pred_sar: torch.Tensor,
        target_sar: torch.Tensor,
        lidar_mask: torch.Tensor | None = None
    ) -> dict[str, torch.Tensor]:
        """
        Compute full reconstruction loss.
        
        Returns:
            Dictionary with individual losses and total
        """
        lidar_l1, lidar_chamfer = self.lidar_loss(pred_lidar, target_lidar, lidar_mask)
        sar_losses = self.sar_loss(pred_sar, target_sar)
        
        # Aggregate amplitude and phase losses across polarizations
        sar_amp = sar_losses['vv_amplitude'] + sar_losses['vh_amplitude']
        sar_phase = sar_losses['vv_phase'] + sar_losses['vh_phase']
        
        total = (
            self.lambda_lidar_l1 * lidar_l1 +
            self.lambda_lidar_chamfer * lidar_chamfer +
            self.lambda_sar_l1 * sar_amp +
            self.lambda_sar_phase * sar_phase
        )
        
        return {
            'lidar_l1': lidar_l1,
            'lidar_chamfer': lidar_chamfer,
            'sar_amplitude': sar_amp,
            'sar_phase': sar_phase,
            **{f'sar_{k}': v for k, v in sar_losses.items()},
            'total': total
        }
