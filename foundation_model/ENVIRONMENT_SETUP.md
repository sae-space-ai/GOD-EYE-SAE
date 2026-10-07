# Environment Setup Guide

Complete guide for setting up the GOD EYE SAE Foundation Model environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Windows CPU Setup](#windows-cpu-setup)
4. [Linux CPU Setup](#linux-cpu-setup)
5. [Linux NVIDIA GPU Setup](#linux-nvidia-gpu-setup)
6. [Multi-GPU DDP Setup](#multi-gpu-ddp-setup)
7. [Docker Setup](#docker-setup)
8. [Dataset Preparation](#dataset-preparation)
9. [Validation](#validation)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required

- **Python 3.11** (recommended) or 3.9+
- **Git**
- **4GB+ RAM** (8GB+ recommended)
- **10GB+ disk space**

### Optional (for GPU training)

- **NVIDIA GPU** with 8GB+ VRAM
- **NVIDIA Driver** 525.60+ (Linux) or 528.33+ (Windows)
- **CUDA 11.8** or **CUDA 12.1**

## Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd GOD-EYE-SAE

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# 4. Install dependencies
cd foundation_model
pip install -r requirements.txt

# 5. Check environment
python check_environment.py

# 6. Validate configuration
python validate_config.py

# 7. Create synthetic dataset for testing
python create_synthetic_dataset.py

# 8. Run tests
pytest tests/ -v

# 9. Run Phase 3B.1 validation
python validate_phase3b1.py
```

## Windows CPU Setup

### 1. Install Python 3.11

Download from https://www.python.org/downloads/

**Important**: Check "Add Python to PATH" during installation.

### 2. Install Git

Download from https://git-scm.com/download/win

### 3. Create Virtual Environment

```powershell
# Open PowerShell
cd GOD-EYE-SAE
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies (CPU-only)

```powershell
cd foundation_model

# Install CPU-only PyTorch
pip install torch==2.1.0+cpu torchvision==0.16.0+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Install other dependencies
pip install -r requirements.txt
```

### 5. Verify Installation

```powershell
python check_environment.py
```

Expected output:
```
✅ Python Version: Python 3.11.x
✅ PyTorch: PyTorch 2.1.0+cpu
✅ CUDA: CUDA not available (CPU-only mode)
```

## Linux CPU Setup

### 1. Install Python 3.11

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Or use pyenv
curl https://pyenv.run | bash
pyenv install 3.11.0
pyenv global 3.11.0
```

### 2. Create Virtual Environment

```bash
cd GOD-EYE-SAE
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
cd foundation_model

# Install CPU-only PyTorch
pip install torch==2.1.0+cpu torchvision==0.16.0+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Install other dependencies
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python check_environment.py
```

## Linux NVIDIA GPU Setup

### 1. Install NVIDIA Driver

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nvidia-driver-535

# Reboot
sudo reboot

# Verify
nvidia-smi
```

### 2. Install CUDA Toolkit

```bash
# Download from https://developer.nvidia.com/cuda-downloads
# Or use package manager

# Ubuntu 22.04 with CUDA 12.1
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install cuda-toolkit-12-1

# Add to PATH
export PATH=/usr/local/cuda-12.1/bin${PATH:+:${PATH}}
export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
```

### 3. Create Virtual Environment

```bash
cd GOD-EYE-SAE
python3.11 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies (GPU)

```bash
cd foundation_model

# Install PyTorch with CUDA 12.1
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121

# Install other dependencies
pip install -r requirements.txt
```

### 5. Verify GPU

```bash
python check_environment.py
```

Expected output:
```
✅ CUDA: CUDA available (1 GPU(s), NVIDIA GeForce RTX 4090)
✅ BF16 Support: BF16 supported on GPU
```

## Multi-GPU DDP Setup

### 1. Ensure Multiple GPUs

```bash
nvidia-smi
```

Should show multiple GPUs.

### 2. Install NCCL

```bash
# Ubuntu/Debian
sudo apt install libnccl2 libnccl-dev
```

### 3. Run with torchrun

```bash
# 4 GPUs
torchrun --nproc_per_node=4 train.py --config config.yaml

# 2 GPUs
torchrun --nproc_per_node=2 train.py --config config.yaml
```

### 4. Verify DDP

```bash
python hardware_profile.py
```

Should show:
```
Recommended Configuration
  Distributed: Yes
  Notes:
    • Multi-GPU detected (4 GPUs)
    • Use torchrun for DDP training
```

## Docker Setup

### CPU Docker

```bash
cd foundation_model

# Build image
docker build -t god-eye-sae-cpu -f Dockerfile .

# Run environment check
docker run --rm god-eye-sae-cpu

# Run tests
docker run --rm god-eye-sae-cpu pytest tests/ -v

# Run validation
docker run --rm god-eye-sae-cpu python validate_phase3b1.py --overfit-steps 10
```

### GPU Docker (requires NVIDIA Container Toolkit)

```bash
# Install NVIDIA Container Toolkit
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

# Build GPU image (create Dockerfile.cuda first)
docker build -t god-eye-sae-gpu -f Dockerfile.cuda .

# Run with GPU
docker run --gpus all --rm god-eye-sae-gpu python check_environment.py
```

## Dataset Preparation

### Dataset Format

HDF5 format with the following structure:

```
train.hdf5
├── lidar_points: (N,) variable-length float32 arrays
│   └── Each: (num_points, 4) - x, y, z, intensity
└── sar_slc: (N, 4, H, W) float32 array
    └── Channels: VV_real, VV_imag, VH_real, VH_imag
```

### Create Synthetic Dataset

```bash
cd foundation_model

python create_synthetic_dataset.py \
  --output runtime/data/synthetic/train.hdf5 \
  --num-train 100 \
  --num-val 20 \
  --num-test 20 \
  --sar-channels 4
```

### Inspect Dataset

```bash
python inspect_dataset.py runtime/data/synthetic/train.hdf5
```

### Configure Dataset Path

Edit `config.yaml`:

```yaml
data:
  train_path: "runtime/data/train.hdf5"
  val_path: "runtime/data/val.hdf5"
  test_path: "runtime/data/test.hdf5"
```

Or use environment variable:

```bash
export GOD_EYE_DATA_ROOT=/path/to/data
```

## Validation

### 1. Environment Check

```bash
python check_environment.py
```

All critical components should show ✅ PASS.

### 2. Configuration Validation

```bash
python validate_config.py
```

Should show ✅ Configuration is valid.

### 3. Hardware Profile

```bash
python hardware_profile.py
```

Review recommended configuration.

### 4. Run Tests

```bash
pytest tests/ -v
```

All tests should pass.

### 5. Phase 3B.1 Validation

```bash
python validate_phase3b1.py
```

Review `validation_report_phase3b1.json` for detailed results.

### 6. Smoke Test

```bash
python train.py --config config.yaml --smoke-test
```

Should complete 1 epoch with 10 steps.

## Troubleshooting

### PyTorch Import Error

```
ImportError: libtorch_cuda.so: cannot open shared object file
```

**Solution**: Install correct PyTorch version for your CUDA:

```bash
# CUDA 11.8
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121

# CPU only
pip install torch==2.1.0+cpu torchvision==0.16.0+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html
```

### CUDA Out of Memory

```
RuntimeError: CUDA out of memory
```

**Solutions**:
1. Reduce batch size in `config.yaml`:
   ```yaml
   training:
     batch_size: 2  # or 1
   ```

2. Enable gradient checkpointing (if implemented)

3. Use smaller SAR tile size:
   ```yaml
   data:
     sar_tile_size: 128  # instead of 256
   ```

### Dataset Not Found

```
FileNotFoundError: runtime/data/train.hdf5
```

**Solution**: Create synthetic dataset or update path in `config.yaml`:

```bash
python create_synthetic_dataset.py
```

### torch-geometric Installation Issues

```
Error: No matching distribution found for torch-scatter
```

**Solution**: Install from PyG wheel index:

```bash
pip install torch-geometric -f https://data.pyg.org/whl/torch-2.1.0+cu121.html
```

Replace `cu121` with your CUDA version (`cu118`, `cpu`, etc.).

### WandB Authentication

```
wandb: ERROR WandB not authenticated
```

**Solution**: Disable WandB or authenticate:

```bash
# Disable WandB
export WANDB_MODE=disabled

# Or authenticate
wandb login
```

### Multi-GPU Communication Error

```
RuntimeError: NCCL error
```

**Solutions**:
1. Check NCCL installation:
   ```bash
   python -c "import torch; print(torch.distributed.is_nccl_available())"
   ```

2. Set NCCL debug level:
   ```bash
   export NCCL_DEBUG=INFO
   ```

3. Use GLOO backend instead:
   ```yaml
   distributed:
     backend: "gloo"
   ```

## Additional Resources

- [PyTorch Installation Guide](https://pytorch.org/get-started/locally/)
- [CUDA Installation Guide](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/)
- [torch-geometric Installation](https://pytorch-geometric.readthedocs.io/en/latest/install/installation.html)
- [Weights & Biases Documentation](https://docs.wandb.ai/)

## Support

For issues and questions:
1. Check troubleshooting section above
2. Review `VALIDATION_REPORT_PHASE_3B1.md`
3. Check GitHub Issues
4. Consult team documentation

---

**Last Updated**: 2026
**Version**: 1.0.0
