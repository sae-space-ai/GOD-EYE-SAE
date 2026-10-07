#!/usr/bin/env python3
"""
Synthetic dataset generator for GOD EYE SAE Foundation Model.

Creates small synthetic datasets for testing and validation.
NOT for scientific use - only for development and testing.
"""

import sys
import logging
import h5py
import numpy as np
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_synthetic_lidar(
    num_points: int,
    num_channels: int = 4,
    seed: int = None
) -> np.ndarray:
    """Generate synthetic LiDAR point cloud."""
    
    if seed is not None:
        np.random.seed(seed)
    
    # Generate random points in a unit cube
    points = np.random.randn(num_points, num_channels).astype(np.float32)
    
    # Scale coordinates to reasonable range
    points[:, :3] *= 10.0  # x, y, z in meters
    
    # Intensity in [0, 1]
    if num_channels >= 4:
        points[:, 3] = np.abs(points[:, 3]) / 10.0
    
    return points


def generate_synthetic_sar(
    height: int,
    width: int,
    num_channels: int = 4,
    seed: int = None
) -> np.ndarray:
    """Generate synthetic SAR SLC image."""
    
    if seed is not None:
        np.random.seed(seed)
    
    # Generate random complex-like data
    sar = np.random.randn(num_channels, height, width).astype(np.float32)
    
    # Scale to reasonable range
    sar *= 0.1
    
    return sar


def create_synthetic_dataset(
    output_path: str,
    num_train: int = 16,
    num_val: int = 4,
    num_test: int = 4,
    lidar_points_range: tuple = (64, 256),
    sar_size: int = 64,
    sar_channels: int = 4,
    seed: int = 42
):
    """Create synthetic dataset for testing."""
    
    logger.info("=" * 70)
    logger.info("Creating Synthetic Dataset")
    logger.info("=" * 70)
    logger.info("⚠️  WARNING: This is SYNTHETIC TEST DATA ONLY")
    logger.info("⚠️  NOT for scientific use or training")
    logger.info("=" * 70)
    
    np.random.seed(seed)
    
    # Create output directory
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate train/val/test splits
    splits = {
        'train': num_train,
        'val': num_val,
        'test': num_test
    }
    
    for split_name, num_samples in splits.items():
        split_path = output_dir / f"{split_name}.hdf5"
        logger.info(f"\nGenerating {split_name} split: {num_samples} samples")
        
        with h5py.File(split_path, 'w') as f:
            # Create variable-length datasets
            lidar_dtype = h5py.special_dtype(vlen=np.dtype('float32'))
            lidar_ds = f.create_dataset(
                'lidar_points',
                (num_samples,),
                dtype=lidar_dtype
            )
            
            # SAR is fixed size
            sar_shape = (num_samples, sar_channels, sar_size, sar_size)
            sar_ds = f.create_dataset(
                'sar_slc',
                sar_shape,
                dtype=np.float32
            )
            
            # Generate samples
            for i in range(num_samples):
                # Variable number of LiDAR points
                num_points = np.random.randint(
                    lidar_points_range[0],
                    lidar_points_range[1] + 1
                )
                
                lidar_points = generate_synthetic_lidar(
                    num_points,
                    num_channels=4,
                    seed=seed + i
                )
                lidar_ds[i] = lidar_points
                
                sar_slc = generate_synthetic_sar(
                    sar_size,
                    sar_size,
                    num_channels=sar_channels,
                    seed=seed + i + 1000
                )
                sar_ds[i] = sar_slc
                
                if (i + 1) % 10 == 0 or i == num_samples - 1:
                    logger.info(f"  Generated {i + 1}/{num_samples} samples")
        
        logger.info(f"✅ Created {split_path}")
    
    logger.info("\n" + "=" * 70)
    logger.info("Synthetic Dataset Creation Complete")
    logger.info("=" * 70)
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Total samples: {sum(splits.values())}")
    logger.info(f"  Train: {num_train}")
    logger.info(f"  Val: {num_val}")
    logger.info(f"  Test: {num_test}")
    logger.info(f"LiDAR points range: {lidar_points_range}")
    logger.info(f"SAR size: {sar_size}x{sar_size}")
    logger.info(f"SAR channels: {sar_channels}")
    logger.info("\n⚠️  REMINDER: This is synthetic test data only!")
    logger.info("⚠️  Do not use for scientific experiments or training!")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create synthetic dataset for testing'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='foundation_model/runtime/data/synthetic/train.hdf5',
        help='Output path for train dataset'
    )
    parser.add_argument(
        '--num-train',
        type=int,
        default=16,
        help='Number of training samples'
    )
    parser.add_argument(
        '--num-val',
        type=int,
        default=4,
        help='Number of validation samples'
    )
    parser.add_argument(
        '--num-test',
        type=int,
        default=4,
        help='Number of test samples'
    )
    parser.add_argument(
        '--lidar-min-points',
        type=int,
        default=64,
        help='Minimum LiDAR points per sample'
    )
    parser.add_argument(
        '--lidar-max-points',
        type=int,
        default=256,
        help='Maximum LiDAR points per sample'
    )
    parser.add_argument(
        '--sar-size',
        type=int,
        default=64,
        help='SAR image size (height=width)'
    )
    parser.add_argument(
        '--sar-channels',
        type=int,
        default=4,
        help='Number of SAR channels'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed'
    )
    args = parser.parse_args()
    
    create_synthetic_dataset(
        output_path=args.output,
        num_train=args.num_train,
        num_val=args.num_val,
        num_test=args.num_test,
        lidar_points_range=(args.lidar_min_points, args.lidar_max_points),
        sar_size=args.sar_size,
        sar_channels=args.sar_channels,
        seed=args.seed
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
