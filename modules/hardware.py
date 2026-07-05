import platform
from typing import Any


def _import_torch_module(torch_module: Any = None) -> Any:
    if torch_module is not None:
        return torch_module

    try:
        import torch  # type: ignore
    except Exception:
        return None
    return torch


def classify_runtime_backend(torch_module: Any = None, platform_name: str | None = None, directml_available: bool = False) -> dict[str, Any]:
    torch_mod = _import_torch_module(torch_module)
    current_platform = (platform_name or platform.system() or "Unknown").strip() or "Unknown"

    if directml_available:
        return {
            "backend": "directml",
            "support": "supported",
            "platform": current_platform,
            "notes": "Windows/DirectML path is now treated as a first-class backend with explicit troubleshooting guidance.",
        }

    if torch_mod is not None:
        version = getattr(torch_mod, "version", None)
        if getattr(version, "hip", None):
            return {
                "backend": "rocm",
                "support": "supported",
                "platform": current_platform,
                "notes": "ROCm detected via torch.version.hip; prefer Linux + ROCm-compatible torch wheels for best results.",
            }

        try:
            mps_backend = getattr(getattr(torch_mod, "backends", None), "mps", None)
            if mps_backend is not None and mps_backend.is_available():
                return {
                    "backend": "mps",
                    "support": "supported",
                    "platform": current_platform,
                    "notes": "Apple Silicon MPS detected; expect shared memory behavior and slower throughput than CUDA.",
                }
        except Exception:
            pass

        try:
            if getattr(torch_mod.cuda, "is_available", lambda: False)():
                return {
                    "backend": "cuda",
                    "support": "supported",
                    "platform": current_platform,
                    "notes": "CUDA detected; this remains the default high-performance path for compatible NVIDIA GPUs.",
                }
        except Exception:
            pass

    return {
        "backend": "cpu",
        "support": "supported",
        "platform": current_platform,
        "notes": "No CUDA/ROCm/MPS/DirectML runtime was detected; the fallback is CPU execution.",
    }


def get_backend_compatibility_matrix() -> dict[str, dict[str, Any]]:
    return {
        "cuda": {
            "support": "supported",
            "platforms": ["Linux", "Windows"],
            "notes": "Recommended for NVIDIA GPUs with a compatible PyTorch build and sufficient VRAM.",
            "install_hint": "Use the standard CUDA-enabled torch build from the project's requirements.",
        },
        "rocm": {
            "support": "supported",
            "platforms": ["Linux"],
            "notes": "Best on Linux with AMD GPUs and ROCm-compatible PyTorch wheels; Windows ROCm is not a first-class target here.",
            "install_hint": "Install ROCm-compatible torch/torchvision wheels and verify the ROCm runtime is available.",
        },
        "directml": {
            "support": "supported",
            "platforms": ["Windows"],
            "notes": "Use the --directml launch path for Windows DirectML-capable GPUs when CUDA is unavailable.",
            "install_hint": "Install torch-directml and launch with --directml.",
        },
        "mps": {
            "support": "supported",
            "platforms": ["macOS"],
            "notes": "Supported for Apple Silicon Macs with MPS, but performance and memory behavior differ from CUDA.",
            "install_hint": "Use the default Apple Silicon PyTorch build and keep enough free system memory.",
        },
    }


def get_runtime_backend_banner(torch_module: Any = None, platform_name: str | None = None, directml_available: bool = False) -> str:
    info = classify_runtime_backend(torch_module=torch_module, platform_name=platform_name, directml_available=directml_available)
    return f"Runtime backend: {info['backend']} ({info['support']}) - {info['notes']}"
