import numpy as np
from PIL import Image
import os
import time
import warnings

# --- Pillow safe settings for large TIFFs ---
Image.MAX_IMAGE_PIXELS = None
warnings.simplefilter("ignore", Image.DecompressionBombWarning)

# SAFE TILE SIZE FOR FREE TIER
TILE_SIZE = 512

# Global in-memory progress tracker
progress_dict = {}  # job_id -> progress percentage

# Optional: store heatmaps temporarily
heatmap_dict = {}  # job_id -> numpy array / file path


def process_tiff_background(file_path: str, job_id: str):
    """
    Memory-safe, background TIFF processing.
    Tile-based grayscale intensity extraction.
    Tracks progress for frontend polling.
    """
    print(f"[JOB {job_id}] Started processing")

    try:
        with Image.open(file_path) as img:
            img = img.convert("L")  # grayscale
            width, height = img.size

            # Optional downscale for very large images
            max_dim = 4000
            if max(width, height) > max_dim:
                img.thumbnail((max_dim, max_dim), Image.LANCZOS)
                width, height = img.size
                print(f"[JOB {job_id}] Image downscaled to {width}x{height}")

            total_tiles = ((width + TILE_SIZE - 1) // TILE_SIZE) * ((height + TILE_SIZE - 1) // TILE_SIZE)
            processed_tiles = 0

            tile_means = np.zeros(( (height + TILE_SIZE -1)//TILE_SIZE , (width + TILE_SIZE -1)//TILE_SIZE ))

            for ty, y in enumerate(range(0, height, TILE_SIZE)):
                for tx, x in enumerate(range(0, width, TILE_SIZE)):
                    box = (x, y, min(x + TILE_SIZE, width), min(y + TILE_SIZE, height))
                    tile = img.crop(box)
                    tile_np = np.asarray(tile, dtype=np.uint8)

                    # mean grayscale as proxy for intensity
                    tile_means[ty, tx] = float(tile_np.mean())

                    # Cleanup
                    del tile_np
                    del tile

                    # Update progress
                    processed_tiles += 1
                    progress_dict[job_id] = int(processed_tiles / total_tiles * 100)

                    # Optional throttle for free-tier CPU
                    time.sleep(0.001)

            # Store processed tile means for future heatmap generation
            heatmap_dict[job_id] = tile_means

            print(f"[JOB {job_id}] Completed | Tiles processed: {processed_tiles}")

    except Exception as e:
        print(f"[JOB {job_id}] ERROR: {str(e)}")
        progress_dict[job_id] = -1  # error code

    finally:
        # Remove temp TIFF
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[JOB {job_id}] Temp file removed")
