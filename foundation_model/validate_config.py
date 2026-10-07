#!/usr/bin/env python3
"""
Configuration validation script for GOD EYE SAE Foundation Model.

Validates config.yaml for correctness and consistency.
Exit code 0 = valid, non-zero = invalid configuration.
"""

import sys
import logging
from pathlib import Path
from omegaconf import OmegaConf, DictConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_config(config_path: str = "config.yaml") -> bool:
    """Validate configuration file."""
    
    logger.info("=" * 70)
    logger.info("GOD EYE SAE Foundation Model - Configuration Validation")
    logger.info("=" * 70)
    
    # Load config
    if not Path(config_path).exists():
        logger.error(f"❌ Config file not found: {config_path}")
        return False
    
    try:
        config = OmegaConf.load(config_path)
        logger.info(f"✅ Loaded config from {config_path}")
    except Exception as e:
        logger.error(f"❌ Failed to load config: {e}")
        return False
    
    errors = []
    warnings = []
    
    # Model architecture validation
    logger.info("\nValidating model architecture...")
    
    if not hasattr(config, 'model'):
        errors.append("Missing 'model' section")
    else:
        model = config.model
        
        # latent_dim
        if not hasattr(model, 'latent_dim'):
            errors.append("Missing model.latent_dim")
        elif model.latent_dim <= 0:
            errors.append(f"model.latent_dim must be > 0, got {model.latent_dim}")
        
        # num_heads
        if not hasattr(model, 'num_heads'):
            errors.append("Missing model.num_heads")
        elif model.num_heads <= 0:
            errors.append(f"model.num_heads must be > 0, got {model.num_heads}")
        
        # Check divisibility
        if hasattr(model, 'latent_dim') and hasattr(model, 'num_heads'):
            if model.latent_dim % model.num_heads != 0:
                errors.append(
                    f"model.latent_dim ({model.latent_dim}) must be divisible by "
                    f"model.num_heads ({model.num_heads})"
                )
        
        # num_layers
        if hasattr(model, 'num_layers') and model.num_layers <= 0:
            errors.append(f"model.num_layers must be > 0, got {model.num_layers}")
        
        # LiDAR config
        if hasattr(model, 'lidar'):
            if hasattr(model.lidar, 'knn_k') and model.lidar.knn_k <= 0:
                errors.append(f"model.lidar.knn_k must be > 0, got {model.lidar.knn_k}")
        
        # Fusion config
        if hasattr(model, 'fusion'):
            if hasattr(model.fusion, 'num_layers') and model.fusion.num_layers <= 0:
                errors.append(f"model.fusion.num_layers must be > 0, got {model.fusion.num_layers}")
    
    # Training validation
    logger.info("Validating training configuration...")
    
    if not hasattr(config, 'training'):
        errors.append("Missing 'training' section")
    else:
        training = config.training
        
        # batch_size
        if not hasattr(training, 'batch_size'):
            errors.append("Missing training.batch_size")
        elif training.batch_size <= 0:
            errors.append(f"training.batch_size must be > 0, got {training.batch_size}")
        
        # epochs
        if hasattr(training, 'epochs') and training.epochs <= 0:
            errors.append(f"training.epochs must be > 0, got {training.epochs}")
        
        # learning_rate
        if not hasattr(training, 'learning_rate'):
            errors.append("Missing training.learning_rate")
        elif training.learning_rate <= 0:
            errors.append(f"training.learning_rate must be > 0, got {training.learning_rate}")
        
        # gradient_accumulation_steps
        if hasattr(training, 'gradient_accumulation_steps'):
            if training.gradient_accumulation_steps <= 0:
                errors.append(
                    f"training.gradient_accumulation_steps must be > 0, "
                    f"got {training.gradient_accumulation_steps}"
                )
        
        # Mask ratios
        if hasattr(training, 'lidar_mask_ratio'):
            if not (0 < training.lidar_mask_ratio < 1):
                errors.append(
                    f"training.lidar_mask_ratio must be in (0, 1), "
                    f"got {training.lidar_mask_ratio}"
                )
        
        if hasattr(training, 'sar_mask_ratio'):
            if not (0 < training.sar_mask_ratio < 1):
                errors.append(
                    f"training.sar_mask_ratio must be in (0, 1), "
                    f"got {training.sar_mask_ratio}"
                )
        
        # Contrastive temperature
        if hasattr(training, 'contrastive'):
            if hasattr(training.contrastive, 'temperature'):
                if training.contrastive.temperature <= 0:
                    errors.append(
                        f"training.contrastive.temperature must be > 0, "
                        f"got {training.contrastive.temperature}"
                    )
    
    # Data validation
    logger.info("Validating data configuration...")
    
    if not hasattr(config, 'data'):
        errors.append("Missing 'data' section")
    else:
        data = config.data
        
        # SAR representation consistency
        if hasattr(data, 'sar_representation') and hasattr(data, 'sar_channels'):
            rep = data.sar_representation
            channels = data.sar_channels
            
            if rep == 'dual_pol_real_imag' and channels != 4:
                errors.append(
                    f"sar_representation is '{rep}' but sar_channels is {channels}. "
                    f"Expected 4 channels for dual-pol real/imag."
                )
            elif rep == 'single_pol_amp_phase' and channels != 2:
                errors.append(
                    f"sar_representation is '{rep}' but sar_channels is {channels}. "
                    f"Expected 2 channels for single-pol amplitude/phase."
                )
        
        # Dataset paths
        if hasattr(data, 'train_path'):
            train_path = Path(data.train_path)
            if not train_path.exists():
                warnings.append(
                    f"training dataset path does not exist: {data.train_path}"
                )
        
        if hasattr(data, 'val_path'):
            val_path = Path(data.val_path)
            if not val_path.exists():
                warnings.append(
                    f"validation dataset path does not exist: {data.val_path}"
                )
    
    # Distributed validation
    logger.info("Validating distributed configuration...")
    
    if hasattr(config, 'distributed'):
        if hasattr(config.distributed, 'backend'):
            backend = config.distributed.backend
            if backend not in ['nccl', 'gloo', 'mpi']:
                errors.append(
                    f"distributed.backend must be 'nccl', 'gloo', or 'mpi', "
                    f"got '{backend}'"
                )
    
    # Logging validation
    logger.info("Validating logging configuration...")
    
    if hasattr(config, 'logging'):
        if hasattr(config.logging, 'seed'):
            if not isinstance(config.logging.seed, int):
                errors.append(f"logging.seed must be int, got {type(config.logging.seed)}")
    
    # Report results
    logger.info("\n" + "=" * 70)
    logger.info("Validation Results")
    logger.info("=" * 70)
    
    if errors:
        logger.error(f"\n❌ Found {len(errors)} error(s):")
        for error in errors:
            logger.error(f"  • {error}")
    
    if warnings:
        logger.warning(f"\n⚠️  Found {len(warnings)} warning(s):")
        for warning in warnings:
            logger.warning(f"  • {warning}")
    
    if not errors and not warnings:
        logger.info("\n✅ Configuration is valid")
        return True
    elif errors:
        logger.error("\n❌ Configuration is INVALID")
        return False
    else:
        logger.warning("\n⚠️  Configuration is valid with warnings")
        return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate configuration file')
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    args = parser.parse_args()
    
    success = validate_config(args.config)
    
    if success:
        logger.info("\n✅ Configuration validation PASSED")
        return 0
    else:
        logger.error("\n❌ Configuration validation FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
