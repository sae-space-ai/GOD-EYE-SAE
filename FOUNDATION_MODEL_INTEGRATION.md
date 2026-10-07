# GOD EYE SAE + Foundation Model Integration

## Overview

GOD EYE SAE now integrates a production-grade multimodal foundation model for LiDAR-SAR fusion, enabling advanced geospatial intelligence capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GOD EYE SAE (Web)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   React UI   │  │  CesiumJS    │  │  Evidence    │      │
│  │   (Spanish)  │  │   Globe      │  │   Engine     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Foundation Model Panel (UI Integration)      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Foundation Model (PyTorch)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ LiDAR Encoder│  │ SAR Encoder  │  │   Fusion     │      │
│  │ (PointNet++) │  │  (U-Net)     │  │ Transformer  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ LiDAR Decoder│  │ SAR Decoder  │  │  Losses      │      │
│  │   (MLP)      │  │  (U-Net)     │  │ (MAE+Contr)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Integration Points

### 1. Web Interface (GOD EYE SAE)

The foundation model is accessible via a dedicated panel in the GOD EYE SAE interface:

- **Location**: Bottom toolbar → "AI Model" button
- **Features**:
  - Model architecture overview
  - Training objectives status
  - Data source specifications
  - Real-time training status

### 2. Data Pipeline

```
Satellite Data → HDF5 Format → Foundation Model → Latent Space → Downstream Tasks
     ↓
LiDAR (N×4) ──┐
              ├─→ Multimodal Autoencoder ─→ z_common (256-dim)
SAR (2×H×W) ──┘
```

### 3. Downstream Applications

The frozen latent space can be used for:

- **Land Cover Classification**: Linear probe on labeled data
- **Change Detection**: Compare latent representations over time
- **Anomaly Detection**: Identify unusual patterns in latent space
- **Data Fusion**: Combine with other GOD EYE SAE data sources

## Usage

### Training the Foundation Model

```bash
cd foundation_model

# Single GPU
python train.py --config config.yaml

# Multi-GPU (4 GPUs)
torchrun --nproc_per_node=4 train.py --config config.yaml
```

### Evaluating on Downstream Tasks

```bash
# Linear probe evaluation
python downstream_eval.py --config config.yaml
```

### Viewing in GOD EYE SAE

1. Open GOD EYE SAE web interface
2. Click "AI Model" button in bottom toolbar
3. View model status, architecture, and training objectives

## Technical Specifications

### Model Architecture

| Component | Specification |
|-----------|---------------|
| **Latent Dimension** | 256 |
| **LiDAR Encoder** | PointNet++ (KNN k=16) |
| **SAR Encoder** | 4-level U-Net (residual) |
| **Fusion** | 4-layer Transformer (8 heads) |
| **Parameters** | ~30M |

### Training Configuration

| Parameter | Value |
|-----------|-------|
| **Batch Size** | 8 tiles |
| **Learning Rate** | 3e-4 |
| **Epochs** | 200 |
| **Precision** | bf16 (mixed) |
| **Gradient Accumulation** | 4 steps |

### Self-Supervised Objectives

1. **Cross-modal MAE**: 75% LiDAR mask, 60% SAR mask
2. **Contrastive Learning**: InfoNCE (τ=0.07)
3. **Decoupled Representation**: DeCUR adversarial
4. **Reconstruction**: L1 + Chamfer + Angular

## Data Requirements

### Input Format

**LiDAR Point Clouds**:
- Shape: `(N, 4)`
- Channels: `(x, y, z, intensity)`
- Density: `<22 pts/m²` (sparse)
- Max points: 8192 (configurable)

**SAR SLC Images**:
- Shape: `(2, H, W)`
- Channels: `(amplitude, phase)`
- Band: C-band (VV+VH polarizations)
- Resolution: 10m ground

### HDF5 Structure

```hdf5
/lidar_points: (N, 4)
/sar_slc: (2, H, W)
/labels: (optional, for downstream tasks)
```

## Performance

