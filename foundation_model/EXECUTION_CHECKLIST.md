# Execution Checklist

Pre-flight checklist for GOD EYE SAE Foundation Model execution.

## Status Legend

- ✅ **READY** - Component is configured and validated
- ⚠️ **NOT CONFIGURED** - Component needs setup
- 🔒 **EXTERNAL** - Requires external resource/credentials
- 🚫 **BLOCKED** - Cannot proceed without resolution

---

## 1. Python Environment

### 1.1 Python Installation

- [ ] Python 3.11 installed
- [ ] Python version verified: `python --version`
- [ ] Python added to PATH

**Command**: `python --version`
**Expected**: `Python 3.11.x`
**Status**: ⚠️ NOT VERIFIED

### 1.2 Virtual Environment

- [ ] Virtual environment created
- [ ] Virtual environment activated
- [ ] Using isolated environment (not global)

**Commands**:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\Activate.ps1  # Windows
```
**Status**: ⚠️ NOT CONFIGURED

### 1.3 Dependencies

- [ ] PyTorch installed (correct version for CUDA/CPU)
- [ ] torchvision installed
- [ ] torch-geometric installed
- [ ] All requirements.txt dependencies installed
- [ ] No dependency conflicts

**Command**: `pip list | grep -E "torch|omegaconf|h5py"`
**Status**: ⚠️ NOT CONFIGURED

---

## 2. Hardware

### 2.1 CPU

- [ ] CPU identified
- [ ] Sufficient RAM (8GB+ recommended)
- [ ] Multi-core available

**Command**: `python hardware_profile.py`
**Status**: ⚠️ NOT VERIFIED

### 2.2 GPU (Optional)

- [ ] NVIDIA GPU detected (if applicable)
- [ ] NVIDIA driver installed
- [ ] CUDA toolkit installed
- [ ] cuDNN installed
- [ ] GPU memory sufficient (8GB+ VRAM)

**Command**: `nvidia-smi`
**Status**: ⚠️ NOT VERIFIED

### 2.3 CUDA

- [ ] CUDA available (if GPU training)
- [ ] CUDA version compatible with PyTorch
- [ ] BF16 support verified (if using BF16)

**Command**: `python -c "import torch; print(torch.cuda.is_available())"`
**Status**: ⚠️ NOT VERIFIED

---

## 3. Configuration

### 3.1 Config File

- [ ] config.yaml exists
- [ ] config.yaml validated
- [ ] All required fields present
- [ ] No configuration errors

**Command**: `python validate_config.py`
**Status**: ⚠️ NOT VERIFIED

### 3.2 Model Architecture

- [ ] latent_dim configured (default: 256)
- [ ] num_heads configured (default: 8)
- [ ] latent_dim divisible by num_heads
- [ ] LiDAR encoder configured
- [ ] SAR encoder configured
- [ ] Fusion transformer configured

**Status**: ⚠️ NOT VERIFIED

### 3.3 Training Parameters

- [ ] batch_size configured (default: 8)
- [ ] learning_rate configured (default: 3e-4)
- [ ] epochs configured (default: 200)
- [ ] gradient_accumulation_steps configured (default: 4)
- [ ] Mask ratios configured (LiDAR: 0.75, SAR: 0.60)

**Status**: ⚠️ NOT VERIFIED

### 3.4 SAR Representation

- [ ] sar_representation configured (default: dual_pol_real_imag)
- [ ] sar_channels matches representation (4 for dual-pol)
- [ ] Channels: VV_real, VV_imag, VH_real, VH_imag

**Status**: ⚠️ NOT VERIFIED

---

## 4. Dataset

### 4.1 Dataset Files

- [ ] Training dataset exists
- [ ] Validation dataset exists
- [ ] Test dataset exists
- [ ] Dataset paths configured in config.yaml

**Command**: `python inspect_dataset.py <dataset_path>`
**Status**: 🔒 EXTERNAL (requires real dataset)

### 4.2 Dataset Format

- [ ] HDF5 format
- [ ] Contains lidar_points key
- [ ] Contains sar_slc key
- [ ] LiDAR shape: (N, 4) - x, y, z, intensity
- [ ] SAR shape: (4, H, W) - dual-pol real/imag
- [ ] No NaN values
- [ ] No Inf values

**Command**: `python validate_dataset.py <dataset_path>`
**Status**: 🔒 EXTERNAL (requires real dataset)

### 4.3 Synthetic Dataset (for testing)

- [ ] Synthetic dataset created
- [ ] Synthetic dataset validated
- [ ] Paths updated in config.yaml (if using synthetic)

**Command**: `python create_synthetic_dataset.py`
**Status**: ⚠️ NOT CONFIGURED

---

## 5. Storage

### 5.1 Directories

- [ ] Checkpoint directory exists
- [ ] Log directory exists
- [ ] Output directory exists
- [ ] Write permissions verified

**Directories**:
```
foundation_model/runtime/
├── checkpoints/
├── logs/
├── outputs/
└── data/
```
**Status**: ⚠️ NOT CONFIGURED

### 5.2 Disk Space

- [ ] Sufficient disk space for checkpoints
- [ ] Sufficient disk space for logs
- [ ] Sufficient disk space for dataset

**Command**: `df -h` (Linux) or check disk properties (Windows)
**Status**: ⚠️ NOT VERIFIED

---

## 6. Weights & Biases (Optional)

### 6.1 WandB Configuration

- [ ] WandB installed
- [ ] WandB authenticated (or disabled)
- [ ] Project name configured
- [ ] Entity configured (if using team)

**Commands**:
```bash
# Authenticate
wandb login

