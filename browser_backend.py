import os
import re
import json
import base64
import asyncio
import hashlib
import folder_paths
import comfy.utils
import comfy.sd
from server import PromptServer
from aiohttp import web

# ─── PFADE & ORDNER (BASIC) ─────────────────────────────────────────────────────
# Nutzt relative Pfade, funktioniert also automatisch nach der Ordner-Umbenennung
BASE_DIR = os.path.dirname(__file__)

LORA_CACHE_FILE = os.path.join(BASE_DIR, "lora_cache.json")
LORA_IMG_DIR = os.path.join(BASE_DIR, "lora_local_images")
os.makedirs(LORA_IMG_DIR, exist_ok=True)

CKPT_CACHE_FILE = os.path.join(BASE_DIR, "checkpoint_cache.json")
CKPT_IMG_DIR = os.path.join(BASE_DIR, "checkpoint_local_images")
os.makedirs(CKPT_IMG_DIR, exist_ok=True)

DIFF_CACHE_FILE = os.path.join(BASE_DIR, "diffusion_cache.json")
DIFF_IMG_DIR = os.path.join(BASE_DIR, "diffusion_local_images")
os.makedirs(DIFF_IMG_DIR, exist_ok=True)

PromptServer.instance.app.router.add_static("/visual_lora_images/", path=LORA_IMG_DIR, name="visual_lora_images")
PromptServer.instance.app.router.add_static("/visual_checkpoint_images/", path=CKPT_IMG_DIR, name="visual_checkpoint_images")
PromptServer.instance.app.router.add_static("/visual_diffusion_images/", path=DIFF_IMG_DIR, name="visual_diffusion_images")

# ─── HILFSFUNKTIONEN ────────────────────────────────────────────────────────────
def load_json_cache(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f: return json.load(f)
        # FIX: Narrow exception scope — bare `except:` would also swallow KeyboardInterrupt/SystemExit
        except Exception as e:
            print(f"[Visual Browser] Failed to load cache {filepath}: {e}")
    return {}

def save_json_cache(filepath, data):
    # FIX: Atomic write — write to temp file first, then os.replace().
    # Prevents JSON corruption if the process is killed mid-write.
    tmp_path = filepath + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    os.replace(tmp_path, filepath)

HASH_CACHE = {}  # filepath -> (mtime, sha256_hex)
def calculate_sha256(filepath):
    # FIX: Cache by (mtime, hash) instead of just hash. If the LoRA file is replaced
    # with a different model of the same filename, the stale hash would otherwise
    # cause a wrong Civitai lookup forever until ComfyUI restart.
    try:
        current_mtime = os.path.getmtime(filepath)
    except OSError:
        return None

    cached = HASH_CACHE.get(filepath)
    if cached and cached[0] == current_mtime:
        return cached[1]

    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096 * 1024), b""): sha256_hash.update(byte_block)
        result = sha256_hash.hexdigest()
        HASH_CACHE[filepath] = (current_mtime, result)
        return result
    # FIX: Narrow exception scope (bare except would also swallow KeyboardInterrupt/SystemExit)
    except Exception as e:
        print(f"[Visual Browser] Failed to hash {filepath}: {e}")
        return None

# ─── KONSTANTEN ─────────────────────────────────────────────────────────────────
_MIME_TO_EXT = {
    "image/jpeg": ".jpg", "image/jpg": ".jpg",
    "image/png": ".png", "image/webp": ".webp",
    "image/gif": ".gif", "video/mp4": ".mp4",
    "video/webm": ".webm",
}
_ALLOWED_EXTENSIONS = set(_MIME_TO_EXT.values())  # Whitelist: only known media types
_MAX_IMAGE_BYTES = 50 * 1024 * 1024  # 50 MB decoded limit

