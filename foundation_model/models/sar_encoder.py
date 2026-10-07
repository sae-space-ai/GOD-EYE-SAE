"""
SAR Encoder - U-Net based architecture for SAR backscatter encoding.

Processes SLC (Single Look Complex) SAR images with amplitude and phase channels.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)


class ResidualBlock(nn.Module):
    """Residual block with two convolutions."""
    
    def __init__(self, channels: int) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(channels)
        self.relu = nn.ReLU(inplace=True)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        return self.relu(out + residual)


class UNetEncoderBlock(nn.Module):
    """Encoder block: convolutions + downsampling."""
    
    def __init__(self, in_channels: int, out_channels: int, use_residual: bool = True) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.pool = nn.MaxPool2d(2)
        self.use_residual = use_residual
        
        if use_residual:
            self.residual = ResidualBlock(out_channels)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            skip: features before pooling (for skip connections)
            out: downsampled features
        """
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.relu(self.bn2(self.conv2(x)))
        
        if self.use_residual:
            x = self.residual(x)
        
        skip = x
        out = self.pool(x)
        return skip, out


class UNetDecoderBlock(nn.Module):
    """Decoder block: upsampling + skip connection + convolutions."""
    
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


class UNetEncoder(nn.Module):
    """
    4-level U-Net encoder for SAR images.
    
    Processes SLC amplitude + phase (2 input channels).
    """
    
    def __init__(
        self,
        in_channels: int = 2,
        encoder_channels: list[int] = [64, 128, 256, 512],
        use_residual: bool = True
    ) -> None:
        """
        Args:
            in_channels: Input channels (amplitude + phase = 2)
            encoder_channels: Output channels at each level
            use_residual: Whether to use residual connections
        """
        super().__init__()
        
        self.levels = nn.ModuleList()
        ch_in = in_channels
        
        for ch_out in encoder_channels:
            self.levels.append(UNetEncoderBlock(ch_in, ch_out, use_residual))
            ch_in = ch_out
        
        self.bottleneck = nn.Sequential(
            nn.Conv2d(encoder_channels[-1], encoder_channels[-1], 3, padding=1),
            nn.BatchNorm2d(encoder_channels[-1]),
            nn.ReLU(inplace=True)
        )
        
        self.output_dim = encoder_channels[-1]
        
        logger.info(
            f"U-Net encoder initialized: levels={len(encoder_channels)}, "
            f"output_dim={self.output_dim}"
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, List[torch.Tensor]]:
        """
        Args:
            x: (B, 2, H, W) SAR image (amplitude + phase)
            
        Returns:
            bottleneck: (B, C_bottleneck, H', W') bottleneck features
            skips: list of skip connection features
        """
        skips = []
        
        for level in self.levels:
            skip, x = level(x)
            skips.append(skip)
        
        bottleneck = self.bottleneck(x)
        
        return bottleneck, skips
