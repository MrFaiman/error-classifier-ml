"""
Utility module to detect and configure the best available device (GPU/MPS/CPU)
for embedding models.
"""
import torch
import platform


def get_best_device():
    """
    Detect the best available device for running models.
    
    Returns:
        str: 'mps' for Apple Silicon, 'cuda' for NVIDIA GPU, 'cpu' otherwise
    """
    # Check for Apple Silicon (M1, M2, M3, M4, M5, etc.)
    if platform.system() == 'Darwin' and platform.machine() == 'arm64':
        if torch.backends.mps.is_available():
            print("[Device Detection] Apple Silicon detected - using MPS acceleration")
            return 'mps'
        else:
            print("[Device Detection] Apple Silicon detected but MPS not available - using CPU")
            return 'cpu'
    
    # Check for NVIDIA GPU
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        print(f"[Device Detection] NVIDIA GPU detected ({gpu_name}) - using CUDA acceleration")
        return 'cuda'
    
    # Fallback to CPU
    print("[Device Detection] No GPU detected - using CPU")
    return 'cpu'


def get_device_info():
    """
    Get detailed information about the detected device.
    
    Returns:
        dict: Device information including type, name, and availability
    """
    device = get_best_device()
    info = {
        'device': device,
        'platform': platform.system(),
        'machine': platform.machine(),
        'cuda_available': torch.cuda.is_available(),
        'mps_available': torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False
    }
    
    if device == 'cuda':
        info['gpu_name'] = torch.cuda.get_device_name(0)
        info['gpu_count'] = torch.cuda.device_count()
    
    return info
