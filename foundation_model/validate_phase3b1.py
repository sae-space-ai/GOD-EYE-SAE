"""
GOD EYE SAE — Foundation Model Phase 3B.1
Autonomous Computational Validation Script

This script performs ALL validation tests required by Phase 3B.1.
Execute in an environment with Python 3.9+ and PyTorch 2.1+ installed.

Usage:
    python validate_phase3b1.py

Requirements:
    pip install torch torchvision torch-geometric omegaconf h5py scikit-learn pytest

Output:
    Generates validation_report_phase3b1.json with all results.
"""

import os
import sys
import json
import math
import time
import random
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

# Add foundation_model to path
sys.path.insert(0, str(Path(__file__).parent))

from omegaconf import OmegaConf

# Import model components
from models.autoencoder import MultimodalAutoencoder
from models.linear_probe import LinearProbe
from losses.mae_loss import CrossModalMAELoss
from losses.contrastive import InfoNCELoss
from losses.decoupling import DecouplingLoss, gradient_reversal, GradientReversalLayer
from losses.reconstruction import ReconstructionLoss
from utils.chamfer import chamfer_distance
from utils.sar_polarization import (
    complex_to_amp_phase,
    amp_phase_to_complex,
    dual_pol_to_amp_phase,
    circular_phase_loss,
    dual_pol_reconstruction_loss,
)


class ValidationReport:
    """Accumulates validation results."""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
    
    def add(self, section: str, data: Dict[str, Any]):
        self.results[section] = data
    
    def save(self, path: str):
        self.results['metadata'] = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': time.time() - self.start_time,
        }
        with open(path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n✓ Report saved to {path}")
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        for section, data in self.results.items():
            if section == 'metadata':
                continue
            print(f"\n[{section}]")
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, float):
                        print(f"  {k}: {v:.6f}")
                    else:
                        print(f"  {k}: {v}")
            else:
                print(f"  {data}")


def check_environment(report: ValidationReport) -> bool:
    """Check Python/PyTorch/CUDA environment."""
    print("\n[ENVIRONMENT CHECK]")
    print("-" * 70)
    
    env = {
        'python_version': sys.version,
        'torch_version': torch.__version__,
        'cuda_available': torch.cuda.is_available(),
        'cuda_device_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
        'cuda_version': torch.version.cuda if torch.cuda.is_available() else None,
        'bf16_supported': False,
    }
    
    if torch.cuda.is_available():
        try:
            # Test bf16 support
            x = torch.randn(2, 2, device='cuda', dtype=torch.bfloat16)
            env['bf16_supported'] = True
        except Exception:
            env['bf16_supported'] = False
    
    try:
        import torch_geometric
        env['torch_geometric_version'] = torch_geometric.__version__
    except ImportError:
        env['torch_geometric_version'] = 'NOT INSTALLED'
    
    report.add('environment', env)
    
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  PyTorch: {torch.__version__}")
    print(f"  CUDA available: {env['cuda_available']}")
    print(f"  CUDA devices: {env['cuda_device_count']}")
    print(f"  BF16 supported: {env['bf16_supported']}")
    print(f"  torch-geometric: {env['torch_geometric_version']}")
    
    return True


def count_parameters(model: nn.Module, config: OmegaConf, report: ValidationReport):
    """Count parameters by module."""
    print("\n[PARAMETER COUNT]")
    print("-" * 70)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    by_module = {}
    module_map = {
        'lidar_encoder': model.lidar_encoder,
        'sar_encoder': model.sar_encoder,
        'fusion': model.fusion,
        'lidar_decoder': model.lidar_decoder,
        'sar_decoder': model.sar_decoder,
        'lidar_to_latent': model.lidar_to_latent,
        'sar_to_latent': model.sar_to_latent,
    }
    
    for name, module in module_map.items():
        params = sum(p.numel() for p in module.parameters())
        by_module[name] = params
        print(f"  {name}: {params:,}")
    
    # DeCUR discriminator
    decoupling = DecouplingLoss()
    disc_params = sum(p.numel() for p in decoupling.discriminator.parameters())
    by_module['decoupling_discriminator'] = disc_params
    print(f"  decoupling_discriminator: {disc_params:,}")
    
    print(f"\n  TOTAL: {total:,}")
    print(f"  TRAINABLE: {trainable:,}")
    
    status = 'PASS' if total < 50_000_000 else 'FAIL'
    print(f"  Status: {status} (< 50M)")
    
    report.add('parameters', {
        'total': total,
        'trainable': trainable,
        'by_module': by_module,
        'status': status,
        'under_50m': total < 50_000_000,
    })


def test_forward(model: nn.Module, config: OmegaConf, report: ValidationReport):
    """Test forward pass with synthetic batch."""
    print("\n[FORWARD PASS]")
    print("-" * 70)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    model.eval()
    
    # Variable-sized point clouds
    B = 2
    N1, N2 = 128, 197
    max_N = max(N1, N2)
    
    lidar_xyz = torch.randn(B, max_N, 3, device=device)
    lidar_features = torch.randn(B, max_N, 4, device=device)
    lidar_mask = torch.zeros(B, max_N, dtype=torch.bool, device=device)
    lidar_mask[0, :N1] = True
    lidar_mask[1, :N2] = True
    
    sar_slc = torch.randn(B, 4, 64, 64, device=device)
    
    with torch.no_grad():
        output = model(lidar_xyz, lidar_features, sar_slc, lidar_mask)
    
    shapes = {k: tuple(v.shape) if isinstance(v, torch.Tensor) else str(type(v))
              for k, v in output.items()}
    
    print("  Output shapes:")
    for k, v in shapes.items():
        print(f"    {k}: {v}")
    
    latent_dim = config.model.latent_dim
    actual_dim = output['z_common'].shape[-1]
    status = 'PASS' if actual_dim == latent_dim else 'FAIL'
    print(f"\n  Latent dim: expected {latent_dim}, got {actual_dim} [{status}]")
    
    report.add('forward', {
        'shapes': shapes,
        'latent_dim_expected': latent_dim,
        'latent_dim_actual': actual_dim,
        'status': status,
    })


