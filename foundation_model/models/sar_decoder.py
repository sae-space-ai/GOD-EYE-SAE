"""
SAR Decoder - Reconstructs SLC images from latent representation.

Produces amplitude + phase channels.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List
import logging

logger = logging.getLogger(__name__)


class UNetDecoderBlock(nn.Module):
    """Decoder block with upsampling and skip connections."""
    
    def __init__(self, in_channels: int, skip_channels: int, out_channels: int) -> None:
        super().__init__()
        self.up = nn.ConvTranspose2d(in_channels, out_channels, 2, stride=2)
        self.conv1 = nn.Conv2d(out_channels + skip_channels, out_channels, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
    
    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = self.up(x)
        
        # Handle size mismatch
        if x.shape != skip.shape:
            x = F.interpolate(x, size=skip.shape[2:], mode='bilinear', align_corners=False)
        
        x = torch.cat([x, skip], dim=1)
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.relu(self.bn2(self.conv2(x)))
        return x


class SARDecoder(nn.Module):
    """
    U-Net decoder for SAR SLC reconstruction.
    
    Produces amplitude + phase (2 output channels).
    """
    
    def __init__(
        self,
        latent_channels: int = 512,
        decoder_channels: list[int] = [256, 128, 64],
        skip_channels: list[int] = [256, 128, 64],
        output_channels: int = 4  # VV real, VV imag, VH real, VH imag (dual-pol)
    ) -> None:
        """
        Args:
            latent_channels: Input channels from bottleneck
            decoder_channels: Output channels at each decoder level
            skip_channels: Skip connection channels from encoder
            output_channels: Output channels (amplitude + phase)
        """
        super().__init__()
        
        self.levels = nn.ModuleList()
        in_ch = latent_channels
        
        for i, out_ch in enumerate(decoder_channels):
            skip_ch = skip_channels[i] if i < len(skip_channels) else out_ch
            self.levels.append(UNetDecoderBlock(in_ch, skip_ch, out_ch))
            in_ch = out_ch
        
        # Final output layer
        self.output_conv = nn.Conv2d(decoder_channels[-1], output_channels, 1)
        
        logger.info(
            f"SAR decoder initialized: levels={len(decoder_channels)}, "
            f"output_channels={output_channels}"
        )
    
    def forward(
        self,
        z: torch.Tensor,
        skips: List[torch.Tensor]
    ) -> torch.Tensor:
        """
        Decode latent representation into SAR SLC.
        
        Args:
            z: (B, C, H, W) bottleneck features
            skips: list of skip connection features from encoder
            
        Returns:
            slc: (B, 2, H, W) reconstructed SLC (amplitude + phase)
        """
        x = z
        
        # Decoder path with skip connections
        for i, level in enumerate(self.levels):
            skip = skips[-(i + 1)] if i < len(skips) else None
            if skip is not None:
                x = level(x, skip)
            else:
                # No skip connection, just upsample
                x = F.interpolate(x, scale_factor=2, mode='bilinear', align_corners=False)
                x = level.up(x)
        
        # Final output
        slc = self.output_conv(x)  # (B, 2, H, W)
        
        return slc
