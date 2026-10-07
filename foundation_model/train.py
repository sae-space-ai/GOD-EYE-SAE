"""
Main training script for LiDAR-SAR foundation model.

Supports DDP, AMP, WandB logging, and gradient accumulation.
"""

import os
import sys
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.nn.parallel import DistributedDataParallel as DDP
from omegaconf import OmegaConf
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import MultimodalAutoencoder
from losses import CrossModalMAELoss, InfoNCELoss, DecouplingLoss, ReconstructionLoss
from data import LiDARSARDataset, lidar_sar_collate_fn, ContrastiveAugmentation, LiDARAugmentation, SARAUGmentation
from utils import setup_ddp, cleanup_ddp
from utils.wandb_logger import WandBLogger

logger = logging.getLogger(__name__)


def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    losses: dict,
    config: OmegaConf,
    epoch: int,
    device: torch.device,
    logger: WandBLogger,
    accumulation_steps: int = 4
) -> dict:
    """Train for one epoch."""
    model.train()
    
    total_loss = 0.0
    num_batches = 0
    
    optimizer.zero_grad()
    
    for batch_idx, batch in enumerate(dataloader):
        # Move to device
        lidar_xyz = batch['lidar_xyz'].to(device)
        lidar_features = batch['lidar_features'].to(device)
        lidar_mask = batch['lidar_mask'].to(device)
        sar_slc = batch['sar_slc'].to(device)
        
        # Forward pass with AMP
        with torch.cuda.amp.autocast(dtype=torch.bfloat16):
            # Encode
            encoded = model.module.encode(lidar_xyz, lidar_features, sar_slc, lidar_mask)
            
            # Decode
            decoded = model.module.decode(
                encoded['z_lidar'],
                encoded['z_sar'],
                encoded['sar_skips'],
                encoded['sar_bottleneck']
            )
            
            # Compute losses
            # 1. Reconstruction loss
            recon_losses = losses['reconstruction'](
                decoded['lidar_points'],
                lidar_features,
                decoded['sar_slc'],
                sar_slc,
                lidar_mask
            )
            
            # 2. MAE loss (masked reconstruction)
            mae_loss_fn = losses['mae']
            lidar_mask_mae, sar_mask_mae = mae_loss_fn.generate_masks(
                lidar_xyz.shape[:2],
                sar_slc.shape
            )
            lidar_mae, sar_mae = mae_loss_fn(
                decoded['lidar_points'],
                lidar_features,
                lidar_mask_mae,
                decoded['sar_slc'],
                sar_slc,
                sar_mask_mae
            )
            
            # 3. Contrastive loss (simplified - would need augmented views)
            contrastive_loss = torch.tensor(0.0, device=device)  # Placeholder
            
            # 4. Decoupling loss
            decoupling_loss, gen_loss = losses['decoupling'](
                encoded['z_common'],
                encoded['z_unique_lidar'],
                encoded['z_unique_sar']
            )
            
            # Total loss
            loss = (
                config.training.loss_weights.reconstruction_lidar * recon_losses['lidar_l1'] +
                config.training.loss_weights.reconstruction_lidar * recon_losses['lidar_chamfer'] +
                config.training.loss_weights.reconstruction_sar * recon_losses['sar_amplitude'] +
                config.training.loss_weights.reconstruction_sar * recon_losses['sar_phase'] +
                config.training.loss_weights.mae * (lidar_mae + sar_mae) +
                config.training.loss_weights.contrastive * contrastive_loss +
                config.training.loss_weights.decoupling * decoupling_loss
            ) / accumulation_steps
        
        # Backward pass
        loss.backward()
        
        # Gradient accumulation
        if (batch_idx + 1) % accumulation_steps == 0:
            optimizer.step()
            optimizer.zero_grad()
        
        total_loss += loss.item() * accumulation_steps
        num_batches += 1
        
        # Logging
        if batch_idx % config.logging.log_interval == 0 and logger.rank == 0:
            logger.log({
                'train/loss': loss.item() * accumulation_steps,
                'train/lidar_l1': recon_losses['lidar_l1'].item(),
                'train/lidar_chamfer': recon_losses['lidar_chamfer'].item(),
                'train/sar_amplitude': recon_losses['sar_amplitude'].item(),
                'train/sar_phase': recon_losses['sar_phase'].item(),
                'train/mae_lidar': lidar_mae.item(),
                'train/mae_sar': sar_mae.item(),
                'train/decoupling': decoupling_loss.item(),
                'epoch': epoch,
                'batch': batch_idx
            })
    
    avg_loss = total_loss / num_batches
    return {'loss': avg_loss}