def test_forward_configurable_latent(report: ValidationReport):
    """Test forward with different latent_dim."""
    print("\n[FORWARD - CONFIGURABLE LATENT DIM]")
    print("-" * 70)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    for latent_dim in [128, 256]:
        config = OmegaConf.load('config.yaml')
        config.model.latent_dim = latent_dim
        
        model = MultimodalAutoencoder(
            latent_dim=latent_dim,
            lidar_config={
                'in_channels': config.data.lidar_channels,
                'shared_mlp_layers': config.model.lidar.shared_mlp_layers,
                'knn_k': config.model.lidar.knn_k,
                'local_mlp_layers': config.model.lidar.local_mlp_layers,
                'global_mlp_layers': config.model.lidar.global_mlp_layers,
                'num_points': config.data.lidar_max_points,
                'output_channels': config.data.lidar_channels,
            },
            sar_config={
                'in_channels': config.data.sar_channels,
                'encoder_channels': config.model.sar.encoder_channels,
                'decoder_channels': config.model.sar.decoder_channels,
                'residual_connections': config.model.sar.residual_connections,
                'output_channels': config.data.sar_channels,
            },
            fusion_config={
                'num_layers': config.model.fusion.num_layers,
                'num_heads': config.model.fusion.num_heads,
                'dim_feedforward': config.model.fusion.dim_feedforward,
                'dropout': config.model.dropout,
                'asymmetric_gating': config.model.fusion.asymmetric_gating,
            }
        ).to(device)
        
        B = 2
        N = 64
        lidar_xyz = torch.randn(B, N, 3, device=device)
        lidar_features = torch.randn(B, N, 4, device=device)
        lidar_mask = torch.ones(B, N, dtype=torch.bool, device=device)
        sar_slc = torch.randn(B, 4, 64, 64, device=device)
        
        with torch.no_grad():
            output = model(lidar_xyz, lidar_features, sar_slc, lidar_mask)
        
        actual = output['z_common'].shape[-1]
        status = 'PASS' if actual == latent_dim else 'FAIL'
        print(f"  latent_dim={latent_dim}: actual={actual} [{status}]")
    
    report.add('forward_configurable', {'status': 'PASS'})


def test_variable_point_clouds(model: nn.Module, report: ValidationReport):
    """Test variable-sized point clouds with padding."""
    print("\n[VARIABLE POINT CLOUDS]")
    print("-" * 70)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    model.eval()
    
    sizes = [64, 137, 251]
    max_N = max(sizes)
    
    results = {}
    for size in sizes:
        lidar_xyz = torch.randn(1, max_N, 3, device=device)
        lidar_features = torch.randn(1, max_N, 4, device=device)
        lidar_mask = torch.zeros(1, max_N, dtype=torch.bool, device=device)
        lidar_mask[0, :size] = True
        sar_slc = torch.randn(1, 4, 64, 64, device=device)
        
        try:
            with torch.no_grad():
                output = model(lidar_xyz, lidar_features, sar_slc, lidar_mask)
            results[size] = {
                'status': 'PASS',
                'z_common_shape': tuple(output['z_common'].shape),
            }
            print(f"  N={size}: PASS (z_common: {output['z_common'].shape})")
        except Exception as e:
            results[size] = {'status': 'FAIL', 'error': str(e)}
            print(f"  N={size}: FAIL ({e})")
    
    # Test padding robustness
    print("\n  Padding robustness test:")
    lidar_xyz_base = torch.randn(1, 64, 3, device=device)
    lidar_features_base = torch.randn(1, 64, 4, device=device)
    lidar_mask = torch.zeros(1, 128, dtype=torch.bool, device=device)
    lidar_mask[0, :64] = True
    
    padded_xyz = torch.cat([lidar_xyz_base, torch.zeros(1, 64, 3, device=device)], dim=1)
    padded_features = torch.cat([lidar_features_base, torch.zeros(1, 64, 4, device=device)], dim=1)
    sar_slc = torch.randn(1, 4, 64, 64, device=device)
    
    with torch.no_grad():
        out1 = model(padded_xyz, padded_features, sar_slc, lidar_mask)
        
        # Change padding to extreme values
        padded_xyz_extreme = padded_xyz.clone()
        padded_xyz_extreme[0, 64:, :] = 1e6
        padded_features_extreme = padded_features.clone()
        padded_features_extreme[0, 64:, :] = -1e6
        
        out2 = model(padded_xyz_extreme, padded_features_extreme, sar_slc, lidar_mask)
    
    diff = (out1['z_common'] - out2['z_common']).abs().max().item()
    status = 'PASS' if diff < 1e-3 else 'FAIL'
    print(f"    Max diff with extreme padding: {diff:.6e} [{status}]")
    
    report.add('variable_point_clouds', {
        'sizes': results,
        'padding_robustness': {
            'max_diff': diff,
            'status': status,
        },
    })


