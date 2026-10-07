"""
SAR Polarization Utilities.

Differentiable conversions between dual-pol SLC (real/imag) and
amplitude/phase representations.

Convention:
  Channel 0: VV real
  Channel 1: VV imaginary
  Channel 2: VH real
  Channel 3: VH imaginary
"""

import torch
import torch.nn.functional as F
from typing import Tuple
import math
import logging

logger = logging.getLogger(__name__)


def complex_to_amp_phase(
    real: torch.Tensor,
    imag: torch.Tensor,
    eps: float = 1e-8
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Convert complex (real, imag) to (amplitude, phase).

    amplitude = sqrt(real^2 + imag^2 + eps)   [differentiable]
    phase     = atan2(imag, real)              [differentiable, range (-pi, pi]]

    Args:
        real: Tensor of real parts (any shape)
        imag: Tensor of imaginary parts (same shape as real)
        eps: Small constant for numerical stability in sqrt

    Returns:
        amplitude: Tensor of same shape as real, >= 0
        phase: Tensor of same shape as real, in (-pi, pi]
    """
    amplitude = torch.sqrt(real * real + imag * imag + eps)
    phase = torch.atan2(imag, real)
    return amplitude, phase


def amp_phase_to_complex(
    amplitude: torch.Tensor,
    phase: torch.Tensor
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Convert (amplitude, phase) back to (real, imag).

    real = amplitude * cos(phase)
    imag = amplitude * sin(phase)

    Args:
        amplitude: Non-negative tensor
        phase: Phase tensor in (-pi, pi]

    Returns:
        real, imag: Tensors of same shape as inputs
    """
    real = amplitude * torch.cos(phase)
    imag = amplitude * torch.sin(phase)
    return real, imag


def split_dual_pol(
    slc: torch.Tensor
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Split 4-channel dual-pol SLC into VV and VH complex components.

    Args:
        slc: (B, 4, H, W) tensor with channels [VV_real, VV_imag, VH_real, VH_imag]

    Returns:
        vv_real, vv_imag, vh_real, vh_imag: Each (B, 1, H, W)
    """
    if slc.shape[1] != 4:
        raise ValueError(f"Expected 4 channels for dual-pol SLC, got {slc.shape[1]}")

    vv_real = slc[:, 0:1, :, :]
    vv_imag = slc[:, 1:2, :, :]
    vh_real = slc[:, 2:3, :, :]
    vh_imag = slc[:, 3:4, :, :]
    return vv_real, vv_imag, vh_real, vh_imag


def dual_pol_to_amp_phase(
    slc: torch.Tensor,
    eps: float = 1e-8
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Convert 4-channel dual-pol SLC to amplitude/phase per polarization.

    Args:
        slc: (B, 4, H, W) tensor [VV_real, VV_imag, VH_real, VH_imag]
        eps: Numerical stability constant

    Returns:
        vv_amp, vv_phase, vh_amp, vh_phase: Each (B, 1, H, W)
    """
    vv_real, vv_imag, vh_real, vh_imag = split_dual_pol(slc)
    vv_amp, vv_phase = complex_to_amp_phase(vv_real, vv_imag, eps)
    vh_amp, vh_phase = complex_to_amp_phase(vh_real, vh_imag, eps)
    return vv_amp, vv_phase, vh_amp, vh_phase


def circular_phase_loss(
    pred_phase: torch.Tensor,
    target_phase: torch.Tensor
) -> torch.Tensor:
    """
    Circular (wrap-around aware) phase loss.

    Uses the chordal distance formulation:
        loss = mean(1 - cos(pred - target))

    This correctly handles wrap-around at ±pi. For example:
        target = pi - 0.01
        pred   = -pi + 0.01
    The angular distance is ~0.02, and loss ≈ 1 - cos(0.02) ≈ 0.0002 (small).

    Args:
        pred_phase: Predicted phase tensor (radians)
        target_phase: Target phase tensor (radians)

    Returns:
        Scalar loss in range [0, 2]
    """
    delta = pred_phase - target_phase
    return 1.0 - torch.cos(delta).mean()


def dual_pol_reconstruction_loss(
    pred_slc: torch.Tensor,
    target_slc: torch.Tensor,
    lambda_amp: float = 1.0,
    lambda_phase: float = 0.5,
    eps: float = 1e-8
) -> dict:
    """
    Compute reconstruction loss for 4-channel dual-pol SLC.

    Computes L1 on amplitudes and circular phase loss for both VV and VH.

    Args:
        pred_slc: (B, 4, H, W) predicted SLC
        target_slc: (B, 4, H, W) target SLC
        lambda_amp: Weight for amplitude L1
        lambda_phase: Weight for phase angular loss
        eps: Numerical stability constant

    Returns:
        Dictionary with:
            vv_amp_loss, vv_phase_loss, vh_amp_loss, vh_phase_loss, total
    """
    pred_vv_amp, pred_vv_phase, pred_vh_amp, pred_vh_phase = dual_pol_to_amp_phase(pred_slc, eps)
    tgt_vv_amp, tgt_vv_phase, tgt_vh_amp, tgt_vh_phase = dual_pol_to_amp_phase(target_slc, eps)

    vv_amp_loss = F.l1_loss(pred_vv_amp, tgt_vv_amp)
    vv_phase_loss = circular_phase_loss(pred_vv_phase, tgt_vv_phase)
    vh_amp_loss = F.l1_loss(pred_vh_amp, tgt_vh_amp)
    vh_phase_loss = circular_phase_loss(pred_vh_phase, tgt_vh_phase)

    total = (
        lambda_amp * (vv_amp_loss + vh_amp_loss) +
        lambda_phase * (vv_phase_loss + vh_phase_loss)
    )

    return {
        'vv_amplitude': vv_amp_loss,
        'vv_phase': vv_phase_loss,
        'vh_amplitude': vh_amp_loss,
        'vh_phase': vh_phase_loss,
        'total': total,
    }
