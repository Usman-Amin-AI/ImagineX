from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import base64
import io
from PIL import Image
import modules.default_pipeline as pipeline
import modules.config as config
import modules.flags as flags
import numpy as np
import modules.safety as safety
import threading
import uuid
import time
import os
from modules.api_services import JobStore, require_api_auth
from modules.queue_services import get_queue_manager

app = FastAPI(title="ImagineX API")

API_AUTH_TOKEN = os.environ.get('IMAGINEX_API_TOKEN')
job_store = JobStore()
queue_manager = get_queue_manager()


def _persist_generated_images(images_b64: list[str]) -> None:
    try:
        outdir = config.get_path_output()
        os.makedirs(outdir, exist_ok=True)
        for idx, image_b64 in enumerate(images_b64):
            data = base64.b64decode(image_b64)
            fname = f"img_{int(time.time())}_{uuid.uuid4().hex[:8]}_{idx}.png"
            with open(os.path.join(outdir, fname), 'wb') as handle:
                handle.write(data)
    except Exception:
        pass


def _apply_safety_filter(images_b64: list[str]) -> list[str]:
    if not config.default_enable_safety_checker:
        return images_b64
    try:
        pil_images = [Image.open(io.BytesIO(base64.b64decode(item))).convert('RGB') for item in images_b64]
        safe_images = safety.sanitize_images_for_output(pil_images, enabled=True)
        filtered_b64 = []
        for img in safe_images:
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            filtered_b64.append(base64.b64encode(buf.getvalue()).decode('ascii'))
        return filtered_b64
    except Exception:
        return images_b64


def _run_txt2img_job_payload(job_id: str, payload: dict) -> list[str]:
    queue_manager.update(job_id, status='running', progress=10)
    req = Txt2ImgRequest(**payload)
    steps = req.steps or flags.Steps.SPEED.value if hasattr(flags, 'Steps') else (config.default_cfg_scale)
    cfg_scale = req.cfg_scale if req.cfg_scale is not None else config.default_cfg_scale
    sampler = req.sampler or config.default_sampler
    scheduler = req.scheduler or config.default_scheduler
    base_model = req.base_model or config.default_base_model_name
    width = req.width or 1024
    height = req.height or 1024
    seed = int(req.seed) if req.seed is not None else -1

    pipeline.refresh_everything(refiner_model_name=config.default_refiner_model_name,
                                base_model_name=base_model,
                                loras=[],
                                vae_name=config.default_vae)
    positive = [req.prompt]
    negative = [req.negative_prompt] if req.negative_prompt is not None else ['']
    c = pipeline.clip_encode(texts=positive, pool_top_k=1)
    uc = pipeline.clip_encode(texts=negative, pool_top_k=1)

    images_b64 = []
    for i in range(max(1, req.num_images)):
        image_seed = seed if seed >= 0 else np.random.randint(0, 2 ** 31 - 1)
        imgs = pipeline.process_diffusion(positive_cond=c, negative_cond=uc, steps=req.steps or 30,
                                          switch=config.default_refiner_switch, width=width, height=height,
                                          image_seed=image_seed, callback=lambda *a, **k: None,
                                          sampler_name=sampler, scheduler_name=scheduler,
                                          cfg_scale=cfg_scale, disable_preview=True)
        for img in imgs:
            if isinstance(img, np.ndarray):
                pil = _pil_from_np(img)
            elif isinstance(img, Image.Image):
                pil = img
            else:
                pil = Image.open(img)
            buf = io.BytesIO()
            pil.save(buf, format='PNG')
            images_b64.append(base64.b64encode(buf.getvalue()).decode('ascii'))
    images_b64 = _apply_safety_filter(images_b64)
    _persist_generated_images(images_b64)
    return images_b64