### Expected Metrics

- **Training Speed**: ~2 hours/epoch (4× A100 GPUs)
- **Memory**: ~16GB per GPU (batch=8)
- **Inference**: ~50ms per tile pair (single GPU)

### Downstream Evaluation

- **Land Cover Classification**: Expected >85% accuracy (5 classes)
- **Change Detection**: Expected >80% F1-score
- **Zero-shot Transfer**: Latent space usable without fine-tuning

## File Structure

```
foundation_model/
├── config.yaml              # Training configuration
├── train.py                 # Main training script (DDP + AMP)
├── downstream_eval.py       # Linear probe evaluation
├── README.md                # Model documentation
├── models/
│   ├── autoencoder.py       # Complete model
│   ├── lidar_encoder.py     # PointNet++ encoder
│   ├── sar_encoder.py       # U-Net encoder
│   ├── fusion_transformer.py # Cross-attention fusion
│   ├── lidar_decoder.py     # Point cloud decoder
│   ├── sar_decoder.py       # SLC decoder
│   └── linear_probe.py      # Downstream head
├── losses/
│   ├── mae_loss.py          # Cross-modal MAE
│   ├── contrastive.py       # InfoNCE
│   ├── decoupling.py        # DeCUR
│   └── reconstruction.py    # L1 + Chamfer + Angular
├── data/
│   ├── dataset.py           # HDF5 dataset loader
│   ├── augmentations.py     # Modality-specific augments
│   └── collate.py           # Variable-size collation
├── utils/
│   ├── ddp_setup.py         # Distributed training
│   ├── wandb_logger.py      # WandB integration
│   └── chamfer.py           # Chamfer distance
└── tests/
    └── test_autoencoder.py  # Unit tests
```

## Integration with GOD EYE SAE Data Sources

The foundation model can be integrated with existing GOD EYE SAE data sources:

### Current Sources (Compatible)

- **USGS Earthquakes**: Can be used as anomaly labels
- **CelesTrak Satellites**: Orbital parameters for SAR acquisition geometry
- **OpenSky Flights**: LiDAR acquisition planning

### Future Sources (Planned)

- **NASA FIRMS**: Fire detection as change detection labels
- **Sentinel-2**: Optical imagery for multi-modal fusion
- **Copernicus**: Additional SAR data for training

## Security Considerations

- Model weights stored securely (not in git)
- Training data access controlled via HDF5 permissions
- No sensitive data in model architecture
- WandB logging respects privacy settings

## Deployment

### Local Development

```bash
# Install dependencies
pip install torch torchvision omegaconf wandb h5py scikit-learn

# Run tests
pytest foundation_model/tests/

# Start training
cd foundation_model && python train.py
```

### Production Deployment

1. Train model on GPU cluster
2. Export checkpoint: `checkpoint_final.pt`
3. Deploy inference server (FastAPI/Flask)
4. Connect to GOD EYE SAE via REST API
5. Enable real-time analysis in web interface

## Roadmap

### Phase 1 (Current)
- ✅ Model architecture implemented
- ✅ Training pipeline ready
- ✅ Web integration complete
- ✅ Documentation finished

### Phase 2 (Next)
- ⏳ Train on real satellite data
- ⏳ Validate downstream tasks
- ⏳ Deploy inference API
- ⏳ Connect to GOD EYE SAE data sources

### Phase 3 (Future)
- ⏳ Multi-temporal analysis
- ⏳ Real-time change detection
- ⏳ Integration with FIRECYCLE EXTREM
- ⏳ On-board deployment (satellite)

## References

- **OmniSat (2024)**: Cross-modal masked autoencoding inspiration
- **DeCUR (2025)**: Decoupled common/unique representation
- **PointNet++**: Deep hierarchical features on point clouds
- **SimCLR**: Contrastive learning framework

## License

MIT License - See individual file headers for details.

---

**GOD EYE SAE + Foundation Model**
*Advanced Geospatial Intelligence through Multimodal Deep Learning*
