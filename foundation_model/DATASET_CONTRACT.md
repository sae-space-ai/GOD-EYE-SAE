# Dataset Contract

Specification for LiDAR-SAR dataset format used by GOD EYE SAE Foundation Model.

## Overview

This document defines the exact format, structure, and requirements for datasets used to train and evaluate the LiDAR-SAR foundation model.

**Version**: 1.0.0
**Last Updated**: 2026

---

## Format Specification

### File Format

- **Format**: HDF5 (Hierarchical Data Format)
- **Extension**: `.hdf5` or `.h5`
- **Library**: h5py (Python)

### Required Keys

The dataset must contain the following top-level keys:

1. **`lidar_points`** - LiDAR point clouds
2. **`sar_slc`** - SAR SLC images

### Optional Keys

- **`labels`** - Classification labels (for downstream tasks)
- **`metadata`** - Dataset metadata
- **`sample_ids`** - Unique sample identifiers

---

## LiDAR Specification

### Key: `lidar_points`

**Type**: Variable-length dataset (ragged array)

**Shape**: `(N,)` where each element is `(num_points, 4)`

**Dtype**: `float32`

**Channels** (4):
1. **x** - X coordinate (meters)
2. **y** - Y coordinate (meters)
3. **z** - Z coordinate (meters)
4. **intensity** - Return intensity (normalized, typically [0, 1])

### Requirements

- **Minimum points per sample**: 16 (for KNN with k=16)
- **Maximum points per sample**: No limit (but consider memory)
- **Coordinate system**: Local Cartesian (meters)
- **Intensity range**: [0, 1] or application-specific

### Example

```python
import h5py
import numpy as np

# Create dataset
with h5py.File('train.hdf5', 'w') as f:
    # Variable-length dtype
    lidar_dtype = h5py.special_dtype(vlen=np.dtype('float32'))
    lidar_ds = f.create_dataset('lidar_points', (100,), dtype=lidar_dtype)
    
    # Add samples
    for i in range(100):
        num_points = np.random.randint(64, 256)
        points = np.random.randn(num_points, 4).astype(np.float32)
        points[:, :3] *= 10.0  # Scale coordinates
        points[:, 3] = np.abs(points[:, 3]) / 10.0  # Intensity [0, 1]
        lidar_ds[i] = points
```

---

## SAR Specification

### Key: `sar_slc`

**Type**: Fixed-size array

**Shape**: `(N, C, H, W)` where:
- `N` = number of samples
- `C` = number of channels (4 for dual-pol)
- `H` = height (pixels)
- `W` = width (pixels)

**Dtype**: `float32`

### Dual-Polarization Real/Imaginary (Default)

**Channels** (4):
1. **VV_real** - VV polarization, real component
2. **VV_imag** - VV polarization, imaginary component
3. **VH_real** - VH polarization, real component
4. **VH_imag** - VH polarization, imaginary component

**Value Range**: Typically [-1, 1] after normalization, but can vary

### Single-Polarization Amplitude/Phase (Alternative)

**Channels** (2):
1. **amplitude** - Amplitude (non-negative)
2. **phase** - Phase in radians [-π, π]

**Note**: This mode is supported but not recommended for production.

### Requirements

- **Tile size**: Typically 64x64, 128x128, or 256x256 pixels
- **Resolution**: 10m ground resolution (Sentinel-1 equivalent)
- **Polarization**: Dual-pol VV+VH preferred
- **Representation**: Complex (real/imaginary) preferred over amplitude/phase

### Example

```python
import h5py
import numpy as np

# Create dataset
with h5py.File('train.hdf5', 'w') as f:
    # Fixed-size array
    N = 100
    C = 4  # Dual-pol real/imag
    H = 64
    W = 64
    
    sar_ds = f.create_dataset('sar_slc', (N, C, H, W), dtype=np.float32)
    
    # Add samples
    for i in range(N):
        # Generate synthetic SAR (real/imag)
        sar = np.random.randn(C, H, W).astype(np.float32) * 0.1
        sar_ds[i] = sar
```

---

## Conversion Utilities

### Complex to Amplitude/Phase

```python
import numpy as np

def complex_to_amp_phase(sar_slc):
    """
    Convert dual-pol real/imag to amplitude/phase.
    
    Args:
        sar_slc: (N, 4, H, W) with channels [VV_real, VV_imag, VH_real, VH_imag]
    
    Returns:
        vv_amp, vv_phase, vh_amp, vh_phase: Each (N, 1, H, W)
    """
    vv_real = sar_slc[:, 0:1]
    vv_imag = sar_slc[:, 1:2]
    vh_real = sar_slc[:, 2:3]
    vh_imag = sar_slc[:, 3:4]
    
    eps = 1e-8
    vv_amp = np.sqrt(vv_real**2 + vv_imag**2 + eps)
    vv_phase = np.arctan2(vv_imag, vv_real)
    vh_amp = np.sqrt(vh_real**2 + vh_imag**2 + eps)
    vh_phase = np.arctan2(vh_imag, vh_real)
    
    return vv_amp, vv_phase, vh_amp, vh_phase
```

