"""
Loss functions package for multimodal autoencoder training.
"""

from .mae_loss import CrossModalMAELoss
from .contrastive import InfoNCELoss
from .decoupling import DecouplingLoss
from .reconstruction import ReconstructionLoss

__all__ = [
    'CrossModalMAELoss',
    'InfoNCELoss',
    'DecouplingLoss',
    'ReconstructionLoss'
]
