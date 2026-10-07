"""
WandB logging utilities.
"""

import torch
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class WandBLogger:
    """WandB logging wrapper."""
    
    def __init__(
        self,
        project: str,
        entity: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        rank: int = 0
    ) -> None:
        """
        Args:
            project: WandB project name
            entity: WandB entity (username/team)
            config: Configuration dictionary
            rank: Process rank (only rank 0 logs)
        """
        self.rank = rank
        self.enabled = rank == 0
        
        if self.enabled:
            try:
                import wandb
                wandb.init(
                    project=project,
                    entity=entity,
                    config=config
                )
                self.wandb = wandb
                logger.info(f"WandB initialized: project={project}")
            except ImportError:
                logger.warning("WandB not available, logging disabled")
                self.enabled = False
    
    def log(self, metrics: Dict[str, Any], step: Optional[int] = None) -> None:
        """Log metrics to WandB."""
        if self.enabled:
            self.wandb.log(metrics, step=step)
    
    def log_gradients(self, model: torch.nn.Module, step: int) -> None:
        """Log gradient norms."""
        if not self.enabled:
            return
        
        grad_norms = {}
        for name, param in model.named_parameters():
            if param.grad is not None:
                grad_norms[f"grad_norm/{name}"] = param.grad.norm().item()
        
        if grad_norms:
            self.log(grad_norms, step=step)
    
    def finish(self) -> None:
        """Finish WandB run."""
        if self.enabled:
            self.wandb.finish()
