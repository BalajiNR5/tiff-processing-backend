# TIFF Heatmap Backend

Backend service for processing large (100MB+) TIFF scanned images
and generating grayscale intensity heatmaps.

## Features
- Streaming upload (no RAM overload)
- Tile-based TIFF decoding
- Background processing
- Heatmap generation
- Cloud-ready (Render)

## API
POST   /upload
GET    /status/{job_id}
GET    /result/{job_id}
