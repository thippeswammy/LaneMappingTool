
import os
import json
import numpy as np
import open3d.t.io
from PIL import Image

def process_pcd_to_image(pcd_path, output_dir, resolution=0.1):
    """
    Converts a PCD file to a top-down intensity projection image.
    
    Args:
        pcd_path (str): Path to the input .pcd file.
        output_dir (str): Directory to save the output image and metadata.
        resolution (float): Meters per pixel.
        
    Returns:
        dict: Metadata containing image path, bounds, and resolution.
    """
    if not os.path.exists(pcd_path):
        raise FileNotFoundError(f"PCD file not found: {pcd_path}")
        
    print(f"Loading PCD from {pcd_path}...")
    try:
        pcd = open3d.t.io.read_point_cloud(pcd_path)
    except Exception as e:
        print(f"Error loading PCD: {e}")
        return None

    positions = pcd.point.positions.numpy()
    
    # Check for intensity
    if 'intensity' in pcd.point:
        intensities = pcd.point.intensity.numpy().flatten()
    else:
        print("No intensity channel found. Using height as intensity.")
        intensities = positions[:, 2] # Use Z as intensity fallback

    # Extract X, Y
    x = positions[:, 0]
    y = positions[:, 1]
    
    min_x, max_x = np.min(x), np.max(x)
    min_y, max_y = np.min(y), np.max(y)
    
    print(f"Bounds: X[{min_x:.2f}, {max_x:.2f}], Y[{min_y:.2f}, {max_y:.2f}]")
    
    width = int(np.ceil((max_x - min_x) / resolution))
    height = int(np.ceil((max_y - min_y) / resolution))
    
    print(f"Image Size: {width} x {height}")
    
    # Create grid
    # We map x, y to indices
    # col = (x - min_x) / res
    # row = (max_y - y) / res  <-- Image origin is usually top-left.
    # But coordinate system: Y is up? 
    # In standard map (East-North), Y is North (Up).
    # In Image, Y is Down.
    # So we need to flip Y.
    
    cols = ((x - min_x) / resolution).astype(int)
    rows = ((max_y - y) / resolution).astype(int)
    
    # Clip to be safe
    cols = np.clip(cols, 0, width - 1)
    rows = np.clip(rows, 0, height - 1)
    
    # Aggregate intensity
    # We want max intensity per pixel to see lane markings clearly
    grid = np.zeros((height, width), dtype=np.float32)
    
    # Naive loop is slow for 10M points. Use numpy accumulation if possible.
    # Or just iterate. 10M is a lot.
    # Faster: Sort by index and reduce.
    
    flat_indices = rows * width + cols
    
    # We want max intensity at each index.
    # We can use scipy.ndimage or simpler: 
    # Pandas groupby? overhead.
    # Numpy `at` ufunc?
    # np.maximum.at(grid.ravel(), flat_indices, intensities)
    
    print("Projecting points...")
    grid_flat = grid.ravel()
    np.maximum.at(grid_flat, flat_indices, intensities)
    grid = grid_flat.reshape((height, width))
    
    # Normalize grid to 0-255
    valid_mask = grid > 0
    if np.any(valid_mask):
        vmin, vmax = np.percentile(grid[valid_mask], [5, 99]) # Percentile robust scaling
        print(f"Intensity scaling: {vmin} to {vmax}")
        grid = np.clip((grid - vmin) / (vmax - vmin), 0, 1) * 255
    
    img_array = grid.astype(np.uint8)
    
    # Create image
    img = Image.fromarray(img_array, mode='L') # Grayscale
    
    # Save
    base_name = os.path.splitext(os.path.basename(pcd_path))[0]
    img_filename = f"{base_name}_projection.png"
    img_path = os.path.join(output_dir, img_filename)
    
    os.makedirs(output_dir, exist_ok=True)
    img.save(img_path)
    print(f"Saved map image to {img_path}")
    
    metadata = {
        "image_file": img_filename,
        "width": width,
        "height": height,
        "resolution": resolution,
        "min_x": float(min_x),
        "min_y": float(min_y),
        "max_x": float(max_x),
        "max_y": float(max_y),
        "origin_top_left": True # Indicates we flipped Y
    }
    
    meta_filename = f"{base_name}_metadata.json"
    meta_path = os.path.join(output_dir, meta_filename)
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=4)
        
    return metadata

if __name__ == "__main__":
    # Test run
    pcd = r"f:\RunningProjects\LaneMappingTool\Maps\GitamMap.pcd"
    out = r"f:\RunningProjects\LaneMappingTool\web\backend\static\maps"
    process_pcd_to_image(pcd, out)
