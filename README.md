# ply-to-splat

A quick way to create a Gaussian splat `.ply` file from a LiDAR `.ply` scan.

This repository is designed to avoid resource-intensive splat training when your main goal is fast visualization. It was tested on Share3D LiDAR scanners and can preprocess large scans quickly.

## What this repo does

- Preprocess raw LiDAR scans with CloudCompare for denoising, spatial subsampling, and coordinate transformation.
- Convert the cleaned point cloud to a Gaussian splat PLY using a lightweight Python script.
- Fast performance for large point clouds:
  - ~10s preprocessing, denoising, and transformation of an 11M point cloud using CloudCompare CLI
  - ~2s to create the Gaussian splat from the processed point cloud

## Prerequisites

- Python 3 with a virtual environment.
- Install dependencies from `requirements.txt`:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
- CloudCompare installed.
  - macOS and Windows are tested.
  - Linux is supported by the `src/cloud-compare-prepare.py` script.
  - CloudCompare is not required for the core `src/ply-to-splat.py` conversion, but it is helpful for scan preparation.

## Repository files

- `src/cloud-compare-prepare.py`
  - Runs CloudCompare CLI to load a PLY file, apply optional rotation, perform spatial subsampling, and save a cleaned PLY.
- `src/ply-to-splat.py`
  - Converts a cleaned LiDAR PLY into a Gaussian splat PLY with the 3DGS vertex attributes.

## Usage

### Recommended: Included wrapper script

This repository includes `prepare-and-splat.sh` and `prepare-and-splat.ps1`, which simplify the pipeline and apply a default `90,0,0` rotation during CloudCompare preprocessing.

- accepts input and output paths
- runs `src/cloud-compare-prepare.py --rotate 90,0,0` to produce `tmp-mesh.ply`
- runs `src/ply-to-splat.py` on `tmp-mesh.ply`

Use `./prepare-and-splat.sh input.ply output-splat.ply` on macOS/Linux, or `.\prepare-and-splat.ps1 input.ply output-splat.ply` in PowerShell on Windows.

### Manual workflow

1. Prepare the point cloud:
   ```bash
   python3 src/cloud-compare-prepare.py --ss 0.0075 --rotate 90,0,0 input.ply tmp-mesh.ply
   ```
2. Convert the cleaned point cloud to a Gaussian splat:
   ```bash
   python3 src/ply-to-splat.py tmp-mesh.ply --scale '-5.5' output-splat.ply
   ```

## CloudCompare warning note

If CloudCompare shows a warning about Python during execution, acknowledge it with `OK`. The processing still works correctly despite the warning.
