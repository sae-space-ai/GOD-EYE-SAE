"""
Distributed Data Parallel (DDP) setup utilities.
"""

import os
import torch
import torch.distributed as dist
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def setup_ddp(backend: str = "nccl") -> tuple[int, int, int]:
    """
    Initialize DDP environment.
    
    Args:
        backend: Communication backend (nccl for GPU, gloo for CPU)
        
    Returns:
        rank, local_rank, world_size
    """
    rank = int(os.environ.get("RANK", 0))
    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    world_size = int(os.environ.get("WORLD_SIZE", 1))
    
    if world_size > 1:
        dist.init_process_group(backend=backend, rank=rank, world_size=world_size)
        torch.cuda.set_device(local_rank)
        logger.info(f"DDP initialized: rank={rank}, local_rank={local_rank}, world_size={world_size}")
    
    return rank, local_rank, world_size


def cleanup_ddp() -> None:
    """Cleanup DDP environment."""
    if dist.is_initialized():
        dist.destroy_process_group()
        logger.info("DDP cleaned up")