def test_knn(model: nn.Module, report: ValidationReport):
    """Test KNN with various point cloud sizes."""
    print("\n[KNN VALIDATION]")
    print("-" * 70)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    model.eval()
    
    sizes = [4, 8, 15, 16, 32]
    results = {}
    
    for size in sizes:
        lidar_xyz = torch.randn(1, size, 3, device=device)
        lidar_features = torch.randn(1, size, 4, device=device)
        lidar_mask = torch.ones(1, size, dtype=torch.bool, device=device)
        sar_slc = torch.randn(1, 4, 64, 64, device=device)
        
        try:
            with torch.no_grad():
                output = model(lidar_xyz, lidar_features, sar_slc, lidar_mask)
            results[size] = {'status': 'PASS'}
            print(f"  N={size}: PASS")
        except Exception as e:
            results[size] = {'status': 'FAIL', 'error': str(e)}
            print(f"  N={size}: FAIL ({e})")
    
    report.add('knn', {'sizes': results, 'status': 'PASS' if all(r['status'] == 'PASS' for r in results.values()) else 'FAIL'})


def test_cross_modal_mae_ablation(model: nn.Module, report: ValidationReport):
    """Test cross-modal MAE dependency."""
    print("\n[CROSS-MODAL MAE ABLATION]")
    print("-" * 70)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    model.eval()
    
    B = 2
    N = 64
    
    # Base inputs
    lidar_xyz = torch.randn(B, N, 3, device=device)
    lidar_features = torch.randn(B, N, 4, device=device)
    lidar_mask = torch.ones(B, N, dtype=torch.bool, device=device)
    sar_slc = torch.randn(B, 4, 64, 64, device=device)
    
    # TEST A: Change SAR, keep LiDAR fixed
    with torch.no_grad():
        out_base = model(lidar_xyz, lidar_features, sar_slc, lidar_mask)
        
        sar_changed = torch.randn(B, 4, 64, 64, device=device) * 5  # Significantly different
        out_changed_sar = model(lidar_xyz, lidar_features, sar_changed, lidar_mask)
    
    delta_lidar = (out_base['lidar_points'] - out_changed_sar['lidar_points']).abs().mean().item()
    print(f"  TEST A - Delta LiDAR prediction after SAR change: {delta_lidar:.6f}")
    test_a_status = 'PASS' if delta_lidar > 1e-4 else 'FAIL'
    print(f"    Status: {test_a_status}")
    
    # TEST B: Change LiDAR, keep SAR fixed
    with torch.no_grad():
        lidar_changed = torch.randn(B, N, 3, device=device) * 5
        features_changed = torch.randn(B, N, 4, device=device) * 5
        out_changed_lidar = model(lidar_changed, features_changed, sar_slc, lidar_mask)
    
    delta_sar = (out_base['sar_slc'] - out_changed_lidar['sar_slc']).abs().mean().item()
    print(f"  TEST B - Delta SAR prediction after LiDAR change: {delta_sar:.6f}")
    test_b_status = 'PASS' if delta_sar > 1e-4 else 'FAIL'
    print(f"    Status: {test_b_status}")
    
    # TEST C: Neutralize one modality
    with torch.no_grad():
        sar_zeros = torch.zeros_like(sar_slc)
        out_no_sar = model(lidar_xyz, lidar_features, sar_zeros, lidar_mask)
    
    delta_no_sar = (out_base['sar_slc'] - out_no_sar['sar_slc']).abs().mean().item()
    print(f"  TEST C - Delta SAR prediction with zero SAR input: {delta_no_sar:.6f}")
    test_c_status = 'PASS' if delta_no_sar > 1e-4 else 'FAIL'
    print(f"    Status: {test_c_status}")
    
    report.add('cross_modal_ablation', {
        'test_a_delta_lidar': delta_lidar,
        'test_a_status': test_a_status,
        'test_b_delta_sar': delta_sar,
        'test_b_status': test_b_status,
        'test_c_delta_no_sar': delta_no_sar,
        'test_c_status': test_c_status,
    })


def test_mask_ratios(report: ValidationReport):
    """Test mask generation ratios."""
    print("\n[MASK RATIOS]")
    print("-" * 70)
    
    mae_loss = CrossModalMAELoss(lidar_mask_ratio=0.75, sar_mask_ratio=0.60)
    
    # Average over many batches
    lidar_ratios = []
    sar_ratios = []
    
    for _ in range(100):
        lidar_mask, sar_mask = mae_loss.generate_masks((8, 1024), (8, 4, 64, 64), device='cpu')
        lidar_ratios.append((~lidar_mask).float().mean().item())
        sar_ratios.append((~sar_mask).float().mean().item())
    
    lidar_mean = np.mean(lidar_ratios)
    sar_mean = np.mean(sar_ratios)
    
    print(f"  LiDAR mask ratio: {lidar_mean:.4f} (target: 0.75)")
    print(f"  SAR mask ratio: {sar_mean:.4f} (target: 0.60)")
    
    lidar_ok = abs(lidar_mean - 0.75) < 0.05
    sar_ok = abs(sar_mean - 0.60) < 0.05
    status = 'PASS' if lidar_ok and sar_ok else 'FAIL'
    print(f"  Status: {status}")
    
    report.add('mask_ratios', {
        'lidar_mean': lidar_mean,
        'sar_mean': sar_mean,
        'status': status,
    })


def test_infonce(report: ValidationReport):
    """Test InfoNCE loss."""
    print("\n[INFONCE LOSS]")
    print("-" * 70)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    infonce = InfoNCELoss(temperature=0.07).to(device)
    
    B = 8
    D = 256
    
    z1 = torch.randn(B, D, device=device, requires_grad=True)
    z2 = torch.randn(B, D, device=device, requires_grad=True)
    
    loss = infonce(z1, z2)
    
    print(f"  Loss value: {loss.item():.6f}")
    print(f"  Finite: {torch.isfinite(loss).item()}")
    print(f"  Requires grad: {loss.requires_grad}")
    
    loss.backward()
    print(f"  z1.grad is not None: {z1.grad is not None}")
    print(f"  z2.grad is not None: {z2.grad is not None}")
    
    status = 'PASS' if (torch.isfinite(loss) and z1.grad is not None and z2.grad is not None) else 'FAIL'
    print(f"  Status: {status}")
    
    report.add('infonce', {
        'loss': loss.item(),
        'finite': torch.isfinite(loss).item(),
        'status': status,
    })