def _run_img2img_job_payload(job_id: str, payload: dict) -> list[str]:
    queue_manager.update(job_id, status='running', progress=10)
    image_b64 = payload.get('image_b64')
    if image_b64 is None:
        raise ValueError('image_b64 required')
    img = _b64_to_pil(image_b64)
    img_np = np.array(img)

    params = {
        'prompt': payload.get('prompt', ''),
        'negative_prompt': payload.get('negative_prompt', ''),
        'steps': payload.get('steps', None),
        'num_images': payload.get('num_images', 1),
        'base_model_name': payload.get('base_model', None),
        'inpaint_input_image': img_np,
        'current_tab': 'ip',
        'inpaint_engine': payload.get('inpaint_engine', config.default_inpaint_engine_version),
        'inpaint_strength': payload.get('denoising_strength', 1.0),
        'disable_preview': True,
    }
    task = __import__('modules.async_worker', fromlist=['create_task_from_params']).create_task_from_params(params)
    while True:
        while len(task.yields) > 0:
            flag, product = task.yields.pop(0)
            if flag == 'preview':
                queue_manager.update(job_id, progress=int(product[0]))
            if flag == 'results':
                images_b64 = []
                for item in product:
                    if isinstance(item, np.ndarray):
                        pil = _pil_from_np(item)
                    elif isinstance(item, Image.Image):
                        pil = item
                    else:
                        pil = Image.open(item)
                    buf = io.BytesIO()
                    pil.save(buf, format='PNG')
                    images_b64.append(base64.b64encode(buf.getvalue()).decode('ascii'))
                images_b64 = _apply_safety_filter(images_b64)
                _persist_generated_images(images_b64)
                return images_b64
        if task.processing is False and len(task.yields) == 0:
            break
        time.sleep(0.1)
    return []


def _process_queue_job(job_id: str, record: dict) -> None:
    payload = record.get('payload', {}) or {}
    task = record.get('task', 'txt2img')
    try:
        if task == 'img2img' or task == 'inpaint':
            result = _run_img2img_job_payload(job_id, payload)
        else:
            result = _run_txt2img_job_payload(job_id, payload)
        queue_manager.update(job_id, status='done', progress=100, result=result)
        job_store.update(job_id, status='done', progress=100, result=result)
    except Exception as exc:
        queue_manager.update(job_id, status='failed', error=str(exc))
        job_store.update(job_id, status='failed', error=str(exc))


queue_manager.start_worker_pool(_process_queue_job, num_workers=int(os.environ.get('IMAGINEX_GPU_COUNT', '1')))


class Txt2ImgRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ''
    steps: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    seed: Optional[int] = -1
    num_images: Optional[int] = 1
    cfg_scale: Optional[float] = None
    sampler: Optional[str] = None
    scheduler: Optional[str] = None
    base_model: Optional[str] = None


class ImageInRequest(BaseModel):
    image_b64: Optional[str] = None


class UpscaleResponse(BaseModel):
    image: str


class DescribeResponse(BaseModel):
    prompt: str


class Txt2ImgResponse(BaseModel):
    images: List[str]  # base64-encoded PNGs


# Simple in-memory task registry for background jobs
tasks = {}

# Simple rate limiter: allow N requests per minute per IP
RATE_LIMIT = int(os.environ.get('IMAGINEX_RATE_LIMIT_PER_MIN', '20'))
rate_counters = {}


def _pil_from_np(img: np.ndarray) -> Image.Image:
    if img.dtype != np.uint8:
        img = (np.clip(img, 0, 255)).astype(np.uint8)
    if img.ndim == 3 and img.shape[2] == 3:
        return Image.fromarray(img)
    if img.ndim == 2:
        return Image.fromarray(img)
    raise ValueError('Unsupported image shape')


