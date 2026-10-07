#!/usr/bin/env python3
"""
Dataset inspection script for GOD EYE SAE Foundation Model.

Inspects HDF5/NetCDF dataset files and reports statistics.
"""

import sys
import logging
import h5py
import numpy as np
from pathlib import Path
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def inspect_hdf5(file_path: str, max_samples: int = 100) -> Dict[str, Any]:
    """Inspect HDF5 dataset file."""
    
    logger.info(f"Inspecting dataset: {file_path}")
    
    if not Path(file_path).exists():
        logger.error(f"File not found: {file_path}")
        return {}
    
    stats = {
        'file_path': file_path,
        'num_samples': 0,
        'keys': [],
        'lidar_stats': {},
        'sar_stats': {},
        'warnings': []
    }
    
    try:
        with h5py.File(file_path, 'r') as f:
            # Get all keys
            stats['keys'] = list(f.keys())
            logger.info(f"Found keys: {stats['keys']}")
            
            # Check for required keys
            if 'lidar_points' not in f:
                stats['warnings'].append("Missing 'lidar_points' key")
            if 'sar_slc' not in f:
                stats['warnings'].append("Missing 'sar_slc' key")
            
            # LiDAR statistics
            if 'lidar_points' in f:
                lidar = f['lidar_points']
                stats['num_samples'] = len(lidar)
                
                # Sample first N samples for statistics
                sample_size = min(max_samples, len(lidar))
                lidar_sample = lidar[:sample_size]
                
                # Point counts
                point_counts = [len(points) for points in lidar_sample]
                stats['lidar_stats'] = {
                    'num_samples': len(lidar),
                    'min_points': int(np.min(point_counts)),
                    'max_points': int(np.max(point_counts)),
                    'mean_points': float(np.mean(point_counts)),
                    'std_points': float(np.std(point_counts)),
                    'dtype': str(lidar_sample[0].dtype) if len(lidar_sample) > 0 else 'unknown',
                    'channels': lidar_sample[0].shape[1] if len(lidar_sample) > 0 and len(lidar_sample[0].shape) > 1 else 0
                }
                
                # Coordinate ranges (sample)
                if len(lidar_sample) > 0 and lidar_sample[0].shape[1] >= 3:
                    all_points = np.vstack([points[:, :3] for points in lidar_sample if len(points) > 0])
                    stats['lidar_stats']['coord_ranges'] = {
                        'x': (float(np.min(all_points[:, 0])), float(np.max(all_points[:, 0]))),
                        'y': (float(np.min(all_points[:, 1])), float(np.max(all_points[:, 1]))),
                        'z': (float(np.min(all_points[:, 2])), float(np.max(all_points[:, 2])))
                    }
                
                # Check for NaN/Inf
                nan_count = 0
                inf_count = 0
                for points in lidar_sample:
                    if len(points) > 0:
                        nan_count += np.sum(np.isnan(points))
                        inf_count += np.sum(np.isinf(points))
                
                stats['lidar_stats']['nan_count'] = int(nan_count)
                stats['lidar_stats']['inf_count'] = int(inf_count)
                
                if nan_count > 0:
                    stats['warnings'].append(f"LiDAR contains {nan_count} NaN values")
                if inf_count > 0:
                    stats['warnings'].append(f"LiDAR contains {inf_count} Inf values")
            
            # SAR statistics
            if 'sar_slc' in f:
                sar = f['sar_slc']
                
                # Sample first N samples
                sample_size = min(max_samples, len(sar))
                sar_sample = sar[:sample_size]
                
                stats['sar_stats'] = {
                    'num_samples': len(sar),
                    'shape': sar_sample[0].shape if len(sar_sample) > 0 else (),
                    'dtype': str(sar_sample[0].dtype) if len(sar_sample) > 0 else 'unknown',
                    'channels': sar_sample[0].shape[0] if len(sar_sample) > 0 and len(sar_sample[0].shape) > 2 else 0
                }
                
                # Value ranges
                if len(sar_sample) > 0:
                    all_values = np.concatenate([s.flatten() for s in sar_sample])
                    stats['sar_stats']['value_ranges'] = {
                        'min': float(np.min(all_values)),
                        'max': float(np.max(all_values)),
                        'mean': float(np.mean(all_values)),
                        'std': float(np.std(all_values))
                    }
                
                # Check for NaN/Inf
                nan_count = 0
                inf_count = 0
                for sar_img in sar_sample:
                    nan_count += np.sum(np.isnan(sar_img))
                    inf_count += np.sum(np.isinf(sar_img))
                
                stats['sar_stats']['nan_count'] = int(nan_count)
                stats['sar_stats']['inf_count'] = int(inf_count)
                
                if nan_count > 0:
                    stats['warnings'].append(f"SAR contains {nan_count} NaN values")
                if inf_count > 0:
                    stats['warnings'].append(f"SAR contains {inf_count} Inf values")
    
    except Exception as e:
        logger.error(f"Error inspecting file: {e}")
        stats['error'] = str(e)
    
    return stats