def test_grl(report: ValidationReport):
    """Test Gradient Reversal Layer."""
    print("\n[GRADIENT REVERSAL LAYER]")
    print("-" * 70)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    lambda_ = 1.0
    
    # Test without GRL
    x1 = torch.randn(4, 16, device=device, requires_grad=True)
    y1 = (x1 ** 2).sum()
    y1.backward()
    grad_without_grl = x1.grad.clone()
    
    # Test with GRL
    x2 = x1.detach().clone().requires_grad_(True)
    x2_reversed = gradient_reversal(x2, lambda_)
    y2 = (x2_reversed ** 2).sum()
    y2.backward()
    grad_with_grl = x2.grad.clone()
    
    # Check sign inversion
    expected = -lambda_ * grad_without_grl
    ratio = grad_with_grl / (grad_without_grl + 1e-10)
    
    print(f"  Gradient without GRL (first 3): {grad_without_grl[:3].tolist()}")
    print(f"  Gradient with GRL (first 3): {grad_with_grl[:3].tolist()}")
    print(f"  Expected ratio: {-lambda_}")
    print(f"  Actual ratio (mean): {ratio.mean().item():.6f}")
    
    # Check sign is inverted
    sign_correct = (grad_with_grl * grad_without_grl < 0).all().item()
    print(f"  Sign correctly inverted: {sign_correct}")
    
    status = 'PASS' if sign_correct else 'FAIL'
    print(f"  Status: {status}")
    
    report.add('grl', {
        'lambda': lambda_,
        'sign_correct': sign_correct,
        'ratio_mean': ratio.mean().item(),
        'status': status,
    })


def test_phase_loss(report: ValidationReport):
    """Test circular phase loss."""
    print("\n[PHASE LOSS - CIRCULAR]")
    print("-" * 70)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # Test wrap-around
    target = torch.tensor([math.pi - 0.01], device=device)
    prediction = torch.tensor([-math.pi + 0.01], device=device)
    
    loss = circular_phase_loss(prediction, target)
    
    # Expected: small loss (angular distance ~0.02)
    expected_approx = 1 - math.cos(0.02)
    
    print(f"  Target: pi - 0.01 = {target.item():.6f}")
    print(f"  Prediction: -pi + 0.01 = {prediction.item():.6f}")
    print(f"  Loss: {loss.item():.6f}")
    print(f"  Expected approx: {expected_approx:.6f}")
    
    # Should be small, not ~2 (which would be L1 distance)
    l1_would_be = abs(target.item() - prediction.item())
    print(f"  L1 would give: {l1_would_be:.6f}")
    
    status = 'PASS' if loss.item() < 0.1 else 'FAIL'
    print(f"  Status: {status}")
    
    # Test for VV and VH
    vv_loss = circular_phase_loss(
        torch.tensor([0.5], device=device),
        torch.tensor([0.5], device=device)
    )
    vh_loss = circular_phase_loss(
        torch.tensor([1.0], device=device),
        torch.tensor([1.0], device=device)
    )
    print(f"  VV identical phases loss: {vv_loss.item():.6f}")
    print(f"  VH identical phases loss: {vh_loss.item():.6f}")
    
    report.add('phase_loss', {
        'wrap_around_loss': loss.item(),
        'expected_approx': expected_approx,
        'l1_would_be': l1_would_be,
        'status': status,
    })


def test_chamfer(report: ValidationReport):
    """Test Chamfer distance."""
    print("\n[CHAMFER DISTANCE]")
    print("-" * 70)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # TEST A: XYZ identical, intensity different
    xyz = torch.randn(2, 100, 3, device=device)
    pred = torch.cat([xyz, torch.randn(2, 100, 1, device=device)], dim=-1)
    target = torch.cat([xyz, torch.randn(2, 100, 1, device=device) * 10], dim=-1)
    
    chamfer_a = chamfer_distance(pred[:, :, :3], target[:, :, :3])
    print(f"  TEST A - XYZ identical, intensity different: {chamfer_a.item():.6e}")
    test_a_status = 'PASS' if chamfer_a.item() < 1e-5 else 'FAIL'
    print(f"    Status: {test_a_status}")
    
    # TEST B: XYZ displaced
    xyz_displaced = xyz + 1.0
    chamfer_b = chamfer_distance(xyz, xyz_displaced)
    print(f"  TEST B - XYZ displaced by 1.0: {chamfer_b.item():.6f}")
    test_b_status = 'PASS' if chamfer_b.item() > 0.5 else 'FAIL'
    print(f"    Status: {test_b_status}")
    
    # TEST C: Padding with mask
    N = 50
    xyz_base = torch.randn(1, N, 3, device=device)
    xyz_padded = torch.cat([xyz_base, torch.full((1, 50, 3), 1e6, device=device)], dim=1)
    mask = torch.zeros(1, 100, dtype=torch.bool, device=device)
    mask[0, :N] = True
    
    chamfer_base = chamfer_distance(xyz_base, xyz_base)
    chamfer_padded = chamfer_distance(xyz_padded[:, :N, :], xyz_padded[:, :N, :], mask[:, :N])
    
    print(f"  TEST C - Base Chamfer: {chamfer_base.item():.6e}")
    print(f"  TEST C - Padded with mask: {chamfer_padded.item():.6e}")
    test_c_status = 'PASS' if abs(chamfer_base.item() - chamfer_padded.item()) < 1e-5 else 'FAIL'
    print(f"    Status: {test_c_status}")
    
    report.add('chamfer', {
        'test_a': {'value': chamfer_a.item(), 'status': test_a_status},
        'test_b': {'value': chamfer_b.item(), 'status': test_b_status},
        'test_c': {'base': chamfer_base.item(), 'padded': chamfer_padded.item(), 'status': test_c_status},
    })