# ─── API ROUTEN GENERATOR (BASIC - REDUZIERT) ───────────────────────────────────
def create_routes(prefix, folder_name, cache_file, img_dir, web_img_path):
    # FIX: Per-cache asyncio lock — serializes update_cache so concurrent requests
    # (e.g. fast typed notes + Civitai save) cannot drop each other's writes via
    # the read-modify-write pattern below.
    cache_lock = asyncio.Lock()

    @PromptServer.instance.routes.get(f"/{prefix}/list_models")
    async def list_models(request):
        models = folder_paths.get_filename_list(folder_name)
        result_list = []
        for m in models:
            filepath = folder_paths.get_full_path(folder_name, m)
            download_date = None
            if filepath and os.path.exists(filepath):
                try:
                    # Windows: st_birthtime (Creation Time) | Linux: st_mtime (Modification Time)
                    stat = os.stat(filepath)
                    timestamp = getattr(stat, 'st_birthtime', stat.st_mtime)
                    # Konvertiere in Millisekunden für das JavaScript Frontend
                    download_date = int(timestamp * 1000)
                except Exception:
                    pass

            result_list.append({
                "filename": m, 
                "name": os.path.splitext(m)[0].replace("\\", "/").split("/")[-1],
                "download_date": download_date
            })
            
        return web.json_response({"models": result_list})

    @PromptServer.instance.routes.post(f"/{prefix}/get_hash")
    async def get_hash(request):
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"hash": None})
        filepath = folder_paths.get_full_path(folder_name, data.get("filename"))
        if not filepath or not os.path.exists(filepath): return web.json_response({"hash": None})
        return web.json_response({"hash": calculate_sha256(filepath)})

    @PromptServer.instance.routes.get(f"/{prefix}/get_cache")
    async def get_cache_route(request):
        return web.json_response(load_json_cache(cache_file))

    @PromptServer.instance.routes.post(f"/{prefix}/update_cache")
    async def update_cache_route(request):
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"status": "error", "reason": "invalid_json"}, status=400)

        filename = data.get("filename")
        civitai_data = data.get("civitai_data")

        # FIX: Validate inputs — reject non-string filenames and non-dict cache values.
        # Without this, a malformed request could write None/int/list keys into the JSON
        # cache and corrupt it for everyone (cache[None] becomes "null" key after round-trip).
        if not isinstance(filename, str) or not filename:
            return web.json_response({"status": "error", "reason": "filename_must_be_nonempty_string"}, status=400)
        if not isinstance(civitai_data, dict):
            return web.json_response({"status": "error", "reason": "civitai_data_must_be_object"}, status=400)

        # Hold the per-cache lock for the full read-modify-write so concurrent writes
        # can't clobber each other (combined with atomic save_json_cache).
        async with cache_lock:
            cache = load_json_cache(cache_file)
            cache[filename] = civitai_data
            save_json_cache(cache_file, cache)
        return web.json_response({"status": "ok"})

    @PromptServer.instance.routes.post(f"/{prefix}/save_local_image")
    async def save_local_image(request):
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"status": "error", "reason": "invalid_json"}, status=400)

        lora_filename = data.get("lora_filename", "")
        image_b64    = data.get("image_b64", "")
        mime_type    = data.get("mime_type", "image/jpeg")
        orig_name    = data.get("orig_filename", "")

        if not isinstance(lora_filename, str) or not lora_filename:
            return web.json_response({"status": "error", "reason": "missing lora_filename"}, status=400)
        if not isinstance(image_b64, str) or not image_b64:
            return web.json_response({"status": "error", "reason": "missing image_b64"}, status=400)

        # Size check on base64 string (base64 is ~4/3 of decoded size)
        if len(image_b64) > _MAX_IMAGE_BYTES * 4 // 3 + 64:
            return web.json_response({"status": "error", "reason": "image_too_large"}, status=413)

        try:
            img_bytes = base64.b64decode(image_b64)
        except Exception:
            return web.json_response({"status": "error", "reason": "invalid_base64"}, status=400)

        if len(img_bytes) > _MAX_IMAGE_BYTES:
            return web.json_response({"status": "error", "reason": "image_too_large"}, status=413)

        # Extension: derive from orig_filename, then mime_type — but only allow whitelisted extensions
        _, fe = os.path.splitext(orig_name)
        ext = fe.lower() if fe.lower() in _ALLOWED_EXTENSIONS else _MIME_TO_EXT.get(mime_type.split(";")[0].strip().lower(), ".jpg")

        safe_base = re.sub(r"[^\w\-]", "_", os.path.splitext(os.path.basename(lora_filename))[0])[:80]
        img_filename = safe_base + ext
        img_path = os.path.join(img_dir, img_filename)

        try:
            with open(img_path, "wb") as f:
                f.write(img_bytes)
        except Exception as e:
            print(f"[Visual Browser] Failed to save local image: {e}")
            return web.json_response({"status": "error", "reason": str(e)}, status=500)

        return web.json_response({"status": "ok", "url": f"/{web_img_path}/{img_filename}"})

    @PromptServer.instance.routes.post(f"/{prefix}/delete_local_image")
    async def delete_local_image(request):
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"status": "error", "reason": "invalid_json"}, status=400)
        url = data.get("url", "")
        if not isinstance(url, str) or not url:
            return web.json_response({"status": "error", "reason": "missing url"}, status=400)
        basename = os.path.basename(url.split("?")[0])
        if not basename:
            return web.json_response({"status": "error", "reason": "invalid_url"}, status=400)
        img_path = os.path.join(img_dir, basename)
        # Path traversal guard
        if not os.path.abspath(img_path).startswith(os.path.abspath(img_dir) + os.sep):
            return web.json_response({"status": "error", "reason": "path_traversal"}, status=400)
        try:
            if os.path.exists(img_path):
                os.remove(img_path)
            return web.json_response({"status": "ok"})
        except Exception as e:
            print(f"[Visual Browser] Failed to delete local image: {e}")
            return web.json_response({"status": "error", "reason": str(e)}, status=500)

