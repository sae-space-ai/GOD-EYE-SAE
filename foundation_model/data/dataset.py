"""
LiDAR-SAR Tile Pair Dataset.

Loads co-registered LiDAR point clouds and SAR SLC images from HDF5.
"""

import torch
from torch.utils.data import Dataset
import h5py
import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class LiDARSARDataset(Dataset):
    """
    Dataset for co-registered LiDAR-SAR tile pairs.
    
    Expected HDF5 format:
        /lidar_points: (N, 4) - x, y, z, intensity
        /sar_slc: (2, H, W) - amplitude, phase
        /labels: (optional) class label
    """
    
    def __init__(
        self,
        data_path: str,
        max_points: int = 8192,
        transform: Optional[callable] = None
    ) -> None:
        """
        Args:
            data_path: Path to HDF5 file
            max_points: Maximum number of LiDAR points
            transform: Optional augmentation transform
        """
        super().__init__()
        self.data_path = data_path
        self.max_points = max_points
        self.transform = transform
        
        # Load dataset metadata
        with h5py.File(data_path, 'r') as f:
            self.num_samples = len(f['lidar_points'])
            logger.info(f"Loaded dataset: {self.num_samples} samples from {data_path}")
    
    def __len__(self) -> int:
        return self.num_samples
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Load a single LiDAR-SAR pair.
        
        Returns:
            Dictionary with:
                - lidar_xyz: (N, 3) point coordinates
                - lidar_features: (N, 4) point features (xyz + intensity)
                - lidar_mask: (N,) valid point mask
                - sar_slc: (2, H, W) SAR image
                - label: (optional) class label
        """
        with h5py.File(self.data_path, 'r') as f:
            # Load LiDAR
            lidar_points = f['lidar_points'][idx]  # (N, 4)
            
            # Load SAR
            sar_slc = f['sar_slc'][idx]  # (2, H, W)
            
            # Load label if available
            label = f['labels'][idx] if 'labels' in f else -1
        
        # Convert to tensors
        lidar_points = torch.from_numpy(lidar_points).float()
        sar_slc = torch.from_numpy(sar_slc).float()
        
        # Handle variable-sized point clouds
        N = lidar_points.shape[0]
        
        if N > self.max_points:
            # Subsample
            indices = torch.randperm(N)[:self.max_points]
            lidar_points = lidar_points[indices]
            N = self.max_points
        elif N < self.max_points:
            # Pad with zeros
            padding = torch.zeros(self.max_points - N, 4)
            lidar_points = torch.cat([lidar_points, padding], dim=0)
        
        # Create mask
        lidar_mask = torch.zeros(self.max_points, dtype=torch.bool)
        lidar_mask[:min(N, self.max_points)] = True
        
        # Split coordinates and features
        lidar_xyz = lidar_points[:, :3]
        lidar_features = lidar_points  # Keep all 4 channels
        
        # Apply augmentations
        if self.transform is not None:
            lidar_xyz, lidar_features, sar_slc = self.transform(
                lidar_xyz, lidar_features, sar_slc
            )
        
        sample = {
            'lidar_xyz': lidar_xyz,
            'lidar_features': lidar_features,
            'lidar_mask': lidar_mask,
            'sar_slc': sar_slc
        }
        
        if label >= 0:
            sample['label'] = torch.tensor(label, dtype=torch.long)
        
        return sample