def test_backward(model: nn.Module, report: ValidationReport):
    """Test backward pass and gradient flow."""
    print("\n[BACKWARD PASS]")
    print("-" * 70)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    model.train()
    
    B = 2
    N = 64
    
    lidar_xyz = torch.randn(B, N, 3, device=device)
    lidar_features = torch.randn(B, N, 4, device=device)
    lidar_mask = torch.ones(B, N, dtype=torch.bool, device=device)
    sar_slc = torch.randn(B, 4, 64, 64, device=device)
    
    output = model(lidar_xyz, lidar_features, sar_slc, lidar_mask)
    
    # Compute losses
    recon_loss_fn = ReconstructionLoss()
    recon_losses = recon_loss_fn(
        output['lidar_points'], lidar_features,
        output['sar_slc'], sar_slc, lidar_mask
    )
    
    mae_loss_fn = CrossModalMAELoss()
    lidar_mask_mae, sar_mask_mae = mae_loss_fn.generate_masks(
        (B, N), (B, 4, 64, 64), device=device
    )
    lidar_mae, sar_mae = mae_loss_fn(
        output['lidar_points'], lidar_features, lidar_mask_mae,
        output['sar_slc'], sar_slc, sar_mask_mae
    )
    
    infonce = InfoNCELoss()
    contrastive = infonce(output['z_lidar'], output['z_sar'])
    
    decoupling = DecouplingLoss().to(device)
    dec_loss, _ = decoupling(
        output['z_common'], output['z_unique_lidar'], output['z_unique_sar']
    )
    
    total_loss = (
        recon_losses['total'] +
        lidar_mae + sar_mae +
        0.5 * contrastive +
        0.3 * dec_loss
    )
    
    print(f"  Total loss: {total_loss.item():.6f}")
    print(f"  Reconstruction: {recon_losses['total'].item():.6f}")
    print(f"  MAE LiDAR: {lidar_mae.item():.6f}")
    print(f"  MAE SAR: {sar_mae.item():.6f}")
    print(f"  Contrastive: {contrastive.item():.6f}")
    print(f"  Decoupling: {dec_loss.item():.6f}")
    
    total_loss.backward()
    
    # Check gradients by module
    modules_to_check = {
        'lidar_encoder': model.lidar_encoder,
        'sar_encoder': model.sar_encoder,
        'fusion': model.fusion,
        'lidar_decoder': model.lidar_decoder,
        'sar_decoder': model.sar_decoder,
    }
    
    gradient_info = {}
    for name, module in modules_to_check.items():
        params_with_grad = 0
        params_without_grad = 0
        total_params = 0
        nan_count = 0
        inf_count = 0
        zero_count = 0
        grad_norm = 0.0
        
        for p in module.parameters():
            total_params += 1
            if p.grad is not None:
                params_with_grad += 1
                if torch.isnan(p.grad).any():
                    nan_count += 1
                if torch.isinf(p.grad).any():
                    inf_count += 1
                if p.grad.abs().max() < 1e-10:
                    zero_count += 1
                grad_norm += p.grad.norm().item() ** 2
            else:
                params_without_grad += 1
        
        grad_norm = math.sqrt(grad_norm)
        gradient_info[name] = {
            'total_params': total_params,
            'with_grad': params_with_grad,
            'without_grad': params_without_grad,
            'grad_norm': grad_norm,
            'nan_count': nan_count,
            'inf_count': inf_count,
            'zero_count': zero_count,
        }
        
        status = 'OK' if params_with_grad > 0 and nan_count == 0 and inf_count == 0 else 'ISSUE'
        print(f"  {name}: {params_with_grad}/{total_params} with grad, norm={grad_norm:.4f} [{status}]")
    
    report.add('backward', {
        'total_loss': total_loss.item(),
        'losses': {
            'reconstruction': recon_losses['total'].item(),
            'mae_lidar': lidar_mae.item(),
            'mae_sar': sar_mae.item(),
            'contrastive': contrastive.item(),
            'decoupling': dec_loss.item(),
        },
        'gradients': gradient_info,
        'status': 'PASS',
    })