### Amplitude/Phase to Complex

```python
def amp_phase_to_complex(vv_amp, vv_phase, vh_amp, vh_phase):
    """
    Convert amplitude/phase to dual-pol real/imag.
    
    Args:
        vv_amp, vv_phase: (N, 1, H, W) VV polarization
        vh_amp, vh_phase: (N, 1, H, W) VH polarization
    
    Returns:
        sar_slc: (N, 4, H, W) with channels [VV_real, VV_imag, VH_real, VH_imag]
    """
    vv_real = vv_amp * np.cos(vv_phase)
    vv_imag = vv_amp * np.sin(vv_phase)
    vh_real = vh_amp * np.cos(vh_phase)
    vh_imag = vh_amp * np.sin(vh_phase)
    
    return np.concatenate([vv_real, vv_imag, vh_real, vh_imag], axis=1)
```

---

## Data Quality Requirements

### Mandatory Checks

1. **No NaN values**
   - LiDAR: All coordinates and intensity must be finite
   - SAR: All channels must be finite

2. **No Inf values**
   - LiDAR: All coordinates and intensity must be finite
   - SAR: All channels must be finite

3. **Valid shapes**
   - LiDAR: Each sample must have shape `(num_points, 4)`
   - SAR: Each sample must have shape `(C, H, W)`

4. **Minimum point count**
   - LiDAR: Each sample must have at least 16 points

### Validation Script

```bash
python validate_dataset.py <dataset_path>
```

This script checks:
- Required keys exist
- Shapes are correct
- No NaN/Inf values
- Minimum point count
- Channel consistency

---

## Georegistration Requirements

### Coordinate Systems

**LiDAR**:
- Local Cartesian coordinates (meters)
- Origin: Application-specific
- Z-axis: Typically up (elevation)

**SAR**:
- Pixel coordinates
- Geotransform required for geo-referencing (if available)

### Co-registration

**Critical**: LiDAR and SAR must be spatially aligned.

**Requirements**:
1. Same geographic area
2. Same coordinate reference system (CRS)
3. Pixel-to-point correspondence (within tolerance)

**Note**: Simple image resizing is NOT co-registration. Proper georegistration requires:
- CRS metadata
- Tile bounds
- Pixel transform
- Acquisition timestamp alignment

### Metadata (Recommended)

Store georegistration metadata in HDF5 attributes:

```python
with h5py.File('train.hdf5', 'w') as f:
    # Dataset-level metadata
    f.attrs['crs'] = 'EPSG:32632'  # UTM zone 32N
    f.attrs['tile_bounds'] = [500000, 5000000, 501000, 5001000]  # [xmin, ymin, xmax, ymax]
    f.attrs['sar_resolution'] = 10.0  # meters
    f.attrs['sar_geotransform'] = [500000, 10, 0, 5001000, 0, -10]
    
    # Sample-level metadata (optional)
    f['lidar_points'].attrs['coordinate_system'] = 'local_cartesian'
    f['sar_slc'].attrs['polarization'] = 'VV+VH'
    f['sar_slc'].attrs['representation'] = 'real_imaginary'
```

---

## Normalization

### LiDAR Normalization

**Coordinates (x, y, z)**:
- Option 1: No normalization (use raw meters)
- Option 2: Normalize to zero mean, unit variance per tile
- Option 3: Normalize to [-1, 1] based on tile bounds

**Intensity**:
- Normalize to [0, 1] if not already

**Recommendation**: Store normalization parameters in metadata for reproducibility.

### SAR Normalization

**Real/Imaginary**:
- Option 1: No normalization (use raw values)
- Option 2: Normalize to zero mean, unit variance per channel
- Option 3: Normalize to [-1, 1] based on dataset statistics

**Amplitude/Phase**:
- Amplitude: Normalize to [0, 1] or zero mean/unit variance
- Phase: Keep in [-π, π] (do NOT normalize as linear variable)

**Recommendation**: Compute statistics on training set, save to `dataset_statistics.json`, apply to validation/test.

### Statistics File

