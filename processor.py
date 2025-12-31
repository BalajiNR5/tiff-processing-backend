import tifffile as tiff
import numpy as np
import cv2, os, json

TILE_SIZE = 512

def update_status(job_dir, status):
    with open(os.path.join(job_dir, "status.json"), "w") as f:
        json.dump({"status": status}, f)

def process_tiff(job_dir):
    try:
        update_status(job_dir, "DECODING_TIFF")

        tiff_path = os.path.join(job_dir, "input.tiff")

        values = []

        with tiff.TiffFile(tiff_path) as tif:
            page = tif.pages[0]

            for y in range(0, page.imagelength, TILE_SIZE):
                for x in range(0, page.imagewidth, TILE_SIZE):
                    tile = page.asarray(region=(y, x, TILE_SIZE, TILE_SIZE))
                    gray = tile.astype("float32")
                    values.append(gray.mean())
                    del tile  # important for memory

        update_status(job_dir, "GENERATING_HEATMAP")

        data = np.array(values)
        data = cv2.normalize(data, None, 0, 255, cv2.NORM_MINMAX)
        data = data.astype("uint8")

        # reshape to grid-like heatmap
        side = int(np.sqrt(len(data)))
        data = data[: side * side].reshape(side, side)

        heatmap = cv2.applyColorMap(data, cv2.COLORMAP_JET)
        cv2.imwrite(os.path.join(job_dir, "heatmap.png"), heatmap)

        update_status(job_dir, "COMPLETED")

    except Exception as e:
        update_status(job_dir, f"FAILED: {str(e)}")
