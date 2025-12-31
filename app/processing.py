import numpy as np
from PIL import Image
import os
import time
import warnings

# --- Pillow safe settings for large TIFFs ---
Image.MAX_IMAGE_PIXELS = None
warnings.simplefilter("ignore", Image.DecompressionBombWarning)

# Safe tile size for free-tier RAM
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
    - Progress tracking for frontend
    """

    print(f"[JOB {job_id}] Started processing")
    progress_dict[job_id] = 1  # initial progress

    try:
        with Image.open(file_path) as img:
            # Convert to 8-bit grayscale
            img = img.convert("L")
            width, height = img.size

            # Downscale extremely large images for free-tier safety
            max_dim = 2000
            if max(width, height) > max_dim:
                img.thumbnail((max_dim, max_dim), Image.LANCZOS)
                width, height = img.size
                print(f"[JOB {job_id}] Image downscaled to {width}x{height}")

            # Save temporary compressed TIFF to reduce memory usage
            os.makedirs("tmp", exist_ok=True)
            compressed_path = os.path.join("tmp", f"{job_id}_compressed.tiff")
            img.save(compressed_path, compression="tiff_deflate")

            # Compute tile counts
            tiles_y = (height + TILE_SIZE - 1) // TILE_SIZE
            tiles_x = (width + TILE_SIZE - 1) // TILE_SIZE
            total_tiles = tiles_y * tiles_x
            processed_tiles = 0

            # Prepare heatmap array
            heatmap_array = np.zeros((tiles_y, tiles_x), dtype=np.float32)

            # Tile-by-tile processing
            for ty, y in enumerate(range(0, height, TILE_SIZE)):
                for tx, x in enumerate(range(0, width, TILE_SIZE)):
                    box = (x, y, min(x + TILE_SIZE, width), min(y + TILE_SIZE, height))
                    tile = img.crop(box)
                    tile_np = np.asarray(tile, dtype=np.uint8)

                    # Compute mean intensity
                    heatmap_array[ty, tx] = float(tile_np.mean())

                    # Cleanup
                    del tile_np
                    del tile

                    # Update progress
                    processed_tiles += 1
                    progress_dict[job_id] = max(1, int(processed_tiles / total_tiles * 100))

                    # Avoid CPU spike on free-tier
                    time.sleep(0.001)

            # Save final heatmap as PNG for frontend
            heatmap_normalized = ((heatmap_array - heatmap_array.min()) /
                                  (heatmap_array.ptp() + 1e-5) * 255).astype(np.uint8)
            heatmap_img = Image.fromarray(heatmap_normalized)
            heatmap_path = os.path.join("tmp", f"{job_id}_heatmap.png")
            heatmap_img.save(heatmap_path)
            heatmap_dict[job_id] = heatmap_path

            print(f"[JOB {job_id}] Completed | Tiles processed: {processed_tiles}")
            progress_dict[job_id] = 100  # mark as complete

    except Exception as e:
        print(f"[JOB {job_id}] ERROR: {str(e)}")
        progress_dict[job_id] = -1  # error flag

    finally:
        # Clean uploaded TIFF
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[JOB {job_id}] Uploaded temp file removed")

        # Clean compressed TIFF
        if os.path.exists(compressed_path):
            os.remove(compressed_path)
            print(f"[JOB {job_id}] Compressed temp file removed")
