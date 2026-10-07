"""
Fusion Transformer - Cross-modal attention with asymmetric gating.

Fuses LiDAR and SAR features using multi-head cross-attention.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple
import logging
import math

logger = logging.getLogger(__name__)


class ModalityGating(nn.Module):
    """Learnable gating scalar per modality per layer."""
    
    def __init__(self, num_modalities: int = 2) -> None:
        super().__init__()
        self.gates = nn.Parameter(torch.ones(num_modalities))
    
    def forward(self) -> torch.Tensor:
        """Returns softmax-normalized gating weights."""
        return F.softmax(self.gates, dim=0)


class CrossAttentionBlock(nn.Module):
    """Multi-head cross-attention block."""
    
    def __init__(
        self,
        dim: int,
        num_heads: int = 8,
        dim_feedforward: int = 1024,
        dropout: float = 0.1
    ) -> None:
        super().__init__()
        self.num_heads = num_heads
        self.dim = dim
        
        # Cross-attention: Q from modality A, K/V from modality B
        self.cross_attn = nn.MultiheadAttention(
            dim, num_heads, dropout=dropout, batch_first=True
        )
        
        # Self-attention for refinement
        self.self_attn = nn.MultiheadAttention(
            dim, num_heads, dropout=dropout, batch_first=True
        )
        
        # Feed-forward
        self.ff = nn.Sequential(
            nn.Linear(dim, dim_feedforward),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim_feedforward, dim),
            nn.Dropout(dropout)
        )
        
        # Layer norms
        self.norm1 = nn.LayerNorm(dim)
        self.norm2 = nn.LayerNorm(dim)
        self.norm3 = nn.LayerNorm(dim)
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(
        self,
        query: torch.Tensor,
        key_value: torch.Tensor,
        query_mask: torch.Tensor | None = None
    ) -> torch.Tensor:
        """
        Args:
            query: (B, N_q, D) query features
            key_value: (B, N_kv, D) key/value features
            query_mask: (B, N_q) attention mask
            
        Returns:
            (B, N_q, D) updated query features
        """
        # Cross-attention
        attn_out, _ = self.cross_attn(
            query, key_value, key_value,
            key_padding_mask=query_mask
        )
        query = self.norm1(query + self.dropout(attn_out))
        
        # Self-attention
        self_out, _ = self.self_attn(query, query, query)
        query = self.norm2(query + self.dropout(self_out))
        
        # Feed-forward
        ff_out = self.ff(query)
        query = self.norm3(query + ff_out)
        
        return query


class FusionTransformer(nn.Module):
    """
    Cross-modal Transformer with asymmetric gating.
    
    Allows the model to down-weight less informative modalities per patch.
    """
    
    def __init__(
        self,
        dim: int = 256,
        num_layers: int = 4,
        num_heads: int = 8,
        dim_feedforward: int = 1024,
        dropout: float = 0.1,
        asymmetric_gating: bool = True
    ) -> None:
        """
        Args:
            dim: Feature dimension
            num_layers: Number of transformer layers
            num_heads: Number of attention heads
            dim_feedforward: FFN hidden dimension
            dropout: Dropout rate
            asymmetric_gating: Enable modality-specific gating
        """
        super().__init__()
        
        self.dim = dim
        self.num_layers = num_layers
        self.asymmetric_gating = asymmetric_gating
        
        # Cross-attention layers
        self.lidar_to_sar_layers = nn.ModuleList([
            CrossAttentionBlock(dim, num_heads, dim_feedforward, dropout)
            for _ in range(num_layers)
        ])
        
        self.sar_to_lidar_layers = nn.ModuleList([
            CrossAttentionBlock(dim, num_heads, dim_feedforward, dropout)
            for _ in range(num_layers)
        ])
        
        # Modality gating
        if asymmetric_gating:
            self.gates = nn.ModuleList([
                ModalityGating(num_modalities=2)
                for _ in range(num_layers)
            ])
        
        # Projection layers to match dimensions
        self.lidar_proj = nn.Linear(256, dim)  # From PointNet++ global
        self.sar_proj = nn.Linear(512, dim)    # From U-Net bottleneck
        
        logger.info(
            f"Fusion Transformer initialized: layers={num_layers}, "
            f"heads={num_heads}, gating={asymmetric_gating}"
        )
    
    def forward(
        self,
        lidar_features: torch.Tensor,
        sar_features: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Fuse LiDAR and SAR features via cross-attention.
        
        Args:
            lidar_features: (B, N_lidar, D_lidar) or (B, D_lidar)
            sar_features: (B, C_sar, H, W) or (B, D_sar)
            
        Returns:
            fused_lidar: (B, D) fused LiDAR representation
            fused_sar: (B, D) fused SAR representation
            z_common: (B, D) shared latent representation
        """
        B = lidar_features.shape[0]
        
        # Project to common dimension
        if lidar_features.dim() == 2:
            lidar_features = lidar_features.unsqueeze(1)  # (B, 1, D)
        
        lidar_proj = self.lidar_proj(lidar_features)  # (B, N, D)
        
        if sar_features.dim() == 4:
            # Flatten spatial dimensions
            B, C, H, W = sar_features.shape
            sar_features = sar_features.view(B, C, H * W).transpose(1, 2)  # (B, H*W, C)
        
        sar_proj = self.sar_proj(sar_features)  # (B, N, D)
        
        # Cross-attention fusion
        lidar_fused = lidar_proj
        sar_fused = sar_proj
        
        for i in range(self.num_layers):
            # LiDAR attends to SAR
            lidar_fused = self.lidar_to_sar_layers[i](lidar_fused, sar_fused)
            
            # SAR attends to LiDAR
            sar_fused = self.sar_to_lidar_layers[i](sar_fused, lidar_fused)
            
            # Apply gating
            if self.asymmetric_gating:
                gate_weights = self.gates[i]()
                # gate_weights[0] for LiDAR, gate_weights[1] for SAR
                lidar_fused = lidar_fused * gate_weights[0]
                sar_fused = sar_fused * gate_weights[1]
        
        # Global pooling
        fused_lidar = lidar_fused.mean(dim=1)  # (B, D)
        fused_sar = sar_fused.mean(dim=1)      # (B, D)
        
        # Common representation (average of both)
        z_common = (fused_lidar + fused_sar) / 2
        
        return fused_lidar, fused_sar, z_common
