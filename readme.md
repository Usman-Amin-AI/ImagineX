# ImagineX

[ **Click Here to Install ImagineX** ](#download)

**ImagineX** is an independently maintained fork of the public Fooocus image-generation project, developed and led by **Usman Amin**. It is built from the existing Fooocus codebase but is not presented as a copy or rebrand-only clone. Instead, it preserves the familiar Fooocus WebUI workflow while extending it with its own deployment model, API capabilities, queueing, safety controls, backend flexibility, and container support.

> [!IMPORTANT]
> This repository is a modified and extended fork of the public Fooocus GitHub project. It is maintained under the ImagineX brand by Usman Amin, with its own support scope, roadmap, and deployment focus. The goal is to provide a stronger, more production-oriented image-generation platform than a basic upstream clone.
>
> This project is protected as an independently maintained work by Usman Amin. You may use it for your own daily work and internal tasks, but you may not copy, paste, repackage, or claim it as your own project without permission.

>  **Beware of fake websites claiming to be Fooocus or ImagineX.** The only official source is this GitHub page.

---

##  Project Status

**ImagineX is actively maintained as a differentiated, owner-led project** with its own deployment, API, queue, and safety-focused direction. It is intended to be used as a self-managed creative platform rather than treated as a generic upstream clone.

For newer models like **Flux**, try:
- [WebUI Forge](https://github.com/lllyasviel/stable-diffusion-webui-forge)
- [ComfyUI / SwarmUI](https://github.com/comfyanonymous/ComfyUI)
- [Community Forks](https://github.com/lllyasviel/Fooocus?tab=readme-ov-file#forks)

---

##  About ImagineX

ImagineX is a self-managed image generation platform built and maintained by **Usman Amin**. It is designed for users who want a familiar, high-quality generation workflow without depending on a generic upstream experience.

This project is not merely a renamed copy of the old Fooocus project. It is a modified, extended, and owner-led distribution focused on:
- a more production-friendly API experience,
- queue-based job orchestration,
- broader deployment flexibility,
- safety controls,
- and a cleaner path to private or team use.

##  Features

## Why ImagineX is Better

ImagineX is designed to be more than a simple image-generation UI. It is built as a stronger, more practical platform for real-world use by offering:

- a cleaner deployment experience with Docker and Docker Compose,
- headless API support for automation and integration,
- queue-based job handling for shared or multi-user environments,
- flexible backend selection for different hardware setups,
- optional safety filtering for more controlled usage,
- and a clear owner-led identity under Usman Amin.

This makes ImagineX more suitable for private projects, team workflows, automation, and long-term ownership than a basic upstream clone.


| Midjourney Feature | Fooocus Equivalent |
|--------------------|---------------------|
| Text-to-image with minimal prompt tuning | GPT-2 based prompt processor |
| V1–V4 Variations | Upscale / Variation / Vary Subtle / Strong |
| U1–U4 Upscaling | Upscale to 1.5x or 2x |
| Inpaint / Pan | Built-in inpainting models |
| Image Prompt | Enhanced algorithmic support |
| --style | Style configuration in Advanced |
| --no | Negative prompts |
| --ar | Aspect ratio setting |
| Prompt weights | `(word:1.5)` format |
| Describe image | Use Describe tool |
| ControlNet | Advanced image prompt control |
| InsightFace | FaceSwap with tools |

More in [Advanced Features](https://github.com/lllyasviel/Fooocus/discussions/117)

---

##  Queue & Shared Deployments

For small-team shared deployments, the API can use a queue layer for fair scheduling across available GPUs. Configure:

- `IMAGINEX_QUEUE_BACKEND=redis` for Redis-backed job storage, or leave it as `memory` for local/dev use.
- `IMAGINEX_REDIS_URL=redis://redis:6379/0` when Redis is available.
- `IMAGINEX_GPU_COUNT=2` to start a matching number of worker threads.

Jobs can be polled with `/v1/jobs/{job_id}` while queued work is processed in the background.

---

##  Download & Install

###  Windows (NVIDIA)

1. Clone or download this ImagineX repository.
2. Extract the archive if needed.
3. Run `run.bat`.
4. Wait for model downloads.

> 🛠 Requires **4GB VRAM (NVIDIA)** and **8GB RAM**

#### Optional Presets:
- `run.bat` – Default
- `run_anime.bat` – Anime
- `run_realistic.bat` – Realistic


###  Linux (Anaconda)

```bash
git clone <your-imaginex-repository-url>
cd ImagineX
conda env create -f environment.yaml
conda activate fooocus
pip install -r requirements_versions.txt
python entry_with_update.py
```

###  Linux (Python venv)

```bash
git clone <your-imaginex-repository-url>
cd ImagineX
python3 -m venv fooocus_env
source fooocus_env/bin/activate
pip install -r requirements_versions.txt
python entry_with_update.py
```

###  AMD GPU (Windows/Linux)

```bash
pip uninstall torch torchvision torchaudio
pip install torch-directml  # Windows
# OR
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.6  # Linux

python entry_with_update.py --directml --preset anime
```

>  ROCm and DirectML are now treated as supported backend paths with explicit guidance and smoke tests.

###  Apple Silicon (macOS)

```bash
pip install -r requirements_versions.txt
python entry_with_update.py
```

>  Apple Silicon/MPS is now documented as a supported backend path for compatible Macs; expect shared-memory behavior and slower throughput than CUDA.

### Compatibility matrix

| Backend | Status | Recommended target | Notes |
| --- | --- | --- | --- |
| CUDA | Supported | NVIDIA GPUs | Default high-performance path for compatible hardware. |
| ROCm | Supported | Linux + AMD GPUs | Prefer ROCm-compatible PyTorch wheels and enough system memory. |
| DirectML | Supported | Windows + DirectML GPUs | Use the --directml launch path when CUDA is unavailable. |
| MPS | Supported | Apple Silicon Macs | Works on MPS-capable Macs, but memory behavior differs from CUDA. |
| CPU | Supported | Any machine | Fallback mode; generation will be slower and less capable. |

---

##  Troubleshooting

- **Corrupted models** → Re-download model files
- **RuntimeError: CPUAllocator** → Enable swap memory
- **Slow generation?** → Try NVIDIA driver v531

More: [Troubleshooting Guide](https://github.com/lllyasviel/Fooocus/blob/main/docs/troubleshoot.md)

---

##  Screenshots

<img src="https://github.com/lllyasviel/Fooocus/assets/19834515/938737a5-b105-4f19-b051-81356cb7c495" width="600">

---

##  Maintained By

### Usman Amin | Founder of ImagineX

<table style="width: 100%; margin-top: 15px; border-collapse: collapse;">
    <tr style="background-color: #64B5F6; color: #ffffff;">
        <th style="padding: 8px;">Name</th>
        <th style="padding: 8px;">Email</th>
        <th style="padding: 8px;">LinkedIn</th>
        <th style="padding: 8px;">GitHub</th>
        <th style="padding: 8px;">Kaggle</th>
        <th style="padding: 8px;">WhatsApp</th>
    </tr>
    <tr style="background-color: #FFFFFF; color: #000000;">
        <td style="padding: 8px;">Usman Amin</td>
        <td style="padding: 8px;">usmanamin.ai.dev@gmail.com</td>
        <td style="padding: 8px;">
            <a href="https://www.linkedin.com/in/usman-amin-ai/" target="_blank">
                <img src="https://img.shields.io/badge/LinkedIn-0e76a8.svg?style=for-the-badge&logo=LinkedIn&logoColor=white" alt="LinkedIn Badge">
            </a>
        </td>
        <td style="padding: 8px;">
            <a href="https://github.com/Usman-Amin-AI" target="_blank">
                <img src="https://img.shields.io/badge/GitHub-171515.svg?style=for-the-badge&logo=GitHub&logoColor=white" alt="GitHub Badge">
            </a>
        </td>
        <td style="padding: 8px;">
            <a href="https://www.kaggle.com/usmanamin01" target="_blank">
                <img src="https://img.shields.io/badge/Kaggle-20beff.svg?style=for-the-badge&logo=Kaggle&logoColor=white" alt="Kaggle Badge">
            </a>
        </td>
           </a>
        </td>
        <td style="padding: 8px;">
            <a href="https://wa.me/923183007566" target="_blank">
                <img src="https://img.shields.io/badge/WhatsApp-25D366.svg?style=for-the-badge&logo=WhatsApp&logoColor=white" alt="WhatsApp Badge">
            </a>
        </td>
    </tr>
</table>