def print_report(stats: Dict[str, Any]):
    """Print inspection report."""
    
    logger.info("=" * 70)
    logger.info("Dataset Inspection Report")
    logger.info("=" * 70)
    
    logger.info(f"\nFile: {stats.get('file_path', 'N/A')}")
    logger.info(f"Total samples: {stats.get('num_samples', 0)}")
    logger.info(f"Keys: {stats.get('keys', [])}")
    
    if stats.get('lidar_stats'):
        lidar = stats['lidar_stats']
        logger.info("\n" + "-" * 70)
        logger.info("LiDAR Statistics")
        logger.info("-" * 70)
        logger.info(f"  Samples: {lidar.get('num_samples', 0)}")
        logger.info(f"  Points per sample:")
        logger.info(f"    Min: {lidar.get('min_points', 'N/A')}")
        logger.info(f"    Max: {lidar.get('max_points', 'N/A')}")
        logger.info(f"    Mean: {lidar.get('mean_points', 'N/A'):.1f}")
        logger.info(f"    Std: {lidar.get('std_points', 'N/A'):.1f}")
        logger.info(f"  Channels: {lidar.get('channels', 'N/A')}")
        logger.info(f"  Dtype: {lidar.get('dtype', 'N/A')}")
        logger.info(f"  NaN count: {lidar.get('nan_count', 0)}")
        logger.info(f"  Inf count: {lidar.get('inf_count', 0)}")
        
        if 'coord_ranges' in lidar:
            logger.info("  Coordinate ranges:")
            for axis, (min_val, max_val) in lidar['coord_ranges'].items():
                logger.info(f"    {axis}: [{min_val:.2f}, {max_val:.2f}]")
    
    if stats.get('sar_stats'):
        sar = stats['sar_stats']
        logger.info("\n" + "-" * 70)
        logger.info("SAR Statistics")
        logger.info("-" * 70)
        logger.info(f"  Samples: {sar.get('num_samples', 0)}")
        logger.info(f"  Shape: {sar.get('shape', 'N/A')}")
        logger.info(f"  Channels: {sar.get('channels', 'N/A')}")
        logger.info(f"  Dtype: {sar.get('dtype', 'N/A')}")
        logger.info(f"  NaN count: {sar.get('nan_count', 0)}")
        logger.info(f"  Inf count: {sar.get('inf_count', 0)}")
        
        if 'value_ranges' in sar:
            vr = sar['value_ranges']
            logger.info("  Value ranges:")
            logger.info(f"    Min: {vr['min']:.4f}")
            logger.info(f"    Max: {vr['max']:.4f}")
            logger.info(f"    Mean: {vr['mean']:.4f}")
            logger.info(f"    Std: {vr['std']:.4f}")
    
    if stats.get('warnings'):
        logger.info("\n" + "-" * 70)
        logger.warning("Warnings")
        logger.warning("-" * 70)
        for warning in stats['warnings']:
            logger.warning(f"  ⚠️  {warning}")
    
    if stats.get('error'):
        logger.error(f"\n❌ Error: {stats['error']}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Inspect dataset file')
    parser.add_argument('file', type=str, help='Path to HDF5/NetCDF file')
    parser.add_argument(
        '--max-samples',
        type=int,
        default=100,
        help='Maximum number of samples to inspect (default: 100)'
    )
    args = parser.parse_args()
    
    stats = inspect_hdf5(args.file, args.max_samples)
    
    if stats:
        print_report(stats)
        
        if stats.get('error'):
            return 1
        elif stats.get('warnings'):
            return 0  # Warnings are OK
        else:
            return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