```json
{
  "lidar": {
    "coordinates": {
      "mean": [0.0, 0.0, 5.0],
      "std": [10.0, 10.0, 2.0]
    },
    "intensity": {
      "min": 0.0,
      "max": 1.0
    }
  },
  "sar": {
    "VV_real": {"mean": 0.0, "std": 0.1},
    "VV_imag": {"mean": 0.0, "std": 0.1},
    "VH_real": {"mean": 0.0, "std": 0.08},
    "VH_imag": {"mean": 0.0, "std": 0.08}
  }
}
```

---

## Data Splits

### Split Strategy

**Critical**: Avoid spatial leakage.

**Recommended**: Split by tile or geographic region, NOT by random sampling within tiles.

**Example**:
- Training: Tiles 1-80
- Validation: Tiles 81-90
- Test: Tiles 91-100

**Avoid**:
- Random split within same tile
- Overlapping tiles between splits
- Temporal leakage (same area, different times)

### Split Files

Create separate HDF5 files for each split:

```
data/
├── train.hdf5
├── val.hdf5
└── test.hdf5
```

---

## Example Dataset Structure

### Minimal Dataset

```python
import h5py
import numpy as np

def create_minimal_dataset(output_path, num_samples=100):
    """Create minimal compliant dataset."""
    
    with h5py.File(output_path, 'w') as f:
        # LiDAR (variable-length)
        lidar_dtype = h5py.special_dtype(vlen=np.dtype('float32'))
        lidar_ds = f.create_dataset('lidar_points', (num_samples,), dtype=lidar_dtype)
        
        # SAR (fixed-size)
        sar_ds = f.create_dataset('sar_slc', (num_samples, 4, 64, 64), dtype=np.float32)
        
        # Generate samples
        for i in range(num_samples):
            # LiDAR: 64-256 points, 4 channels
            num_points = np.random.randint(64, 257)
            points = np.random.randn(num_points, 4).astype(np.float32)
            points[:, :3] *= 10.0  # Coordinates in meters
            points[:, 3] = np.abs(points[:, 3]) / 10.0  # Intensity [0, 1]
            lidar_ds[i] = points
            
            # SAR: 4 channels (VV_real, VV_imag, VH_real, VH_imag)
            sar = np.random.randn(4, 64, 64).astype(np.float32) * 0.1
            sar_ds[i] = sar
        
        # Metadata
        f.attrs['num_samples'] = num_samples
        f.attrs['lidar_channels'] = 4
        f.attrs['sar_channels'] = 4
        f.attrs['sar_representation'] = 'dual_pol_real_imag'
        f.attrs['sar_tile_size'] = 64

# Create dataset
create_minimal_dataset('train.hdf5', num_samples=100)
```

---

## Validation Checklist

Before using a dataset, verify:

- [ ] File is valid HDF5
- [ ] Contains `lidar_points` key
- [ ] Contains `sar_slc` key
- [ ] LiDAR shape: `(N,)` with each element `(num_points, 4)`
- [ ] SAR shape: `(N, 4, H, W)` for dual-pol
- [ ] No NaN values in LiDAR
- [ ] No NaN values in SAR
- [ ] No Inf values in LiDAR
- [ ] No Inf values in SAR
- [ ] LiDAR has at least 16 points per sample
- [ ] SAR channels match configuration (4 for dual-pol)
- [ ] LiDAR and SAR are co-registered (if metadata available)
- [ ] Normalization parameters documented (if applicable)
- [ ] Data splits avoid spatial leakage

---

## Tools

### Inspect Dataset

```bash
python inspect_dataset.py train.hdf5
```

### Validate Dataset

```bash
python validate_dataset.py train.hdf5
```

### Create Synthetic Dataset

```bash
python create_synthetic_dataset.py \
  --output runtime/data/synthetic/train.hdf5 \
  --num-train 100 \
  --num-val 20 \
  --num-test 20
```

---

## Common Issues

### Issue: NaN values

**Cause**: Corrupted data or processing error

**Solution**: Check data pipeline, regenerate dataset

### Issue: Shape mismatch

**Cause**: Incorrect dataset structure

**Solution**: Verify LiDAR is `(N, 4)` and SAR is `(4, H, W)`

### Issue: Too few points

**Cause**: Sparse LiDAR or filtering

**Solution**: Ensure minimum 16 points per sample

### Issue: SAR channel mismatch

**Cause**: Using amplitude/phase instead of real/imag

**Solution**: Convert to real/imaginary or update config

---

## References

- HDF5 Documentation: https://www.hdfgroup.org/solutions/hdf5/
- h5py Documentation: https://docs.h5py.org/
- Sentinel-1 SAR: https://sentinel.esa.int/web/sentinel/missions/sentinel-1

---

**Document Version**: 1.0.0
**Last Updated**: 2026
**Maintainer**: GOD EYE SAE Team
