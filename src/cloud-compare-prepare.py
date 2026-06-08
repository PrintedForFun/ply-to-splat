#!/usr/bin/env python3
"""
prepare_point_cloud.sh (now a Python script)

Wrapper to run CloudCompare CLI across platforms with optional spatial sampling (--ss)
and optional rotation (--rotate rx,ry,rz in degrees).

Examples:
  ./prepare_point_cloud.sh input.ply output.ply
  ./prepare_point_cloud.sh --ss 0.01 --rotate 90,0,0 input.ply output.ply
"""

import argparse
import math
import os
import shutil
import subprocess
import sys
import tempfile


def find_cloudcompare():
    platform = sys.platform
    candidates = []
    if platform.startswith("darwin"):
        candidates = [
            "/Applications/CloudCompare.app/Contents/MacOS/CloudCompare",
            shutil.which("CloudCompare"),
        ]
    elif platform.startswith("linux"):
        candidates = [
            shutil.which("CloudCompare"),
            "/usr/bin/CloudCompare",
            "/usr/local/bin/CloudCompare",
        ]
    elif platform.startswith("win") or platform.startswith("cygwin"):
        # Windows-like environments
        pf = os.environ.get("PROGRAMFILES")
        pf_x86 = os.environ.get("ProgramFiles(x86)") or os.environ.get("PROGRAMFILES(X86)")
        pf64 = os.environ.get("PROGRAMW6432")
        candidates = []
        if pf:
            candidates.append(os.path.join(pf, "CloudCompare", "CloudCompare.exe"))
        if pf64:
            candidates.append(os.path.join(pf64, "CloudCompare", "CloudCompare.exe"))
        if pf_x86:
            candidates.append(os.path.join(pf_x86, "CloudCompare", "CloudCompare.exe"))
        candidates.append(shutil.which("CloudCompare.exe"))
        candidates.append(shutil.which("CloudCompare"))
        # Common msys / cygwin mounted paths
        candidates.append(r"/c/Program Files/CloudCompare/CloudCompare.exe")
        candidates.append(r"/c/Program Files (x86)/CloudCompare/CloudCompare.exe")
    else:
        candidates = [shutil.which("CloudCompare"), "/usr/bin/CloudCompare", "/usr/local/bin/CloudCompare"]

    for c in candidates:
        if not c:
            continue
        if os.path.exists(c) and os.access(c, os.X_OK):
            return c
    # last-ditch: return first non-empty candidate
    for c in candidates:
        if c:
            return c
    return None


def rotation_matrix_from_euler_deg(rx_deg, ry_deg, rz_deg):
    rx = math.radians(rx_deg)
    ry = math.radians(ry_deg)
    rz = math.radians(rz_deg)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    # Rx
    Rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    # Ry
    Ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    # Rz
    Rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]

    def matmul(A, B):
        return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

    R = matmul(Rz, matmul(Ry, Rx))
    return R


def write_transform_file(R, path):
    # build 4x4 matrix with translation 0 and bottom row 0 0 0 1
    with open(path, "w") as f:
        for i in range(3):
            row = R[i] + [0.0]
            f.write(" ".join(str(x) for x in row) + "\n")
        f.write("0 0 0 1\n")


def main(argv):
    parser = argparse.ArgumentParser(
        description="Run CloudCompare CLI with optional spatial subsampling and rotation"
    )
    parser.add_argument("input", help="input PLY file")
    parser.add_argument("output", help="output PLY file")
    parser.add_argument("--ss", type=float, default=0.0075, help="SS SPATIAL value (default: 0.0075)")
    parser.add_argument(
        "--rotate",
        type=str,
        default="",
        help="Rotate in degrees as rx,ry,rz (e.g. 90,0,0 rotates 90deg around X)",
    )
    args = parser.parse_args(argv[1:])

    cc = find_cloudcompare()
    if not cc:
        print("CloudCompare binary not found. Please install CloudCompare or add it to PATH.", file=sys.stderr)
        sys.exit(2)

    ss_val = args.ss
    trans_path = None
    try:
        if args.rotate:
            parts = args.rotate.split(",")
            if len(parts) != 3:
                print("--rotate requires three comma-separated values: rx,ry,rz", file=sys.stderr)
                sys.exit(2)
            rx, ry, rz = (float(p) for p in parts)
            if not (rx == 0 and ry == 0 and rz == 0):
                R = rotation_matrix_from_euler_deg(rx, ry, rz)
                tf = tempfile.NamedTemporaryFile(prefix="cc_transform_", suffix=".txt", delete=False)
                tf.close()
                write_transform_file(R, tf.name)
                trans_path = tf.name

        # CloudCompare expects -GLOBAL_SHIFT as an option immediately after -O
        cmd = [
            cc,
            "-SILENT",
            "-AUTO_SAVE",
            "OFF",
            "-O",
            "-GLOBAL_SHIFT",
            "AUTO",
            args.input,
        ]
        # Apply transform after the file is loaded
        if trans_path:
            cmd += ["-APPLY_TRANS", trans_path]
        cmd += ["-SS", "SPATIAL", str(ss_val), "-C_EXPORT_FMT", "PLY", "-SAVE_CLOUDS", "FILE", args.output]

        print("Running:")
        print(" ".join(cmd))
        try:
            completed = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print("--- CloudCompare STDOUT ---")
            print(completed.stdout if completed.stdout else "<no stdout>")
            print("--- CloudCompare STDERR ---", file=sys.stderr)
            print(completed.stderr if completed.stderr else "<no stderr>", file=sys.stderr)
        except subprocess.CalledProcessError as e:
            # Print diagnostics to help debug CloudCompare failure
            print(f"CloudCompare exited with return code {e.returncode}", file=sys.stderr)
            if e.stdout:
                print("--- CloudCompare STDOUT ---", file=sys.stderr)
                print(e.stdout, file=sys.stderr)
            if e.stderr:
                print("--- CloudCompare STDERR ---", file=sys.stderr)
                print(e.stderr, file=sys.stderr)
            # Suggest running without -SILENT or with -VERBOSITY/ -DEBUG for more details
            print("\nHint: try running the printed command in a terminal without -SILENT or add '-VERBOSITY 0 -DEBUG' to see more output.", file=sys.stderr)
            sys.exit(e.returncode)
    finally:
        if trans_path:
            try:
                os.remove(trans_path)
            except Exception:
                pass


if __name__ == "__main__":
    main(sys.argv)