# Initialisiere reduzierte Routen für alle 3 Module
create_routes("visual_lora", "loras", LORA_CACHE_FILE, LORA_IMG_DIR, "visual_lora_images")
create_routes("visual_checkpoint", "checkpoints", CKPT_CACHE_FILE, CKPT_IMG_DIR, "visual_checkpoint_images")
create_routes("visual_diffusion", "unet", DIFF_CACHE_FILE, DIFF_IMG_DIR, "visual_diffusion_images")

# ─── NODE KLASSEN ───────────────────────────────────────────────────────────────
class VisualLoraBrowserLX:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "selected_lora": ("STRING", {"default": ""}),
                "strength_model": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "strength_clip": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
            }
        }
    RETURN_TYPES = ("MODEL", "CLIP")
    RETURN_NAMES = ("model", "clip")
    FUNCTION = "apply_lora"
    CATEGORY = "Smart Nodes"

    def apply_lora(self, model, clip, selected_lora, strength_model, strength_clip):
        if not selected_lora or selected_lora == "--- Select LoRA ---": return (model, clip)
        lora_path = folder_paths.get_full_path("loras", selected_lora)
        if not lora_path: return (model, clip)
        lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
        return comfy.sd.load_lora_for_models(model, clip, lora, strength_model, strength_clip)

class VisualCheckpointLoaderLX:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"selected_model": ("STRING", {"default": ""})}}
    RETURN_TYPES = ("MODEL", "CLIP", "VAE")
    RETURN_NAMES = ("MODEL", "CLIP", "VAE")
    FUNCTION = "load_checkpoint"
    CATEGORY = "Smart Nodes"

    def load_checkpoint(self, selected_model):
        if not selected_model or selected_model == "--- Select Model ---": raise ValueError("No checkpoint selected.")
        ckpt_path = folder_paths.get_full_path("checkpoints", selected_model)
        if not ckpt_path: raise ValueError(f"Checkpoint not found: {selected_model}")
        out = comfy.sd.load_checkpoint_guess_config(ckpt_path, output_vae=True, output_clip=True, embedding_directory=folder_paths.get_folder_paths("embeddings"))
        return (out[0], out[1], out[2])

class VisualDiffusionLoaderLX:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"selected_model": ("STRING", {"default": ""})}}
    RETURN_TYPES = ("MODEL",)
    RETURN_NAMES = ("MODEL",)
    FUNCTION = "load_unet"
    CATEGORY = "Smart Nodes"

    def load_unet(self, selected_model):
        if not selected_model or selected_model == "--- Select Model ---": raise ValueError("No Diffusion Model selected.")
        unet_path = folder_paths.get_full_path("unet", selected_model)
        if not unet_path: raise ValueError(f"Model not found: {selected_model}")
        return (comfy.sd.load_unet(unet_path),)

NODE_CLASS_MAPPINGS = {
    "VisualLoraBrowserLX": VisualLoraBrowserLX,
    "VisualCheckpointLoaderLX": VisualCheckpointLoaderLX,
    "VisualDiffusionLoaderLX": VisualDiffusionLoaderLX
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "VisualLoraBrowserLX": "🌐 Civitai Visual LoRA Loader by LX",
    "VisualCheckpointLoaderLX": "🌐 Civitai Visual Checkpoint Model Loader by LX",
    "VisualDiffusionLoaderLX": "🌐 Civitai Visual Diffusion Model Loader by LX"
}