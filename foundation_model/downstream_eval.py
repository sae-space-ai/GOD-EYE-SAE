"""
Downstream evaluation script with linear probe.

Evaluates frozen backbone on labeled downstream tasks.
"""

import os
import sys
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from omegaconf import OmegaConf
import logging
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import MultimodalAutoencoder, LinearProbe
from data import LiDARSARDataset, lidar_sar_collate_fn

logger = logging.getLogger(__name__)


def evaluate_linear_probe(
    probe: nn.Module,
    dataloader: DataLoader,
    device: torch.device
) -> dict:
    """
    Evaluate linear probe on labeled data.
    
    Returns:
        Dictionary with accuracy, macro-F1, confusion matrix
    """
    probe.eval()
    
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for batch in dataloader:
            lidar_xyz = batch['lidar_xyz'].to(device)
            lidar_features = batch['lidar_features'].to(device)
            lidar_mask = batch['lidar_mask'].to(device)
            sar_slc = batch['sar_slc'].to(device)
            labels = batch['label'].to(device)
            
            logits = probe(lidar_xyz, lidar_features, sar_slc, lidar_mask)
            preds = logits.argmax(dim=1)
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    
    accuracy = accuracy_score(all_labels, all_preds)
    macro_f1 = f1_score(all_labels, all_preds, average='macro')
    conf_matrix = confusion_matrix(all_labels, all_preds)
    
    return {
        'accuracy': accuracy,
        'macro_f1': macro_f1,
        'confusion_matrix': conf_matrix
    }


def main():
    """Main evaluation function."""
    # Load config
    config = OmegaConf.load('config.yaml')
    
    # Setup device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Load pretrained backbone
    checkpoint = torch.load('checkpoints/checkpoint_final.pt', map_location=device)
    
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
    )
    
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    
    # Create linear probe
    probe = LinearProbe(
        backbone=model,
        num_classes=config.downstream.num_classes,
        latent_dim=config.model.latent_dim,
        use_common=True
    ).to(device)
    
    # Load labeled dataset
    eval_dataset = LiDARSARDataset(
        config.data.val_path,
        max_points=config.data.lidar_max_points
    )
    
    eval_loader = DataLoader(
        eval_dataset,
        batch_size=config.training.batch_size,
        shuffle=False,
        num_workers=config.data.num_workers,
        collate_fn=lidar_sar_collate_fn
    )
    
    # Train linear probe
    optimizer = torch.optim.Adam(
        probe.get_trainable_parameters(),
        lr=config.downstream.linear_probe_lr
    )
    
    criterion = nn.CrossEntropyLoss()
    
    logger.info("Training linear probe...")
    for epoch in range(config.downstream.linear_probe_epochs):
        probe.train()
        
        for batch in eval_loader:
            lidar_xyz = batch['lidar_xyz'].to(device)
            lidar_features = batch['lidar_features'].to(device)
            lidar_mask = batch['lidar_mask'].to(device)
            sar_slc = batch['sar_slc'].to(device)
            labels = batch['label'].to(device)
            
            optimizer.zero_grad()
            logits = probe(lidar_xyz, lidar_features, sar_slc, lidar_mask)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
        
        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch + 1}/{config.downstream.linear_probe_epochs}")
    
    # Evaluate
    logger.info("Evaluating linear probe...")
    metrics = evaluate_linear_probe(probe, eval_loader, device)
    
    logger.info(f"Accuracy: {metrics['accuracy']:.4f}")
    logger.info(f"Macro-F1: {metrics['macro_f1']:.4f}")
    logger.info(f"Confusion Matrix:\n{metrics['confusion_matrix']}")
    
    # Save results
    torch.save({
        'metrics': metrics,
        'config': OmegaConf.to_container(config)
    }, 'results/downstream_eval.pt')


if __name__ == '__main__':
    main()