def main():
    """Main training function."""
    # Load config
    config = OmegaConf.load('config.yaml')
    
    # Setup DDP
    rank, local_rank, world_size = setup_ddp(config.distributed.backend)
    device = torch.device(f'cuda:{local_rank}' if torch.cuda.is_available() else 'cpu')
    
    # Set seed
    torch.manual_seed(config.logging.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(config.logging.seed)
    
    # Initialize WandB
    wandb_logger = WandBLogger(
        project=config.logging.wandb_project,
        entity=config.logging.wandb_entity,
        config=OmegaConf.to_container(config),
        rank=rank
    )
    
    # Create dataset
    train_dataset = LiDARSARDataset(
        config.data.train_path,
        max_points=config.data.lidar_max_points
    )
    
    # Create dataloader with DDP sampler
    train_sampler = torch.utils.data.distributed.DistributedSampler(
        train_dataset,
        num_replicas=world_size,
        rank=rank
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.training.batch_size,
        sampler=train_sampler,
        num_workers=config.data.num_workers,
        pin_memory=config.data.pin_memory,
        collate_fn=lidar_sar_collate_fn
    )
    
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
            'output_channels': config.data.lidar_channels
        },
        sar_config={
            'in_channels': config.data.sar_channels,
            'encoder_channels': config.model.sar.encoder_channels,
            'decoder_channels': config.model.sar.decoder_channels,
            'residual_connections': config.model.sar.residual_connections,
            'output_channels': config.data.sar_channels
        },
        fusion_config={
            'num_layers': config.model.fusion.num_layers,
            'num_heads': config.model.fusion.num_heads,
            'dim_feedforward': config.model.fusion.dim_feedforward,
            'dropout': config.model.dropout,
            'asymmetric_gating': config.model.fusion.asymmetric_gating
        }
    ).to(device)
    
    # Wrap with DDP
    if world_size > 1:
        model = DDP(model, device_ids=[local_rank], find_unused_parameters=config.distributed.find_unused_parameters)
    
    # Create losses
    losses = {
        'reconstruction': ReconstructionLoss(),
        'mae': CrossModalMAELoss(
            lidar_mask_ratio=config.training.lidar_mask_ratio,
            sar_mask_ratio=config.training.sar_mask_ratio
        ),
        'contrastive': InfoNCELoss(temperature=config.training.contrastive.temperature),
        'decoupling': DecouplingLoss()
    }
    
    # Create optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.training.learning_rate,
        weight_decay=config.training.weight_decay
    )
    
    # Training loop
    for epoch in range(config.training.num_epochs):
        train_sampler.set_epoch(epoch)
        
        metrics = train_epoch(
            model, train_loader, optimizer, losses, config, epoch, device, wandb_logger,
            accumulation_steps=config.training.gradient_accumulation_steps
        )
        
        if rank == 0:
            logger.info(f"Epoch {epoch}: loss={metrics['loss']:.4f}")
            
            # Save checkpoint
            if (epoch + 1) % config.logging.save_interval == 0:
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.module.state_dict() if world_size > 1 else model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'config': OmegaConf.to_container(config)
                }, f'checkpoints/checkpoint_epoch_{epoch}.pt')
    
    # Cleanup
    cleanup_ddp()
    wandb_logger.finish()


if __name__ == '__main__':
    main()