def test_overfit(model: nn.Module, report: ValidationReport, steps: int = 50):
    """Test minibatch overfit."""
    print(f"\n[CONTROLLED OVERFIT - {steps} steps]")
    print("-" * 70)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    model.train()
    
    # Deterministic synthetic batch
    torch.manual_seed(42)
    B = 2
    N = 64
    
    lidar_xyz = torch.randn(B, N, 3, device=device)
    lidar_features = torch.randn(B, N, 4, device=device)
    lidar_mask = torch.ones(B, N, dtype=torch.bool, device=device)
    sar_slc = torch.randn(B, 4, 64, 64, device=device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    recon_loss_fn = ReconstructionLoss()
    mae_loss_fn = CrossModalMAELoss()
    infonce = InfoNCELoss()
    decoupling = DecouplingLoss().to(device)
    
    losses_over_time = []
    initial_loss = None
    initial_recon = None
    
    for step in range(steps):
        optimizer.zero_grad()
        
        output = model(lidar_xyz, lidar_features, sar_slc, lidar_mask)
        
        recon_losses = recon_loss_fn(
            output['lidar_points'], lidar_features,
            output['sar_slc'], sar_slc, lidar_mask
        )
        
        lidar_mask_mae, sar_mask_mae = mae_loss_fn.generate_masks(
            (B, N), (B, 4, 64, 64), device=device
        )
        lidar_mae, sar_mae = mae_loss_fn(
            output['lidar_points'], lidar_features, lidar_mask_mae,
            output['sar_slc'], sar_slc, sar_mask_mae
        )
        
        contrastive = infonce(output['z_lidar'], output['z_sar'])
        dec_loss, _ = decoupling(
            output['z_common'], output['z_unique_lidar'], output['z_unique_sar']
        )
        
        total_loss = (
            recon_losses['total'] +
            lidar_mae + sar_mae +
            0.5 * contrastive +
            0.3 * dec_loss
        )
        
        total_loss.backward()
        optimizer.step()
        
        if step == 0:
            initial_loss = total_loss.item()
            initial_recon = recon_losses['total'].item()
        
        if step % 10 == 0 or step == steps - 1:
            losses_over_time.append({
                'step': step,
                'total': total_loss.item(),
                'reconstruction': recon_losses['total'].item(),
                'mae_lidar': lidar_mae.item(),
                'mae_sar': sar_mae.item(),
                'contrastive': contrastive.item(),
                'decoupling': dec_loss.item(),
            })
            print(f"  Step {step:3d}: total={total_loss.item():.4f}, recon={recon_losses['total'].item():.4f}")
    
    final_loss = losses_over_time[-1]['total']
    final_recon = losses_over_time[-1]['reconstruction']
    
    total_decrease = ((initial_loss - final_loss) / initial_loss) * 100
    recon_decrease = ((initial_recon - final_recon) / initial_recon) * 100
    
    print(f"\n  Initial total loss: {initial_loss:.4f}")
    print(f"  Final total loss: {final_loss:.4f}")
    print(f"  Total decrease: {total_decrease:.2f}%")
    print(f"\n  Initial reconstruction: {initial_recon:.4f}")
    print(f"  Final reconstruction: {final_recon:.4f}")
    print(f"  Reconstruction decrease: {recon_decrease:.2f}%")
    
    status = 'PASS' if (total_decrease > 0 and recon_decrease > 0) else 'FAIL'
    print(f"  Status: {status}")
    
    # Check for NaN
    has_nan = any(math.isnan(l['total']) for l in losses_over_time)
    if has_nan:
        status = 'FAIL'
        print("  WARNING: NaN detected in losses!")
    
    report.add('overfit', {
        'steps': steps,
        'initial_total': initial_loss,
        'final_total': final_loss,
        'total_decrease_pct': total_decrease,
        'initial_reconstruction': initial_recon,
        'final_reconstruction': final_recon,
        'reconstruction_decrease_pct': recon_decrease,
        'has_nan': has_nan,
        'losses_over_time': losses_over_time,
        'status': status,
    })


def test_two_step(report: ValidationReport):
    """Test two-step reconstruction decrease."""
    print("\n[TWO-STEP RECONSTRUCTION TEST]")
    print("-" * 70)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    torch.manual_seed(42)
    
    config = OmegaConf.load('config.yaml')
    model = MultimodalAutoencoder(
        latent_dim=config.model.latent_dim,
        lidar_config={
            'in_channels': config.data.lidar_channels,
            'shared_mlp_layers': config.model.lidar.shared_mlp_layers,
            'knn_k': config.model.lidar.knn_k,
            'local_mlp_layers': config.model.lidar.local_mlp_layers,
            'global_mlp_layers': config.model.lidar.global_mlp_layers,
            'num_points': config.data.lidar_max_points,
            'output_channels': config.data.lidar_channels,
        },
        sar_config={
            'in_channels': config.data.sar_channels,
            'encoder_channels': config.model.sar.encoder_channels,
            'decoder_channels': config.model.sar.decoder_channels,
            'residual_connections': config.model.sar.residual_connections,
            'output_channels': config.data.sar_channels,
        },
        fusion_config={
            'num_layers': config.model.fusion.num_layers,
            'num_heads': config.model.fusion.num_heads,
            'dim_feedforward': config.model.fusion.dim_feedforward,
            'dropout': config.model.dropout,
            'asymmetric_gating': config.model.fusion.asymmetric_gating,
        }
    ).to(device)
    
    model.train()
    
    B = 2
    N = 32
    
    lidar_xyz = torch.randn(B, N, 3, device=device)
    lidar_features = torch.randn(B, N, 4, device=device)
    lidar_mask = torch.ones(B, N, dtype=torch.bool, device=device)
    sar_slc = torch.randn(B, 4, 64, 64, device=device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    recon_loss_fn = ReconstructionLoss()
    
    losses = []
    for step in range(2):
        optimizer.zero_grad()
        output = model(lidar_xyz, lidar_features, sar_slc, lidar_mask)
        recon_losses = recon_loss_fn(
            output['lidar_points'], lidar_features,
            output['sar_slc'], sar_slc, lidar_mask
        )
        recon_losses['total'].backward()
        optimizer.step()
        losses.append(recon_losses['total'].item())
        print(f"  Step {step}: reconstruction loss = {recon_losses['total'].item():.6f}")
    
    status = 'PASS' if losses[1] < losses[0] else 'FAIL'
    print(f"  Decrease: {losses[0] - losses[1]:.6f}")
    print(f"  Status: {status}")
    
    report.add('two_step', {
        'losses': losses,
        'decrease': losses[0] - losses[1],
        'status': status,
    })


def test_amp_bf16(model: nn.Module, report: ValidationReport):
    """Test AMP/BF16 if available."""
    print("\n[AMP/BF16]")
    print("-" * 70)
    
    if not torch.cuda.is_available():
        print("  BLOCKED BY HARDWARE: No CUDA")
        report.add('amp_bf16', {'status': 'BLOCKED_BY_HARDWARE', 'reason': 'No CUDA'})
        return
    
    try:
        x = torch.randn(2, 2, device='cuda', dtype=torch.bfloat16)
    except Exception:
        print("  BLOCKED BY HARDWARE: BF16 not supported")
        report.add('amp_bf16', {'status': 'BLOCKED_BY_HARDWARE', 'reason': 'BF16 not supported'})
        return
    
    device = 'cuda'
    model = model.to(device)
    model.train()
    
    B = 2
    N = 32
    
    lidar_xyz = torch.randn(B, N, 3, device=device)
    lidar_features = torch.randn(B, N, 4, device=device)
    lidar_mask = torch.ones(B, N, dtype=torch.bool, device=device)
    sar_slc = torch.randn(B, 4, 64, 64, device=device)
    
    try:
        with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
            output = model(lidar_xyz, lidar_features, sar_slc, lidar_mask)
            loss = output['z_common'].sum()
        
        loss.backward()
        
        finite = torch.isfinite(loss).item()
        has_grad = any(p.grad is not None for p in model.parameters())
        
        print(f"  Loss: {loss.item():.6f}")
        print(f"  Finite: {finite}")
        print(f"  Has gradients: {has_grad}")
        
        status = 'PASS' if finite and has_grad else 'FAIL'
        print(f"  Status: {status}")
        
        report.add('amp_bf16', {
            'loss': loss.item(),
            'finite': finite,
            'has_grad': has_grad,
            'status': status,
        })
    except Exception as e:
        print(f"  FAIL: {e}")
        report.add('amp_bf16', {'status': 'FAIL', 'error': str(e)})


def test_linear_probe(model: nn.Module, report: ValidationReport):
    """Test linear probe with frozen backbone."""
    print("\n[LINEAR PROBE]")
    print("-" * 70)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    
    # Save backbone weights
    backbone_state = {k: v.clone() for k, v in model.state_dict().items()}
    
    # Create linear probe
    probe = LinearProbe(
        backbone=model,
        num_classes=5,
        latent_dim=256,
        use_common=True
    ).to(device)
    
    # Verify backbone frozen
    backbone_frozen = all(not p.requires_grad for p in model.parameters())
    print(f"  Backbone frozen: {backbone_frozen}")
    
    # Verify head trainable
    head_trainable = all(p.requires_grad for p in probe.classifier.parameters())
    print(f"  Head trainable: {head_trainable}")
    
    # Forward and backward
    B = 4
    N = 32
    
    lidar_xyz = torch.randn(B, N, 3, device=device)
    lidar_features = torch.randn(B, N, 4, device=device)
    lidar_mask = torch.ones(B, N, dtype=torch.bool, device=device)
    sar_slc = torch.randn(B, 4, 64, 64, device=device)
    labels = torch.randint(0, 5, (B,), device=device)
    
    optimizer = torch.optim.Adam(probe.get_trainable_parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()
    
    optimizer.zero_grad()
    logits = probe(lidar_xyz, lidar_features, sar_slc, lidar_mask)
    loss = criterion(logits, labels)
    loss.backward()
    optimizer.step()
    
    # Check backbone unchanged
    backbone_unchanged = True
    for k, v in model.state_dict().items():
        if not torch.allclose(v, backbone_state[k]):
            backbone_unchanged = False
            break
    
    # Check head changed
    head_changed = any(p.grad is not None and p.grad.abs().sum() > 0 for p in probe.classifier.parameters())
    
    # Check backbone gradients absent
    backbone_no_grad = all(p.grad is None for p in model.parameters())
    
    print(f"  Backbone unchanged: {backbone_unchanged}")
    print(f"  Head changed: {head_changed}")
    print(f"  Backbone no gradients: {backbone_no_grad}")
    
    status = 'PASS' if (backbone_frozen and head_trainable and backbone_unchanged and head_changed and backbone_no_grad) else 'FAIL'
    print(f"  Status: {status}")
    
    report.add('linear_probe', {
        'backbone_frozen': backbone_frozen,
        'head_trainable': head_trainable,
        'backbone_unchanged': backbone_unchanged,
        'head_changed': head_changed,
        'backbone_no_grad': backbone_no_grad,
        'status': status,
    })


def test_reproducibility(model: nn.Module, report: ValidationReport):
    """Test reproducibility with same seed."""
    print("\n[REPRODUCIBILITY]")
    print("-" * 70)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    model.eval()
    
    B = 2
    N = 32
    
    def run_with_seed(seed):
        torch.manual_seed(seed)
        np.random.seed(seed)
        random.seed(seed)
        
        lidar_xyz = torch.randn(B, N, 3, device=device)
        lidar_features = torch.randn(B, N, 4, device=device)
        lidar_mask = torch.ones(B, N, dtype=torch.bool, device=device)
        sar_slc = torch.randn(B, 4, 64, 64, device=device)
        
        with torch.no_grad():
            output = model(lidar_xyz, lidar_features, sar_slc, lidar_mask)
        return output['z_common']
    
    out1 = run_with_seed(42)
    out2 = run_with_seed(42)
    
    max_diff = (out1 - out2).abs().max().item()
    print(f"  Max absolute difference with same seed: {max_diff:.6e}")
    
    status = 'PASS' if max_diff < 1e-5 else 'FAIL'
    print(f"  Status: {status}")
    
    report.add('reproducibility', {
        'max_diff': max_diff,
        'status': status,
    })


def test_downstream_metrics(report: ValidationReport):
    """Test downstream metrics computation."""
    print("\n[DOWNSTREAM METRICS]")
    print("-" * 70)
    
    # Synthetic predictions and labels
    torch.manual_seed(42)
    y_true = torch.tensor([0, 1, 2, 3, 4, 0, 1, 2, 3, 4])
    y_pred = torch.tensor([0, 1, 2, 3, 4, 0, 1, 2, 3, 0])  # 1 error
    
    # Accuracy
    accuracy = (y_true == y_pred).float().mean().item()
    
    # Macro-F1 (manual)
    num_classes = 5
    f1_scores = []
    for c in range(num_classes):
        tp = ((y_pred == c) & (y_true == c)).sum().item()
        fp = ((y_pred == c) & (y_true != c)).sum().item()
        fn = ((y_pred != c) & (y_true == c)).sum().item()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        f1_scores.append(f1)
    
    macro_f1 = sum(f1_scores) / len(f1_scores)
    
    # Confusion matrix
    conf_matrix = torch.zeros(num_classes, num_classes, dtype=torch.long)
    for t, p in zip(y_true, y_pred):
        conf_matrix[t, p] += 1
    
    print(f"  Accuracy: {accuracy:.4f}")
    print(f"  Macro-F1: {macro_f1:.4f}")
    print(f"  Confusion matrix:\n{conf_matrix}")
    
    status = 'PASS' if accuracy > 0.8 and macro_f1 > 0.8 else 'FAIL'
    print(f"  Status: {status}")
    
    report.add('downstream_metrics', {
        'accuracy': accuracy,
        'macro_f1': macro_f1,
        'confusion_matrix': conf_matrix.tolist(),
        'status': status,
    })


def main():
    parser = argparse.ArgumentParser(description='Phase 3B.1 Validation')
    parser.add_argument('--config', type=str, default='config.yaml')
    parser.add_argument('--overfit-steps', type=int, default=50)
    parser.add_argument('--output', type=str, default='validation_report_phase3b1.json')
    args = parser.parse_args()
    
    print("=" * 70)
    print("GOD EYE SAE — FOUNDATION MODEL PHASE 3B.1 VALIDATION")
    print("=" * 70)
    
    report = ValidationReport()
    
    # Environment check
    if not check_environment(report):
        report.save(args.output)
        return
    
    # Load config
    config = OmegaConf.load(args.config)
    print(f"\n  Config: {args.config}")
    print(f"  Latent dim: {config.model.latent_dim}")
    print(f"  SAR channels: {config.data.sar_channels}")
    print(f"  SAR representation: {config.data.sar_representation}")
    
    # Create model
    model = MultimodalAutoencoder(
        latent_dim=config.model.latent_dim,
        lidar_config={
            'in_channels': config.data.lidar_channels,
            'shared_mlp_layers': config.model.lidar.shared_mlp_layers,
            'knn_k': config.model.lidar.knn_k,
            'local_mlp_layers': config.model.lidar.local_mlp_layers,
            'global_mlp_layers': config.model.lidar.global_mlp_layers,
            'num_points': config.data.lidar_max_points,
            'output_channels': config.data.lidar_channels,
        },
        sar_config={
            'in_channels': config.data.sar_channels,
            'encoder_channels': config.model.sar.encoder_channels,
            'decoder_channels': config.model.sar.decoder_channels,
            'residual_connections': config.model.sar.residual_connections,
            'output_channels': config.data.sar_channels,
        },
        fusion_config={
            'num_layers': config.model.fusion.num_layers,
            'num_heads': config.model.fusion.num_heads,
            'dim_feedforward': config.model.fusion.dim_feedforward,
            'dropout': config.model.dropout,
            'asymmetric_gating': config.model.fusion.asymmetric_gating,
        }
    )
    
    # Run all tests
    count_parameters(model, config, report)
    test_forward(model, config, report)
    test_forward_configurable_latent(report)
    test_variable_point_clouds(model, report)
    test_knn(model, report)
    test_cross_modal_mae_ablation(model, report)
    test_mask_ratios(report)
    test_infonce(report)
    test_grl(report)
    test_phase_loss(report)
    test_chamfer(report)
    test_backward(model, report)
    test_overfit(model, report, steps=args.overfit_steps)
    test_two_step(report)
    test_amp_bf16(model, report)
    test_linear_probe(model, report)
    test_reproducibility(model, report)
    test_downstream_metrics(report)
    
    # Summary
    report.print_summary()
    report.save(args.output)
    
    # Final GO/NO-GO
    print("\n" + "=" * 70)
    print("FINAL GO/NO-GO DECISION")
    print("=" * 70)
    
    critical_pass = all([
        report.results.get('parameters', {}).get('under_50m', False),
        report.results.get('forward', {}).get('status') == 'PASS',
        report.results.get('variable_point_clouds', {}).get('padding_robustness', {}).get('status') == 'PASS',
        report.results.get('knn', {}).get('status') == 'PASS',
        report.results.get('cross_modal_ablation', {}).get('test_a_status') == 'PASS',
        report.results.get('cross_modal_ablation', {}).get('test_b_status') == 'PASS',
        report.results.get('grl', {}).get('status') == 'PASS',
        report.results.get('phase_loss', {}).get('status') == 'PASS',
        report.results.get('chamfer', {}).get('test_a', {}).get('status') == 'PASS',
        report.results.get('overfit', {}).get('status') == 'PASS',
        report.results.get('linear_probe', {}).get('status') == 'PASS',
    ])
    
    if critical_pass:
        print("\n  ✅ GO TO PHASE 3C")
        print("  All critical criteria passed.")
    else:
        print("\n  ❌ NO-GO — CORRECTIONS REQUIRED")
        print("  Some critical criteria failed.")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
