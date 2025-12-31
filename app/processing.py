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

def process_tiff_background(file_path: str, job_id: str):
    """
    Background-safe, memory-safe TIFF processing.
    Tile-based grayscale intensity extraction.
    """

    print(f"[JOB {job_id}] Started processing")

    try:
        with Image.open(file_path) as img:
            img = img.convert("L")  # single-channel grayscale
            width, height = img.size

            # Optional: downscale extremely large images
            max_dim = 4000  # free-tier safe
            if max(width, height) > max_dim:
                img.thumbnail((max_dim, max_dim), Image.LANCZOS)
                width, height = img.size
                print(f"[JOB {job_id}] Image downscaled to {width}x{height}")

            tile_means = []

            for y in range(0, height, TILE_SIZE):
                for x in range(0, width, TILE_SIZE):
                    box = (
                        x,
                        y,
                        min(x + TILE_SIZE, width),
                        min(y + TILE_SIZE, height)
                    )

                    tile = img.crop(box)
                    tile_np = np.asarray(tile, dtype=np.uint8)

                    # Mean grayscale intensity (pressure proxy)
                    tile_means.append(float(tile_np.mean()))

                    # Explicit cleanup (important)
                    del tile_np
                    del tile

                    # CPU throttle (Render free tier protection)
                    time.sleep(0.002)

            print(
                f"[JOB {job_id}] Completed | "
                f"Tiles processed: {len(tile_means)}"
            )

            # TODO (future):
            # - normalize tile_means
            # - reconstruct heatmap
            # - save output image

    except Exception as e:
        print(f"[JOB {job_id}] ERROR: {str(e)}")

    finally:
        # CLEAN TEMP FILE
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[JOB {job_id}] Temp file removed")
