#!/usr/bin/env python3
"""
Environment check script for GOD EYE SAE Foundation Model.

Validates that all required components are available for execution.
Exit code 0 = CPU validation possible, non-zero = cannot run model.
"""

import sys
import logging
from pathlib import Path
from typing import Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_python_version() -> Tuple[str, str]:
    """Check Python version."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        return "PASS", f"Python {version.major}.{version.minor}.{version.micro}"
    else:
        return "FAIL", f"Python {version.major}.{version.minor}.{version.micro} (requires 3.9+)"


def check_pytorch() -> Tuple[str, str]:
    """Check PyTorch installation."""
    try:
        import torch
        return "PASS", f"PyTorch {torch.__version__}"
    except ImportError:
        return "FAIL", "PyTorch not installed"


def check_torchvision() -> Tuple[str, str]:
    """Check torchvision installation."""
    try:
        import torchvision
        return "PASS", f"torchvision {torchvision.__version__}"
    except ImportError:
        return "FAIL", "torchvision not installed"


def check_torch_geometric() -> Tuple[str, str]:
    """Check torch-geometric installation."""
    try:
        import torch_geometric
        return "PASS", f"torch-geometric {torch_geometric.__version__}"
    except ImportError:
        return "WARNING", "torch-geometric not installed (optional for PointNet++)"


def check_cuda() -> Tuple[str, str]:
    """Check CUDA availability."""
    try:
        import torch
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0)
            return "PASS", f"CUDA available ({device_count} GPU(s), {device_name})"
        else:
            return "WARNING", "CUDA not available (CPU-only mode)"
    except Exception as e:
        return "FAIL", f"CUDA check failed: {e}"


def check_bf16_support() -> Tuple[str, str]:
    """Check BF16 support."""
    try:
        import torch
        if torch.cuda.is_available():
            # Try to create a BF16 tensor
            x = torch.randn(2, 2, device='cuda', dtype=torch.bfloat16)
            return "PASS", "BF16 supported on GPU"
        else:
            return "WARNING", "BF16 not testable (no CUDA)"
    except Exception as e:
        return "WARNING", f"BF16 not supported: {e}"


def check_omegaconf() -> Tuple[str, str]:
    """Check OmegaConf installation."""
    try:
        import omegaconf
        return "PASS", f"OmegaConf {omegaconf.__version__}"
    except ImportError:
        return "FAIL", "OmegaConf not installed"


def check_numpy() -> Tuple[str, str]:
    """Check NumPy installation."""
    try:
        import numpy
        return "PASS", f"NumPy {numpy.__version__}"
    except ImportError:
        return "FAIL", "NumPy not installed"


def check_h5py() -> Tuple[str, str]:
    """Check h5py installation."""
    try:
        import h5py
        return "PASS", f"h5py {h5py.__version__}"
    except ImportError:
        return "FAIL", "h5py not installed"


def check_wandb() -> Tuple[str, str]:
    """Check WandB installation."""
    try:
        import wandb
        return "PASS", f"WandB {wandb.__version__}"
    except ImportError:
        return "WARNING", "WandB not installed (optional, can use WANDB_MODE=disabled)"


def check_pytest() -> Tuple[str, str]:
    """Check pytest installation."""
    try:
        import pytest
        return "PASS", f"pytest {pytest.__version__}"
    except ImportError:
        return "FAIL", "pytest not installed"


def check_dataset_path() -> Tuple[str, str]:
    """Check if dataset path is configured."""
    try:
        from omegaconf import OmegaConf
        config = OmegaConf.load("config.yaml")
        train_path = config.data.train_path
        
        if train_path and Path(train_path).exists():
            return "PASS", f"Dataset found at {train_path}"
        elif train_path:
            return "WARNING", f"Dataset path configured but not found: {train_path}"
        else:
            return "WARNING", "Dataset path not configured in config.yaml"
    except Exception as e:
        return "WARNING", f"Dataset check failed: {e}"


def check_storage_directories() -> Tuple[str, str]:
    """Check storage directories."""
    dirs_to_check = [
        "foundation_model/runtime/checkpoints",
        "foundation_model/runtime/logs",
        "foundation_model/runtime/outputs"
    ]
    
    missing = []
    for dir_path in dirs_to_check:
        if not Path(dir_path).exists():
            missing.append(dir_path)
    
    if not missing:
        return "PASS", "All storage directories exist"
    else:
        return "WARNING", f"Missing directories: {', '.join(missing)}"


def check_config_file() -> Tuple[str, str]:
    """Check if config.yaml exists and is valid."""
    try:
        from omegaconf import OmegaConf
        config = OmegaConf.load("config.yaml")
        
        # Check critical fields
        required_fields = [
            'model.latent_dim',
            'model.num_heads',
            'training.batch_size',
            'training.learning_rate'
        ]
        
        missing = []
        for field in required_fields:
            parts = field.split('.')
            obj = config
            for part in parts:
                if not hasattr(obj, part):
                    missing.append(field)
                    break
                obj = getattr(obj, part)
        
        if missing:
            return "WARNING", f"Config missing fields: {', '.join(missing)}"
        else:
            return "PASS", "config.yaml valid"
    except Exception as e:
        return "FAIL", f"Config validation failed: {e}"


def main():
    """Run all environment checks."""
    logger.info("=" * 70)
    logger.info("GOD EYE SAE Foundation Model - Environment Check")
    logger.info("=" * 70)
    
    checks = [
        ("Python Version", check_python_version),
        ("PyTorch", check_pytorch),
        ("torchvision", check_torchvision),
        ("torch-geometric", check_torch_geometric),
        ("CUDA", check_cuda),
        ("BF16 Support", check_bf16_support),
        ("OmegaConf", check_omegaconf),
        ("NumPy", check_numpy),
        ("h5py", check_h5py),
        ("WandB", check_wandb),
        ("pytest", check_pytest),
        ("Dataset Path", check_dataset_path),
        ("Storage Directories", check_storage_directories),
        ("Config File", check_config_file),
    ]
    
    results = []
    fail_count = 0
    warning_count = 0
    
    for name, check_func in checks:
        status, message = check_func()
        results.append((name, status, message))
        
        if status == "FAIL":
            fail_count += 1
            logger.error(f"❌ {name}: {message}")
        elif status == "WARNING":
            warning_count += 1
            logger.warning(f"⚠️  {name}: {message}")
        else:
            logger.info(f"✅ {name}: {message}")
    
    logger.info("=" * 70)
    logger.info("Summary")
    logger.info("=" * 70)
    logger.info(f"Total checks: {len(results)}")
    logger.info(f"Passed: {len(results) - fail_count - warning_count}")
    logger.info(f"Warnings: {warning_count}")
    logger.info(f"Failed: {fail_count}")
    
    if fail_count > 0:
        logger.error("\n❌ Environment check FAILED - Cannot run model")
        logger.error("Please install missing dependencies from requirements.txt")
        return 1
    elif warning_count > 0:
        logger.warning("\n⚠️  Environment check PASSED with warnings")
        logger.warning("CPU validation is possible, but some features may be limited")
        return 0
    else:
        logger.info("\n✅ Environment check PASSED - Ready for validation")
        return 0


if __name__ == "__main__":
    sys.exit(main())