# Or disable
export WANDB_MODE=disabled
```
**Status**: 🔒 EXTERNAL (requires credentials)

---

## 7. Distributed Training (Optional)

### 7.1 Multi-GPU Setup

- [ ] Multiple GPUs available
- [ ] NCCL installed (Linux)
- [ ] NCCL backend configured
- [ ] torchrun available

**Command**: `torchrun --version`
**Status**: ⚠️ NOT VERIFIED

### 7.2 DDP Configuration

- [ ] distributed.backend configured (nccl/gloo)
- [ ] WORLD_SIZE set correctly
- [ ] LOCAL_RANK handled
- [ ] RANK handled

**Status**: ⚠️ NOT CONFIGURED

---

## 8. Validation

### 8.1 Environment Check

- [ ] `check_environment.py` executed
- [ ] All critical components PASS
- [ ] No FAIL status

**Command**: `python check_environment.py`
**Status**: ⚠️ NOT EXECUTED

### 8.2 Configuration Validation

- [ ] `validate_config.py` executed
- [ ] Configuration is valid
- [ ] No errors

**Command**: `python validate_config.py`
**Status**: ⚠️ NOT EXECUTED

### 8.3 Unit Tests

- [ ] pytest installed
- [ ] All tests pass
- [ ] No test failures

**Command**: `pytest tests/ -v`
**Status**: ⚠️ NOT EXECUTED

### 8.4 Phase 3B.1 Validation

- [ ] `validate_phase3b1.py` executed
- [ ] Validation report generated
- [ ] All critical criteria PASS
- [ ] No FAIL status

**Command**: `python validate_phase3b1.py`
**Status**: ⚠️ NOT EXECUTED

---

## 9. Training

### 9.1 Smoke Test

- [ ] Smoke test executed
- [ ] 1 epoch completed
- [ ] 10 steps completed
- [ ] No errors

**Command**: `python train.py --config config.yaml --smoke-test`
**Status**: ⚠️ NOT EXECUTED

### 9.2 Full Training

- [ ] Dataset ready
- [ ] Configuration validated
- [ ] Phase 3B.1 validation PASSED
- [ ] Sufficient compute resources
- [ ] WandB configured (optional)
- [ ] Checkpoint directory ready

**Command**: `python train.py --config config.yaml`
**Status**: 🚫 BLOCKED (requires Phase 3B.1 PASS)

### 9.3 Resume Training

- [ ] Checkpoint exists
- [ ] Resume flag set
- [ ] Configuration unchanged

**Command**: `python train.py --config config.yaml --resume checkpoint.pt`
**Status**: ⚠️ NOT CONFIGURED

---

## 10. Post-Training

### 10.1 Checkpoints

- [ ] Best checkpoint saved
- [ ] Last checkpoint saved
- [ ] Checkpoint contains model state
- [ ] Checkpoint contains optimizer state
- [ ] Checkpoint contains config

**Status**: ⚠️ NOT EXECUTED

### 10.2 Logs

- [ ] Training logs saved
- [ ] WandB logs synced (if enabled)
- [ ] Loss curves reviewed
- [ ] Metrics reviewed

**Status**: ⚠️ NOT EXECUTED

### 10.3 Evaluation

- [ ] Validation metrics computed
- [ ] Test metrics computed
- [ ] Confusion matrix generated (if applicable)
- [ ] Results documented

**Status**: ⚠️ NOT EXECUTED

---

## Quick Start Commands

### CPU Validation

```bash
# 1. Setup
python -m venv .venv
source .venv/bin/activate
pip install torch==2.1.0+cpu torchvision==0.16.0+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html
pip install -r requirements.txt

# 2. Validate
python check_environment.py
python validate_config.py
python create_synthetic_dataset.py
pytest tests/ -v
python validate_phase3b1.py --overfit-steps 10
```

### GPU Training

```bash
# 1. Setup
python -m venv .venv
source .venv/bin/activate
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

# 2. Validate
python check_environment.py
python validate_config.py
python hardware_profile.py

# 3. Prepare dataset
# (Place real dataset in runtime/data/)

# 4. Smoke test
python train.py --config config.yaml --smoke-test

# 5. Full training (after Phase 3B.1 PASS)
python train.py --config config.yaml
```

### Multi-GPU DDP

```bash
# 1. Setup (same as GPU training)

# 2. Validate
python check_environment.py
python hardware_profile.py

# 3. Train with torchrun
torchrun --nproc_per_node=4 train.py --config config.yaml
```

---

## Checklist Summary

| Category | Items | Ready | Not Configured | External | Blocked |
|----------|-------|-------|----------------|----------|---------|
| Python Environment | 3 | 0 | 3 | 0 | 0 |
| Hardware | 3 | 0 | 3 | 0 | 0 |
| Configuration | 4 | 0 | 4 | 0 | 0 |
| Dataset | 3 | 0 | 1 | 2 | 0 |
| Storage | 2 | 0 | 2 | 0 | 0 |
| WandB | 1 | 0 | 0 | 1 | 0 |
| Distributed | 2 | 0 | 2 | 0 | 0 |
| Validation | 4 | 0 | 4 | 0 | 0 |
| Training | 3 | 0 | 1 | 0 | 2 |
| Post-Training | 3 | 0 | 3 | 0 | 0 |
| **TOTAL** | **28** | **0** | **23** | **3** | **2** |

---

## Next Steps

1. **Complete all "NOT CONFIGURED" items**
2. **Provide external resources (dataset, WandB credentials)**
3. **Resolve blocked items (Phase 3B.1 validation)**
4. **Execute validation steps**
5. **Proceed to training**

---

**Last Updated**: 2026
**Version**: 1.0.0
