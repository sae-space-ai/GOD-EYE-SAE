"""
LiDAR Decoder - Reconstructs point clouds from latent representation.

Produces per-point (x, y, z, intensity) + density estimate.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class PointCloudDecoder(nn.Module):
    """
    MLP-based decoder for point cloud reconstruction.
    
    Reconstructs (x, y, z, intensity) + density from latent vector.
    """
    
    def __init__(
        self,
        latent_dim: int = 256,
        num_points: int = 8192,
        hidden_dims: list[int] = [512, 1024, 2048],
        output_channels: int = 4  # x, y, z, intensity
    ) -> None:
        """
        Args:
            latent_dim: Input latent dimension
            num_points: Number of points to generate
            hidden_dims: Hidden layer dimensions
            output_channels: Output per point (xyz + intensity)
        """
        super().__init__()
        
        self.num_points = num_points
        self.output_channels = output_channels
        
        # Build MLP
        layers = []
        in_dim = latent_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(in_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(inplace=True)
            ])
            in_dim = hidden_dim
        
        self.mlp = nn.Sequential(*layers)
        
        # Output heads
        self.point_head = nn.Linear(hidden_dims[-1], num_points * output_channels)
        self.density_head = nn.Linear(hidden_dims[-1], num_points)
        
        logger.info(
            f"LiDAR decoder initialized: num_points={num_points}, "
            f"output_channels={output_channels}"
        )
    
    def forward(self, z: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Decode latent vector into point cloud.
        
        Args:
            z: (B, latent_dim) latent representation
            
        Returns:
            points: (B, N, 4) reconstructed points (x, y, z, intensity)
            density: (B, N) density estimates
        """
        B = z.shape[0]
        
        # Shared MLP
        features = self.mlp(z)  # (B, hidden_dim)
        
        # Point reconstruction
        points = self.point_head(features)  # (B, N * output_channels)
        points = points.view(B, self.num_points, self.output_channels)
        
        # Density estimation
        density = self.density_head(features)  # (B, N)
        density = torch.sigmoid(density)  # Normalize to [0, 1]
        
        return points, density
