"""
LiDAR Encoder - PointNet++ based architecture for sparse point cloud encoding.

This module implements a PointNet++ encoder that processes variable-sized
3D point clouds with (x, y, z, intensity) features and produces both
local neighborhood features and global point features.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SharedMLP(nn.Module):
    """Shared MLP layers for point feature extraction."""
    
    def __init__(self, in_channels: int, out_channels: list[int]) -> None:
        """
        Args:
            in_channels: Input feature dimension
            out_channels: List of output dimensions for each layer
        """
        super().__init__()
        layers = []
        for out_ch in out_channels:
            layers.extend([
                nn.Conv1d(in_channels, out_ch, kernel_size=1),
                nn.BatchNorm1d(out_ch),
                nn.ReLU(inplace=True)
            ])
            in_channels = out_ch
        self.mlp = nn.Sequential(*layers)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, C, N) point features
            
        Returns:
            (B, C_out, N) transformed features
        """
        return self.mlp(x)


class PointNetPPSetAbstraction(nn.Module):
    """Set abstraction layer with KNN grouping."""
    
    def __init__(
        self,
        in_channels: int,
        mlp_channels: list[int],
        k: int = 16
    ) -> None:
        """
        Args:
            in_channels: Input feature dimension
            mlp_channels: MLP output channels
            k: Number of nearest neighbors
        """
        super().__init__()
        self.k = k
        self.mlp = SharedMLP(in_channels, mlp_channels)
        self.out_channels = mlp_channels[-1]
    
    def forward(
        self,
        xyz: torch.Tensor,
        features: Optional[torch.Tensor] = None,
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            xyz: (B, N, 3) point coordinates
            features: (B, C, N) point features (optional)
            mask: (B, N) boolean mask for valid points (optional)
            
        Returns:
            new_xyz: (B, N', 3) sampled points
            new_features: (B, C_out, N') grouped and transformed features
        """
        B, N, _ = xyz.shape
        
        # Use all points (no subsampling for simplicity)
        new_xyz = xyz
        
        if features is None:
            features = xyz.transpose(1, 2)  # (B, 3, N)
        
        # KNN grouping with mask support
        grouped_features = self._knn_group(xyz, features, mask)  # (B, C, N, k)
        
        # Apply MLP
        B, C, N_pts, K = grouped_features.shape
        grouped_features = grouped_features.view(B * N_pts, C, K)
        grouped_features = self.mlp(grouped_features)
        grouped_features = grouped_features.view(B, N_pts, -1, K)
        
        # Max pooling over neighbors
        new_features, _ = torch.max(grouped_features, dim=-1)  # (B, N, C_out)
        new_features = new_features.transpose(1, 2)  # (B, C_out, N)
        
        return new_xyz, new_features
    
    def _knn_group(
        self,
        xyz: torch.Tensor,
        features: torch.Tensor,
        mask: torch.Tensor | None = None
    ) -> torch.Tensor:
        """
        Group features by KNN with mask support.
        
        Args:
            xyz: (B, N, 3)
            features: (B, C, N)
            mask: (B, N) optional mask for valid points
            
        Returns:
            grouped: (B, C, N, k)
        """
        B, N, _ = xyz.shape
        _, C, _ = features.shape
        
        # Handle small point clouds: use effective_k
        effective_k = min(self.k, N - 1)
        if effective_k < 1:
            effective_k = 1
        
        # Compute pairwise distances
        dist = torch.cdist(xyz, xyz)  # (B, N, N)
        
        # Apply mask if provided: set padding distances to inf
        if mask is not None:
            # mask is (B, N), we need (B, N, N) for distances
            mask_expanded = mask.unsqueeze(1) & mask.unsqueeze(2)  # (B, N, N)
            dist = dist.masked_fill(~mask_expanded, float('inf'))
        
        # Get k nearest neighbors (excluding self)
        _, indices = torch.topk(dist, effective_k + 1, dim=-1, largest=False)
        indices = indices[:, :, 1:]  # Remove self (B, N, effective_k)
        
        # Pad if effective_k < self.k
        if effective_k < self.k:
            padding = indices[:, :, -1:].expand(-1, -1, self.k - effective_k)
            indices = torch.cat([indices, padding], dim=-1)
        
        # Gather features
        indices = indices.unsqueeze(1).expand(-1, C, -1, -1)  # (B, C, N, k)
        features_expanded = features.unsqueeze(-1).expand(-1, -1, -1, self.k)
        grouped = torch.gather(features_expanded, 2, indices)
        
        return grouped


class PointNetPPEncoder(nn.Module):
    """
    Complete PointNet++ encoder with shared MLPs and set abstraction.
    
    Produces both local neighborhood features and global point features.
    """
    
    def __init__(
        self,
        in_channels: int = 4,
        shared_mlp_layers: list[int] = [64, 128, 256],
        knn_k: int = 16,
        local_mlp_layers: list[int] = [64, 128, 256],
        global_mlp_layers: list[int] = [512, 1024]
    ) -> None:
        """
        Args:
            in_channels: Input point features (x, y, z, intensity)
            shared_mlp_layers: Shared MLP output dimensions
            knn_k: Number of nearest neighbors
            local_mlp_layers: Local feature MLP dimensions
            global_mlp_layers: Global feature MLP dimensions
        """
        super().__init__()
        
        # Shared MLP for initial feature extraction
        self.shared_mlp = SharedMLP(in_channels, shared_mlp_layers)
        
        # Set abstraction for local features
        self.sa_layer = PointNetPPSetAbstraction(
            in_channels=shared_mlp_layers[-1],
            mlp_channels=local_mlp_layers,
            k=knn_k
        )
        
        # Global feature extraction via max pooling
        self.global_mlp = SharedMLP(
            local_mlp_layers[-1],
            global_mlp_layers
        )
        
        self.local_dim = local_mlp_layers[-1]
        self.global_dim = global_mlp_layers[-1]
        
        logger.info(
            f"PointNet++ encoder initialized: local_dim={self.local_dim}, "
            f"global_dim={self.global_dim}"
        )
    
    def forward(
        self,
        xyz: torch.Tensor,
        features: Optional[torch.Tensor] = None,
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Encode point cloud into local and global features.
        
        Args:
            xyz: (B, N, 3) point coordinates
            features: (B, N, C) point features (default: xyz)
            mask: (B, N) boolean mask for valid points
            
        Returns:
            local_features: (B, N, local_dim) local neighborhood features
            global_features: (B, global_dim) global point cloud feature
        """
        B, N, _ = xyz.shape
        
        if features is None:
            features = xyz  # (B, N, 3)
        
        # Transpose for Conv1d: (B, C, N)
        features = features.transpose(1, 2)
        
        # Apply mask if provided
        if mask is not None:
            mask_expanded = mask.unsqueeze(1).float()  # (B, 1, N)
            features = features * mask_expanded
        
        # Shared MLP
        shared_features = self.shared_mlp(features)  # (B, C_shared, N)
        
        # Set abstraction for local features with mask
        _, local_features = self.sa_layer(xyz, shared_features, mask)
        local_features = local_features.transpose(1, 2)  # (B, N, local_dim)
        
        # Global feature via max pooling
        if mask is not None:
            # Masked max pooling
            local_features_masked = local_features.clone()
            local_features_masked[~mask] = float('-inf')
            global_features, _ = torch.max(local_features_masked, dim=1)
        else:
            global_features, _ = torch.max(local_features, dim=1)
        
        global_features = global_features.unsqueeze(-1)  # (B, local_dim, 1)
        global_features = self.global_mlp(global_features)
        global_features = global_features.squeeze(-1)  # (B, global_dim)
        
        return local_features, global_features
