import argparse
import numpy as np
from plyfile import PlyData, PlyElement

def convert_lidar_to_clean_splat(input_path, output_path, scale_multiplier=-5.0):
    print(f"Reading LiDAR data from {input_path}...")
    
    # Load the binary PLY
    plydata = PlyData.read(input_path)
    v = plydata['vertex']
    num_pts = v.count

    # 1. Extract XYZ (standardizing to float32)
    x = np.array(v['x'], dtype='f4')
    y = np.array(v['y'], dtype='f4')
    z = np.array(v['z'], dtype='f4')

    # 2. Convert RGB to Spherical Harmonics DC (f_dc)
    # Using the standard 3DGS normalization formula
    f_dc_0 = (np.array(v['red'], dtype='f4') / 255.0 - 0.5) / 0.28209
    f_dc_1 = (np.array(v['green'], dtype='f4') / 255.0 - 0.5) / 0.28209
    f_dc_2 = (np.array(v['blue'], dtype='f4') / 255.0 - 0.5) / 0.28209

    # 3. Generate default Splat attributes
    # Opacity: 10.0 (logit) makes the splats fully opaque
    opacity = np.ones(num_pts, dtype='f4') * 10.0
    
    # Scale: -5.0 is standard. Lower (e.g. -6.0) for sharper points, 
    # higher (e.g. -4.0) for "fuzzier" filling of gaps.
    scale = np.ones((num_pts, 3), dtype='f4') * np.float32(scale_multiplier)
    
    # Rotation: Unit quaternion [1, 0, 0, 0] (no rotation)
    rot = np.zeros((num_pts, 4), dtype='f4')
    rot[:, 0] = 1.0

    # 4. Construct the structured array with the specific 3DGS header
    dtype = [
        ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
        ('f_dc_0', 'f4'), ('f_dc_1', 'f4'), ('f_dc_2', 'f4'),
        ('opacity', 'f4'),
        ('scale_0', 'f4'), ('scale_1', 'f4'), ('scale_2', 'f4'),
        ('rot_0', 'f4'), ('rot_1', 'f4'), ('rot_2', 'f4'), ('rot_3', 'f4')
    ]

    splat_data = np.empty(num_pts, dtype=dtype)
    
    splat_data['x'], splat_data['y'], splat_data['z'] = x, y, z
    splat_data['f_dc_0'], splat_data['f_dc_1'], splat_data['f_dc_2'] = f_dc_0, f_dc_1, f_dc_2
    splat_data['opacity'] = opacity
    splat_data['scale_0'], splat_data['scale_1'], splat_data['scale_2'] = scale[:,0], scale[:,1], scale[:,2]
    splat_data['rot_0'], splat_data['rot_1'], splat_data['rot_2'], splat_data['rot_3'] = rot[:,0], rot[:,1], rot[:,2], rot[:,3]

    # 5. Write to Binary PLY (Strictly stripping comments and obj_info)
    # By passing only the PlyElement, we ensure a clean header.
    print(f"Writing {num_pts} points to {output_path}...")
    el = PlyElement.describe(splat_data, 'vertex')
    
    # We create a fresh PlyData object without passing 'comments' or 'obj_info'
    new_ply = PlyData([el], text=False) 
    new_ply.write(output_path)
    
    print("Success! Your clean Gaussian Splat PLY is ready.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert LiDAR PLY to clean Gaussian Splat PLY with adjustable scale multiplier."
    )
    parser.add_argument("input_path", help="Path to the input LiDAR PLY file")
    parser.add_argument("output_path", help="Path to the output clean splat PLY file")
    parser.add_argument(
        "--scale",
        type=float,
        default=-5.0,
        help="Scale multiplier for splats (default: -5)",
    )

    args = parser.parse_args()
    convert_lidar_to_clean_splat(args.input_path, args.output_path, args.scale)