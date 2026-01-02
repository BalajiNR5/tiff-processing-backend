# processing.py
import numpy as np
from PIL import Image
import os
import time
import warnings

# --- Pillow safe settings for large TIFFs ---
Image.MAX_IMAGE_PIXELS = None
warnings.simplefilter("ignore", Image.DecompressionBombWarning)

TILE_SIZE = 512

# Global in-memory progress tracker
progress_dict = {}  # job_id -> progress percentage

# Store temporary heatmaps per job
heatmap_dict = {}  # job_id -> file path


def process_tiff_background(file_path: str, job_id: str):
    """
    Memory-safe TIFF processing optimized for 512MB RAM.
    - Converts to 8-bit grayscale
    - Lossless compression
    - Tile-based processing
    - Progress tracking
    """

    print(f"[JOB {job_id}] Started processing")
    progress_dict[job_id] = 1  # initial progress

    try:
        with Image.open(file_path) as img:
            img = img.convert("L")
            width, height = img.size

            max_dim = 2000
            if max(width, height) > max_dim:
                img.thumbnail((max_dim, max_dim), Image.LANCZOS)
                width, height = img.size
                print(f"[JOB {job_id}] Image downscaled to {width}x{height}")

            os.makedirs("tmp", exist_ok=True)
            compressed_path = os.path.join("tmp", f"{job_id}_compressed.tiff")
            img.save(compressed_path, compression="tiff_deflate")

            tiles_y = (height + TILE_SIZE - 1) // TILE_SIZE
            tiles_x = (width + TILE_SIZE - 1) // TILE_SIZE
            total_tiles = tiles_y * tiles_x
            processed_tiles = 0

            heatmap_array = np.zeros((tiles_y, tiles_x), dtype=np.float32)

            for ty, y in enumerate(range(0, height, TILE_SIZE)):
                for tx, x in enumerate(range(0, width, TILE_SIZE)):
                    box = (x, y, min(x + TILE_SIZE, width), min(y + TILE_SIZE, height))
                    tile = img.crop(box)
                    tile_np = np.asarray(tile, dtype=np.uint8)

                    heatmap_array[ty, tx] = float(tile_np.mean())

                    del tile_np
                    del tile

                    processed_tiles += 1
                    progress_dict[job_id] = max(1, int(processed_tiles / total_tiles * 100))
                    time.sleep(0.001)

            heatmap_normalized = ((heatmap_array - heatmap_array.min()) /
                                  (heatmap_array.ptp() + 1e-5) * 255).astype(np.uint8)
            heatmap_img = Image.fromarray(heatmap_normalized)
            heatmap_path = os.path.join("tmp", f"{job_id}_heatmap.png")
            heatmap_img.save(heatmap_path)
            heatmap_dict[job_id] = heatmap_path

            print(f"[JOB {job_id}] Completed | Tiles processed: {processed_tiles}")
            progress_dict[job_id] = 100

    except Exception as e:
        print(f"[JOB {job_id}] ERROR: {str(e)}")
        progress_dict[job_id] = -1

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[JOB {job_id}] Uploaded temp file removed")
        if os.path.exists(compressed_path):
            os.remove(compressed_path)
            print(f"[JOB {job_id}] Compressed temp file removed")
