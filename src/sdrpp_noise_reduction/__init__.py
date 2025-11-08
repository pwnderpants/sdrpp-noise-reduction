"""SDR++ Noise Reduction - Processes network radio audio from SDR++ via UDP with noise reduction."""

__version__ = "0.1.0"

from .config import NoiseReductionConfig
from .cli import main

__all__ = ['NoiseReductionConfig', 'main']