@app.post('/v1/txt2img', response_model=Txt2ImgResponse)
def txt2img(req: Txt2ImgRequest, request: Request):
    if not require_api_auth(request, API_AUTH_TOKEN):
        raise HTTPException(status_code=401, detail='Unauthorized')
    client_ip = request.client.host if request.client else 'unknown'
    if not _rate_limit_check(client_ip):
        raise HTTPException(status_code=429, detail='Rate limit exceeded')
    # Apply defaults
    steps = req.steps or flags.Steps.SPEED.value if hasattr(flags, 'Steps') else (config.default_cfg_scale)
    cfg_scale = req.cfg_scale if req.cfg_scale is not None else config.default_cfg_scale
    sampler = req.sampler or config.default_sampler
    scheduler = req.scheduler or config.default_scheduler
    base_model = req.base_model or config.default_base_model_name
    width = req.width or 1024
    height = req.height or 1024
    seed = int(req.seed) if req.seed is not None else -1

    # Refresh models if requested
    try:
        pipeline.refresh_everything(refiner_model_name=config.default_refiner_model_name,
                                    base_model_name=base_model,
                                    loras=[],
                                    vae_name=config.default_vae)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed loading models: {e}")

    # Prepare conditioning
    positive = [req.prompt]
    negative = [req.negative_prompt] if req.negative_prompt is not None else ['']
    try:
        c = pipeline.clip_encode(texts=positive, pool_top_k=1)
        uc = pipeline.clip_encode(texts=negative, pool_top_k=1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed encoding prompts: {e}")

    images_b64 = []
    for i in range(max(1, req.num_images)):
        image_seed = seed if seed >= 0 else np.random.randint(0, 2 ** 31 - 1)
        try:
            imgs = pipeline.process_diffusion(positive_cond=c, negative_cond=uc, steps=req.steps or 30,
                                              switch=config.default_refiner_switch, width=width, height=height,
                                              image_seed=image_seed, callback=lambda *a, **k: None,
                                              sampler_name=sampler, scheduler_name=scheduler,
                                              cfg_scale=cfg_scale, disable_preview=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

        # imgs is list of numpy arrays or PIL images
        for img in imgs:
            if isinstance(img, np.ndarray):
                pil = _pil_from_np(img)
            elif isinstance(img, Image.Image):
                pil = img
            else:
                try:
                    pil = Image.open(img)
                except Exception:
                    raise HTTPException(status_code=500, detail='Unknown image format in pipeline output')

            buf = io.BytesIO()
            pil.save(buf, format='PNG')
            images_b64.append(base64.b64encode(buf.getvalue()).decode('ascii'))

            # Also save to outputs path for persistence
            try:
                outdir = config.get_path_output()
                os.makedirs(outdir, exist_ok=True)
                fname = f"img_{int(time.time())}_{uuid.uuid4().hex[:8]}.png"
                with open(os.path.join(outdir, fname), 'wb') as f:
                    f.write(buf.getvalue())
            except Exception:
                pass

    images_b64 = _apply_safety_filter(images_b64)
    return Txt2ImgResponse(images=images_b64)


def _b64_to_pil(b64: str) -> Image.Image:
    data = base64.b64decode(b64)
    return Image.open(io.BytesIO(data)).convert('RGB')


@app.post('/v1/describe', response_model=DescribeResponse)
def describe(req: ImageInRequest, request: Request):
    if not require_api_auth(request, API_AUTH_TOKEN):
        raise HTTPException(status_code=401, detail='Unauthorized')
    client_ip = request.client.host if request.client else 'unknown'
    if not _rate_limit_check(client_ip):
        raise HTTPException(status_code=429, detail='Rate limit exceeded')
    if req.image_b64 is None:
        raise HTTPException(status_code=400, detail='image_b64 required')
    try:
        pil = _b64_to_pil(req.image_b64)
        img_np = np.array(pil)
        prompt = __import__('extras.interrogate', fromlist=['default_interrogator']).default_interrogator(img_np)
        return DescribeResponse(prompt=prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Describe failed: {e}')


@app.post('/v1/upscale', response_model=UpscaleResponse)
def upscale(req: ImageInRequest, request: Request):
    if not require_api_auth(request, API_AUTH_TOKEN):
        raise HTTPException(status_code=401, detail='Unauthorized')
    client_ip = request.client.host if request.client else 'unknown'
    if not _rate_limit_check(client_ip):
        raise HTTPException(status_code=429, detail='Rate limit exceeded')
    if req.image_b64 is None:
        raise HTTPException(status_code=400, detail='image_b64 required')
    try:
        pil = _b64_to_pil(req.image_b64)
        img_np = np.array(pil)
        # call perform_upscale
        up = __import__('modules.upscaler', fromlist=['perform_upscale']).perform_upscale(img_np)
        pil_up = _pil_from_np(up)
        buf = io.BytesIO()
        pil_up.save(buf, format='PNG')
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        # persist
        try:
            outdir = config.get_path_output()
            os.makedirs(outdir, exist_ok=True)
            fname = f"up_{int(time.time())}_{uuid.uuid4().hex[:8]}.png"
            with open(os.path.join(outdir, fname), 'wb') as f:
                f.write(buf.getvalue())
        except Exception:
            pass
        return UpscaleResponse(image=b64)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Upscale failed: {e}')


def _create_task(func, *args, **kwargs):
    task_id = uuid.uuid4().hex
    tasks[task_id] = {'status': 'queued', 'progress': 0, 'result': None, 'error': None}

    def _wrap():
        try:
            tasks[task_id]['status'] = 'running'
            for progress, data in func(*args, **kwargs):
                # func may yield progress tuples (progress_int, payload)
                tasks[task_id]['progress'] = int(progress)
                tasks[task_id].setdefault('previews', []).append(data)
            tasks[task_id]['status'] = 'done'
        except Exception as e:
            tasks[task_id]['status'] = 'failed'
            tasks[task_id]['error'] = str(e)

    threading.Thread(target=_wrap, daemon=True).start()
    return task_id


@app.get('/v1/tasks/{task_id}')
def get_task_status(task_id: str, request: Request):
    if not require_api_auth(request, API_AUTH_TOKEN):
        raise HTTPException(status_code=401, detail='Unauthorized')
    if task_id not in tasks:
        stored = job_store.get(task_id)
        if stored is None:
            queued = queue_manager.get_job_status(task_id)
            if queued is None:
                raise HTTPException(status_code=404, detail='Task not found')
            return queued
        return stored
    return tasks[task_id]


@app.get('/v1/jobs/{job_id}')
def get_job_status(job_id: str, request: Request):
    if not require_api_auth(request, API_AUTH_TOKEN):
        raise HTTPException(status_code=401, detail='Unauthorized')
    status = queue_manager.get_job_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail='Job not found')
    return status


@app.get('/v1/admin/jobs')
def list_admin_jobs(request: Request):
    if not require_api_auth(request, API_AUTH_TOKEN):
        raise HTTPException(status_code=401, detail='Unauthorized')
    return queue_manager.list_jobs()


@app.post('/v1/jobs/txt2img')
def submit_txt2img_job(req: Txt2ImgRequest, request: Request):
    if not require_api_auth(request, API_AUTH_TOKEN):
        raise HTTPException(status_code=401, detail='Unauthorized')
    client_ip = request.client.host if request.client else 'unknown'
    if not _rate_limit_check(client_ip):
        raise HTTPException(status_code=429, detail='Rate limit exceeded')

    task_id = queue_manager.enqueue('txt2img', payload=req.dict())
    tasks[task_id] = {'status': 'queued', 'progress': 0, 'result': None, 'error': None}
    job_store.create(status='queued', payload=req.dict())
    job_store.update(task_id, status='queued', payload=req.dict())
    return {'task_id': task_id}


@app.post('/v1/jobs/img2img')
def submit_img2img_job(payload: dict, request: Request):
    """Expect payload with keys: image_b64, prompt, negative_prompt, width, height, denoising_strength, steps, etc."""
    if not require_api_auth(request, API_AUTH_TOKEN):
        raise HTTPException(status_code=401, detail='Unauthorized')
    client_ip = request.client.host if request.client else 'unknown'
    if not _rate_limit_check(client_ip):
        raise HTTPException(status_code=429, detail='Rate limit exceeded')

    image_b64 = payload.get('image_b64')
    if image_b64 is None:
        raise HTTPException(status_code=400, detail='image_b64 required')

    # Decode image
    try:
        img = _b64_to_pil(image_b64)
        img_np = np.array(img)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Invalid image: {e}')

    params = {
        'prompt': payload.get('prompt', ''),
        'negative_prompt': payload.get('negative_prompt', ''),
        'steps': payload.get('steps', None),
        'num_images': payload.get('num_images', 1),
        'base_model_name': payload.get('base_model', None),
        'inpaint_input_image': img_np,
        'current_tab': 'ip',
        'inpaint_engine': payload.get('inpaint_engine', config.default_inpaint_engine_version),
        'inpaint_strength': payload.get('denoising_strength', 1.0),
        'disable_preview': True,
    }

    task_id = queue_manager.enqueue('img2img', payload=payload)
    tasks[task_id] = {'status': 'queued', 'progress': 0, 'result': None, 'error': None}
    job_store.create(status='queued', payload=payload)
    job_store.update(task_id, status='queued', payload=payload)
    return {'task_id': task_id}


@app.post('/v1/jobs/inpaint')
def submit_inpaint_job(payload: dict, request: Request):
    return submit_img2img_job(payload, request)


def _rate_limit_check(client_ip: str):
    now = time.time()
    window = 60
    rec = rate_counters.get(client_ip, [])
    # drop old
    rec = [t for t in rec if t > now - window]
    if len(rec) >= RATE_LIMIT:
        return False
    rec.append(now)
    rate_counters[client_ip] = rec
    return True


def run(host: str = '0.0.0.0', port: int = 7865):
    import uvicorn
    uvicorn.run(app, host=host, port=port)
