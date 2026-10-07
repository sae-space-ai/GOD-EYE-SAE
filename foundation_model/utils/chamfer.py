"""
Differentiable Chamfer distance implementation.
"""

import torch


def chamfer_distance(
    pred: torch.Tensor,
    target: torch.Tensor,
    mask: torch.Tensor | None = None
) -> torch.Tensor:
    """
    Compute Chamfer distance between two point clouds.
    
    Args:
        pred: (B, N, 3) predicted points
        target: (B, M, 3) target points
        mask: (B, M) optional mask for target
        
    Returns:
        Scalar Chamfer distance
    """
    # Pairwise distances
    dist = torch.cdist(pred, target)  # (B, N, M)
    
    # Min distances
    min_dist_pred, _ = dist.min(dim=2)  # (B, N)
    min_dist_target, _ = dist.min(dim=1)  # (B, M)
    
    if mask is not None:
        min_dist_target = min_dist_target * mask.float()
        chamfer = min_dist_pred.mean() + (min_dist_target * mask.float()).sum() / (mask.sum() + 1e-8)
    else:
        chamfer = min_dist_pred.mean() + min_dist_target.mean()
    
    return chamfer
