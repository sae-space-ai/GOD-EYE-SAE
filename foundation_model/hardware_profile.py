#!/usr/bin/env python3
"""
Hardware profiling script for GOD EYE SAE Foundation Model.

Reports available hardware and recommends configuration parameters.
"""

import sys
import logging
import platform
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_cpu_info() -> Dict[str, Any]:
    """Get CPU information."""
    info = {
        'system': platform.system(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version()
    }
    
    # Try to get CPU count
    try:
        import os
        info['cpu_count'] = os.cpu_count()
    except:
        info['cpu_count'] = 'unknown'
    
    # Try to get RAM (Linux only)
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if 'MemTotal' in line:
                    ram_kb = int(line.split()[1])
                    info['ram_gb'] = ram_kb / (1024 * 1024)
                    break
    except:
        info['ram_gb'] = 'unknown'
    
    return info


def get_gpu_info() -> Dict[str, Any]:
    """Get GPU information."""
    info = {
        'cuda_available': False,
        'gpu_count': 0,
        'gpus': []
    }
    
    try:
        import torch
        
        info['cuda_available'] = torch.cuda.is_available()
        
        if torch.cuda.is_available():
            info['gpu_count'] = torch.cuda.device_count()
            info['cuda_version'] = torch.version.cuda
            
            for i in range(info['gpu_count']):
                gpu_info = {
                    'id': i,
                    'name': torch.cuda.get_device_name(i),
                    'capability': torch.cuda.get_device_capability(i)
                }
                
                # Get memory info
                try:
                    props = torch.cuda.get_device_properties(i)
                    gpu_info['total_memory_gb'] = props.total_memory / (1024**3)
                except:
                    gpu_info['total_memory_gb'] = 'unknown'
                
                # Check BF16 support
                try:
                    x = torch.randn(2, 2, device=f'cuda:{i}', dtype=torch.bfloat16)
                    gpu_info['bf16_supported'] = True
                except:
                    gpu_info['bf16_supported'] = False
                
                info['gpus'].append(gpu_info)
        
        # Check MPS (Apple Silicon)
        try:
            info['mps_available'] = torch.backends.mps.is_available()
        except:
            info['mps_available'] = False
    
    except ImportError:
        logger.warning("PyTorch not available for GPU detection")
    
    return info


def recommend_config(cpu_info: Dict, gpu_info: Dict) -> Dict[str, Any]:
    """Recommend configuration based on hardware."""
    
    recommendations = {
        'device': 'cpu',
        'precision': 'fp32',
        'batch_size': 4,
        'num_workers': 2,
        'distributed': False,
        'notes': []
    }
    
    # GPU recommendations
    if gpu_info['cuda_available'] and gpu_info['gpu_count'] > 0:
        recommendations['device'] = 'cuda'
        
        # Check if any GPU supports BF16
        bf16_supported = any(gpu.get('bf16_supported', False) for gpu in gpu_info['gpus'])
        if bf16_supported:
            recommendations['precision'] = 'bf16'
            recommendations['notes'].append("BF16 precision available")
        
        # Recommend batch size based on GPU memory
        if gpu_info['gpus']:
            gpu_memory = gpu_info['gpus'][0].get('total_memory_gb', 0)
            if isinstance(gpu_memory, (int, float)):
                if gpu_memory >= 24:  # RTX 3090/4090, A100
                    recommendations['batch_size'] = 8
                    recommendations['notes'].append("Large GPU memory detected")
                elif gpu_memory >= 16:  # RTX 3080/4080
                    recommendations['batch_size'] = 6
                elif gpu_memory >= 8:  # RTX 3070/4070
                    recommendations['batch_size'] = 4
                else:
                    recommendations['batch_size'] = 2
                    recommendations['notes'].append("Limited GPU memory")
        
        # Multi-GPU recommendations
        if gpu_info['gpu_count'] > 1:
            recommendations['distributed'] = True
            recommendations['notes'].append(f"Multi-GPU detected ({gpu_info['gpu_count']} GPUs)")
            recommendations['notes'].append("Use torchrun for DDP training")
        
        # Num workers
        cpu_count = cpu_info.get('cpu_count', 4)
        if isinstance(cpu_count, int):
            recommendations['num_workers'] = min(cpu_count, 8)
    
    # MPS (Apple Silicon)
    elif gpu_info.get('mps_available', False):
        recommendations['device'] = 'mps'
        recommendations['precision'] = 'fp32'
        recommendations['batch_size'] = 4
        recommendations['notes'].append("Apple Silicon MPS detected")
        recommendations['notes'].append("BF16 not yet fully supported on MPS")
    
    # CPU fallback
    else:
        recommendations['notes'].append("No GPU detected, using CPU")
        recommendations['notes'].append("Training will be slow")
        recommendations['notes'].append("Consider using GPU for production")
    
    return recommendations


def print_report(cpu_info: Dict, gpu_info: Dict, recommendations: Dict):
    """Print hardware profile report."""
    
    logger.info("=" * 70)
    logger.info("Hardware Profile Report")
    logger.info("=" * 70)
    
    # CPU info
    logger.info("\n" + "-" * 70)
    logger.info("CPU Information")
    logger.info("-" * 70)
    logger.info(f"  System: {cpu_info.get('system', 'unknown')}")
    logger.info(f"  Machine: {cpu_info.get('machine', 'unknown')}")
    logger.info(f"  Processor: {cpu_info.get('processor', 'unknown')}")
    logger.info(f"  CPU Count: {cpu_info.get('cpu_count', 'unknown')}")
    logger.info(f"  RAM: {cpu_info.get('ram_gb', 'unknown')} GB")
    logger.info(f"  Python: {cpu_info.get('python_version', 'unknown')}")
    
    # GPU info
    logger.info("\n" + "-" * 70)
    logger.info("GPU Information")
    logger.info("-" * 70)
    
    if gpu_info['cuda_available']:
        logger.info(f"  CUDA Available: Yes")
        logger.info(f"  CUDA Version: {gpu_info.get('cuda_version', 'unknown')}")
        logger.info(f"  GPU Count: {gpu_info['gpu_count']}")
        
        for gpu in gpu_info['gpus']:
            logger.info(f"\n  GPU {gpu['id']}:")
            logger.info(f"    Name: {gpu['name']}")
            logger.info(f"    Compute Capability: {gpu['capability']}")
            logger.info(f"    Memory: {gpu.get('total_memory_gb', 'unknown')} GB")
            logger.info(f"    BF16 Support: {'Yes' if gpu.get('bf16_supported') else 'No'}")
    else:
        logger.info("  CUDA Available: No")
        
        if gpu_info.get('mps_available'):
            logger.info("  MPS Available: Yes (Apple Silicon)")
        else:
            logger.info("  MPS Available: No")
    
    # Recommendations
    logger.info("\n" + "-" * 70)
    logger.info("Recommended Configuration")
    logger.info("-" * 70)
    logger.info(f"  Device: {recommendations['device']}")
    logger.info(f"  Precision: {recommendations['precision']}")
    logger.info(f"  Batch Size: {recommendations['batch_size']}")
    logger.info(f"  Num Workers: {recommendations['num_workers']}")
    logger.info(f"  Distributed: {'Yes' if recommendations['distributed'] else 'No'}")
    
    if recommendations['notes']:
        logger.info("\n  Notes:")
        for note in recommendations['notes']:
            logger.info(f"    • {note}")


def main():
    """Main entry point."""
    
    logger.info("Profiling hardware...")
    
    cpu_info = get_cpu_info()
    gpu_info = get_gpu_info()
    recommendations = recommend_config(cpu_info, gpu_info)
    
    print_report(cpu_info, gpu_info, recommendations)
    
    logger.info("\n" + "=" * 70)
    logger.info("Hardware profiling complete")
    logger.info("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
