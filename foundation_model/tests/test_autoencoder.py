"""
Unit tests for multimodal autoencoder.

Verifies forward pass, gradient flow, and reconstruction loss.
"""

import torch
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import MultimodalAutoencoder
from losses import ReconstructionLoss


@pytest.fixture
def model():
    """Create a small model for testing."""
    return MultimodalAutoencoder(
        latent_dim=64,
        lidar_config={
            'in_channels': 4,
            'shared_mlp_layers': [32, 64],
            'knn_k': 8,
            'local_mlp_layers': [32, 64],
            'global_mlp_layers': [128, 256],
            'num_points': 512,
            'output_channels': 4
        },
        sar_config={
            'in_channels': 2,
            'encoder_channels': [32, 64, 128],
            'decoder_channels': [64, 32],
            'residual_connections': True,
            'output_channels': 2
        },
        fusion_config={
            'num_layers': 2,
            'num_heads': 4,
            'dim_feedforward': 128,
            'dropout': 0.1,
            'asymmetric_gating': True
        }
    )


@pytest.fixture
def synthetic_batch():
    """Create synthetic LiDAR-SAR batch."""
    B = 2
    N = 512
    H, W = 64, 64
    
    lidar_xyz = torch.randn(B, N, 3)
    lidar_features = torch.randn(B, N, 4)
    lidar_mask = torch.ones(B, N, dtype=torch.bool)
    sar_slc = torch.randn(B, 2, H, W)
    
    return {
        'lidar_xyz': lidar_xyz,
        'lidar_features': lidar_features,
        'lidar_mask': lidar_mask,
        'sar_slc': sar_slc
    }


def test_forward_pass_shapes(model, synthetic_batch):
    """Test that forward pass produces correct output shapes."""
    output = model(
        synthetic_batch['lidar_xyz'],
        synthetic_batch['lidar_features'],
        synthetic_batch['sar_slc'],
        synthetic_batch['lidar_mask']
    )
    
    # Check latents
    assert output['z_lidar'].shape == (2, 64)
    assert output['z_sar'].shape == (2, 64)
    assert output['z_common'].shape == (2, 64)
    
    # Check reconstructions
    assert output['lidar_points'].shape == (2, 512, 4)
    assert output['lidar_density'].shape == (2, 512)
    assert output['sar_slc'].shape[0] == 2
    assert output['sar_slc'].shape[1] == 2


def test_gradient_flow(model, synthetic_batch):
    """Test that gradients flow through all parameters."""
    output = model(
        synthetic_batch['lidar_xyz'],
        synthetic_batch['lidar_features'],
        synthetic_batch['sar_slc'],
        synthetic_batch['lidar_mask']
    )
    
    # Compute dummy loss
    loss = output['z_common'].sum()
    loss.backward()
    
    # Check that all parameters have gradients
    for name, param in model.named_parameters():
        if param.requires_grad:
            assert param.grad is not None, f"No gradient for {name}"


def test_reconstruction_loss_decreases(model, synthetic_batch):
    """Test that reconstruction loss decreases over 2 steps."""
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    recon_loss_fn = ReconstructionLoss()
    
    losses = []
    
    for _ in range(2):
        optimizer.zero_grad()
        
        output = model(
            synthetic_batch['lidar_xyz'],
            synthetic_batch['lidar_features'],
            synthetic_batch['sar_slc'],
            synthetic_batch['lidar_mask']
        )
        
        recon_losses = recon_loss_fn(
            output['lidar_points'],
            synthetic_batch['lidar_features'],
            output['sar_slc'],
            synthetic_batch['sar_slc'],
            synthetic_batch['lidar_mask']
        )
        
        loss = recon_losses['total']
        loss.backward()
        optimizer.step()
        
        losses.append(loss.item())
    
    # Loss should decrease
    assert losses[1] < losses[0], f"Loss did not decrease: {losses[0]} -> {losses[1]}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
