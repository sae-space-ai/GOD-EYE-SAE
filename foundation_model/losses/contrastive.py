"""
Contrastive Loss - InfoNCE for self-supervised alignment.

SimCLR-style contrastive learning with augmented views.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import logging

logger = logging.getLogger(__name__)


class InfoNCELoss(nn.Module):
    """
    InfoNCE contrastive loss for aligning augmented views.
    
    Temperature-scaled cosine similarity with cross-entropy.
    """
    
    def __init__(self, temperature: float = 0.07) -> None:
        """
        Args:
            temperature: Temperature scaling parameter (tau)
        """
        super().__init__()
        self.temperature = temperature
        
        logger.info(f"InfoNCE loss initialized: temperature={temperature}")
    
    def forward(
        self,
        z1: torch.Tensor,
        z2: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute InfoNCE loss between two augmented views.
        
        Args:
            z1: (B, D) first view representations
            z2: (B, D) second view representations
            
        Returns:
            loss: scalar contrastive loss
        """
        B = z1.shape[0]
        
        # Normalize
        z1 = F.normalize(z1, dim=1)
        z2 = F.normalize(z2, dim=1)
        
        # Concatenate
        representations = torch.cat([z1, z2], dim=0)  # (2B, D)
        
        # Similarity matrix
        similarity_matrix = F.cosine_similarity(
            representations.unsqueeze(1),
            representations.unsqueeze(0),
            dim=2
        ) / self.temperature  # (2B, 2B)
        
        # Positive pairs: (i, i+B) and (i+B, i)
        pos_mask = torch.zeros(2 * B, 2 * B, dtype=torch.bool, device=z1.device)
        for i in range(B):
            pos_mask[i, i + B] = True
            pos_mask[i + B, i] = True
        
        # Extract positive similarities
        pos_sim = similarity_matrix[pos_mask].view(2 * B, 1)
        
        # Extract negative similarities (exclude diagonal and positives)
        neg_mask = ~torch.eye(2 * B, dtype=torch.bool, device=z1.device) & ~pos_mask
        neg_sim = similarity_matrix[neg_mask].view(2 * B, -1)
        
        # Concatenate positives and negatives
        logits = torch.cat([pos_sim, neg_sim], dim=1)  # (2B, 1 + 2B-2)
        
        # Labels: positives are at index 0
        labels = torch.zeros(2 * B, dtype=torch.long, device=z1.device)
        
        # Cross-entropy loss
        loss = F.cross_entropy(logits, labels)
        
        return loss
