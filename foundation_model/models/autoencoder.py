"""
Complete Multimodal Autoencoder - LiDAR-SAR Foundation Model.

Combines encoders, fusion transformer, and decoders for self-supervised training.
"""

import torch
import torch.nn as nn
from typing import Tuple, Dict
import logging

from .lidar_encoder import PointNetPPEncoder
from .sar_encoder import UNetEncoder
from .fusion_transformer import FusionTransformer
from .lidar_decoder import PointCloudDecoder
from .sar_decoder import SARDecoder

logger = logging.getLogger(__name__)


class MultimodalAutoencoder(nn.Module):
    """
    Complete multimodal autoencoder for LiDAR-SAR fusion.
    
    Encodes each modality separately, fuses via cross-attention,
    and reconstructs both modalities from shared latent space.
    """
    
    def __init__(
        self,
        latent_dim: int = 256,
        lidar_config: dict | None = None,
        sar_config: dict | None = None,
        fusion_config: dict | None = None
    ) -> None:
        """
        Args:
            latent_dim: Shared latent dimension
            lidar_config: LiDAR encoder/decoder configuration
            sar_config: SAR encoder/decoder configuration
            fusion_config: Fusion transformer configuration
        """
        super().__init__()
        
        self.latent_dim = latent_dim
        
        # Default configs
        lidar_config = lidar_config or {}
        sar_config = sar_config or {}
        fusion_config = fusion_config or {}
        
        # LiDAR branch
        self.lidar_encoder = PointNetPPEncoder(
            in_channels=lidar_config.get('in_channels', 4),
            shared_mlp_layers=lidar_config.get('shared_mlp_layers', [64, 128, 256]),
            knn_k=lidar_config.get('knn_k', 16),
            local_mlp_layers=lidar_config.get('local_mlp_layers', [64, 128, 256]),
            global_mlp_layers=lidar_config.get('global_mlp_layers', [512, 1024])
        )
        
        self.lidar_decoder = PointCloudDecoder(
            latent_dim=latent_dim,
            num_points=lidar_config.get('num_points', 8192),
            output_channels=lidar_config.get('output_channels', 4)
        )
        
        # SAR branch
        self.sar_encoder = UNetEncoder(
            in_channels=sar_config.get('in_channels', 2),
            encoder_channels=sar_config.get('encoder_channels', [64, 128, 256, 512]),
            use_residual=sar_config.get('residual_connections', True)
        )
        
        self.sar_decoder = SARDecoder(
            latent_channels=sar_config.get('encoder_channels', [64, 128, 256, 512])[-1],
            decoder_channels=sar_config.get('decoder_channels', [256, 128, 64]),
            output_channels=sar_config.get('output_channels', 2)
        )
        
        # Fusion transformer
        self.fusion = FusionTransformer(
            dim=latent_dim,
            num_layers=fusion_config.get('num_layers', 4),
            num_heads=fusion_config.get('num_heads', 8),
            dim_feedforward=fusion_config.get('dim_feedforward', 1024),
            dropout=fusion_config.get('dropout', 0.1),
            asymmetric_gating=fusion_config.get('asymmetric_gating', True)
        )
        
        # Projection to latent space
        self.lidar_to_latent = nn.Linear(1024, latent_dim)
        self.sar_to_latent = nn.Linear(512, latent_dim)
        
        # Count parameters
        total_params = sum(p.numel() for p in self.parameters())
        logger.info(f"Multimodal Autoencoder initialized: {total_params / 1e6:.2f}M parameters")
    
    def encode(
        self,
        lidar_xyz: torch.Tensor,
        lidar_features: torch.Tensor | None,
        sar_image: torch.Tensor,
        lidar_mask: torch.Tensor | None = None
    ) -> Dict[str, torch.Tensor]:
        """
        Encode both modalities and fuse.
        
        Args:
            lidar_xyz: (B, N, 3) LiDAR point coordinates
            lidar_features: (B, N, C) LiDAR features (optional)
            sar_image: (B, 2, H, W) SAR SLC image
            lidar_mask: (B, N) mask for valid points
            
        Returns:
            Dictionary with:
                - z_lidar: LiDAR latent
                - z_sar: SAR latent
                - z_common: Shared latent
                - z_unique_lidar: LiDAR-unique latent
                - z_unique_sar: SAR-unique latent
        """
        # Encode LiDAR
        lidar_local, lidar_global = self.lidar_encoder(
            lidar_xyz, lidar_features, lidar_mask
        )
        
        # Encode SAR
        sar_bottleneck, sar_skips = self.sar_encoder(sar_image)
        
        # Project to latent dimension
        z_lidar = self.lidar_to_latent(lidar_global)  # (B, latent_dim)
        z_sar = self.sar_to_latent(sar_bottleneck.mean(dim=[2, 3]))  # (B, latent_dim)
        
        # Fuse via cross-attention
        fused_lidar, fused_sar, z_common = self.fusion(
            z_lidar.unsqueeze(1),  # (B, 1, D)
            z_sar.unsqueeze(1)     # (B, 1, D)
        )
        
        fused_lidar = fused_lidar.squeeze(1)  # (B, D)
        fused_sar = fused_sar.squeeze(1)      # (B, D)
        
        # Decompose into common and unique (DeCUR-style)
        z_unique_lidar = z_lidar - z_common
        z_unique_sar = z_sar - z_common
        
        return {
            'z_lidar': fused_lidar,
            'z_sar': fused_sar,
            'z_common': z_common,
            'z_unique_lidar': z_unique_lidar,
            'z_unique_sar': z_unique_sar,
            'sar_skips': sar_skips,
            'sar_bottleneck': sar_bottleneck
        }
    
    def decode(
        self,
        z_lidar: torch.Tensor,
        z_sar: torch.Tensor,
        sar_skips: list[torch.Tensor],
        sar_bottleneck: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Decode latent representations back to original modalities.
        
        Args:
            z_lidar: (B, D) LiDAR latent
            z_sar: (B, D) SAR latent
            sar_skips: Skip connections from SAR encoder
            sar_bottleneck: SAR bottleneck features
            
        Returns:
            Dictionary with:
                - lidar_points: (B, N, 4) reconstructed points
                - lidar_density: (B, N) density estimates
                - sar_slc: (B, 2, H, W) reconstructed SLC
        """
        # Decode LiDAR
        lidar_points, lidar_density = self.lidar_decoder(z_lidar)
        
        # Decode SAR
        sar_slc = self.sar_decoder(sar_bottleneck, sar_skips)
        
        return {
            'lidar_points': lidar_points,
            'lidar_density': lidar_density,
            'sar_slc': sar_slc
        }
    
    def forward(
        self,
        lidar_xyz: torch.Tensor,
        lidar_features: torch.Tensor | None,
        sar_image: torch.Tensor,
        lidar_mask: torch.Tensor | None = None
    ) -> Dict[str, torch.Tensor]:
        """
        Full forward pass: encode, fuse, decode.
        
        Args:
            lidar_xyz: (B, N, 3) LiDAR points
            lidar_features: (B, N, C) LiDAR features
            sar_image: (B, 2, H, W) SAR SLC
            lidar_mask: (B, N) valid point mask
            
        Returns:
            Dictionary with all latents and reconstructions
        """
        # Encode
        encoded = self.encode(lidar_xyz, lidar_features, sar_image, lidar_mask)
        
        # Decode
        decoded = self.decode(
            encoded['z_lidar'],
            encoded['z_sar'],
            encoded['sar_skips'],
            encoded['sar_bottleneck']
        )
        
        # Combine outputs
        output = {**encoded, **decoded}
        
        return output
