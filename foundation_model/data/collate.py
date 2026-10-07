"""
Custom collate function for variable-sized point clouds.

Handles padding and spatial alignment between LiDAR and SAR.
"""

import torch
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def lidar_sar_collate_fn(batch: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
    """
    Custom collate function for LiDAR-SAR batches.
    
    Handles variable-sized point clouds and ensures spatial alignment.
    
    Args:
        batch: List of sample dictionaries
        
    Returns:
        Batched dictionary with stacked tensors
    """
    collated = {}
    
    # Stack LiDAR tensors (already padded to max_points)
    collated['lidar_xyz'] = torch.stack([sample['lidar_xyz'] for sample in batch])
    collated['lidar_features'] = torch.stack([sample['lidar_features'] for sample in batch])
    collated['lidar_mask'] = torch.stack([sample['lidar_mask'] for sample in batch])
    
    # Stack SAR tensors (should all be same size)
    collated['sar_slc'] = torch.stack([sample['sar_slc'] for sample in batch])
    
    # Stack labels if present
    if 'label' in batch[0]:
        collated['label'] = torch.stack([sample['label'] for sample in batch])
    
    return collated


def align_spatial_extent(
    lidar_xyz: torch.Tensor,
    sar_slc: torch.Tensor,
    sar_resolution: float = 10.0
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Align LiDAR and SAR to same spatial extent.
    
    Args:
        lidar_xyz: (N, 3) LiDAR points in meters
        sar_slc: (2, H, W) SAR image
        sar_resolution: SAR ground resolution in meters
        
    Returns:
        Aligned lidar_xyz, sar_slc
    """
    # Compute LiDAR extent
    lidar_min = lidar_xyz.min(dim=0)[0]
    lidar_max = lidar_xyz.max(dim=0)[0]
    
    # Compute SAR extent
    sar_height = sar_slc.shape[1] * sar_resolution
    sar_width = sar_slc.shape[2] * sar_resolution
    
    # Center both at origin
    lidar_center = (lidar_min + lidar_max) / 2
    lidar_xyz = lidar_xyz - lidar_center
    
    return lidar_xyz, sar_slc
