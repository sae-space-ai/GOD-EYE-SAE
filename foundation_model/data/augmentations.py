"""
Modality-specific augmentations for contrastive learning.

Creates two augmented views of the same tile pair.
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class LiDARAugmentation:
    """LiDAR-specific augmentations."""
    
    def __init__(
        self,
        rotation_range: float = 30.0,
        point_dropout: float = 0.10,
        noise_sigma: float = 0.01
    ) -> None:
        """
        Args:
            rotation_range: Max rotation in degrees
            point_dropout: Fraction of points to drop
            noise_sigma: Gaussian noise std on coordinates
        """
        self.rotation_range = rotation_range
        self.point_dropout = point_dropout
        self.noise_sigma = noise_sigma
    
    def __call__(
        self,
        xyz: torch.Tensor,
        features: torch.Tensor,
        mask: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Apply augmentations to LiDAR.
        
        Args:
            xyz: (N, 3) point coordinates
            features: (N, 4) point features
            mask: (N,) valid point mask
            
        Returns:
            Augmented xyz, features, mask
        """
        # Random rotation around Z axis
        angle = np.random.uniform(-self.rotation_range, self.rotation_range)
        angle_rad = np.deg2rad(angle)
        
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        
        rotation_matrix = torch.tensor([
            [cos_a, -sin_a, 0],
            [sin_a, cos_a, 0],
            [0, 0, 1]
        ], dtype=xyz.dtype, device=xyz.device)
        
        xyz = xyz @ rotation_matrix.T
        
        # Random point dropout
        if self.point_dropout > 0:
            dropout_mask = torch.rand(xyz.shape[0], device=xyz.device) > self.point_dropout
            mask = mask & dropout_mask
        
        # Gaussian noise
        if self.noise_sigma > 0:
            noise = torch.randn_like(xyz) * self.noise_sigma
            xyz = xyz + noise * mask.unsqueeze(-1).float()
        
        return xyz, features, mask


class SARAUGmentation:
    """SAR-specific augmentations."""
    
    def __init__(self, noise_sigma: float = 0.05) -> None:
        """
        Args:
            noise_sigma: Gaussian noise std on amplitude
        """
        self.noise_sigma = noise_sigma
    
    def __call__(self, sar_slc: torch.Tensor) -> torch.Tensor:
        """
        Apply augmentations to SAR.
        
        Args:
            sar_slc: (2, H, W) SAR image (amplitude, phase)
            
        Returns:
            Augmented SAR
        """
        # Gaussian noise on amplitude
        if self.noise_sigma > 0:
            noise = torch.randn_like(sar_slc[0:1]) * self.noise_sigma
            sar_slc = sar_slc.clone()
            sar_slc[0] = sar_slc[0] + noise
        
        return sar_slc


class ContrastiveAugmentation:
    """Creates two augmented views for contrastive learning."""
    
    def __init__(
        self,
        lidar_aug: LiDARAugmentation,
        sar_aug: SARAUGmentation
    ) -> None:
        self.lidar_aug = lidar_aug
        self.sar_aug = sar_aug
    
    def __call__(
        self,
        lidar_xyz: torch.Tensor,
        lidar_features: torch.Tensor,
        lidar_mask: torch.Tensor,
        sar_slc: torch.Tensor
    ) -> Tuple[dict, dict]:
        """
        Create two augmented views.
        
        Returns:
            view1, view2: Each is a dict with augmented data
        """
        # View 1
        xyz1, feat1, mask1 = self.lidar_aug(lidar_xyz, lidar_features, lidar_mask)
        sar1 = self.sar_aug(sar_slc)
        
        view1 = {
            'lidar_xyz': xyz1,
            'lidar_features': feat1,
            'lidar_mask': mask1,
            'sar_slc': sar1
        }
        
        # View 2 (different random augmentations)
        xyz2, feat2, mask2 = self.lidar_aug(lidar_xyz, lidar_features, lidar_mask)
        sar2 = self.sar_aug(sar_slc)
        
        view2 = {
            'lidar_xyz': xyz2,
            'lidar_features': feat2,
            'lidar_mask': mask2,
            'sar_slc': sar2
        }
        
        return view1, view2
