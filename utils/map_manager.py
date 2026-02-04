
import os
import json
import glob
from web.backend.utils.map_processor import process_pcd_to_image

class MapManager:
    def __init__(self, maps_dir, static_maps_dir):
        """
        Args:
            maps_dir (str): Directory containing .pcd files.
            static_maps_dir (str): Directory where generated images and metadata will be stored.
        """
        self.maps_dir = maps_dir
        self.static_maps_dir = static_maps_dir
        
        if not os.path.exists(self.static_maps_dir):
            os.makedirs(self.static_maps_dir)

    def list_maps(self):
        """
        Lists available .pcd files and their status (processed or not).
        Returns:
            list: List of dicts {name, has_projection, image_url (if ready)}
        """
        pcd_files = glob.glob(os.path.join(self.maps_dir, "*.pcd"))
        maps = []
        
        for pcd_path in pcd_files:
            base_name = os.path.splitext(os.path.basename(pcd_path))[0]
            meta_filename = f"{base_name}_metadata.json"
            meta_path = os.path.join(self.static_maps_dir, meta_filename)
            
            pcd_info = {
                "name": base_name,
                "filename": os.path.basename(pcd_path),
                "processed": False,
                "metadata": None
            }
            
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r') as f:
                        metadata = json.load(f)
                        pcd_info["processed"] = True
                        pcd_info["metadata"] = metadata
                except Exception as e:
                    print(f"Error reading metadata for {base_name}: {e}")
            
            maps.append(pcd_info)
            
        return maps

    def load_map(self, map_name, force_process=False):
        """
        Ensures a map is processed and returns its metadata.
        If projection doesn't exist, it triggers processing.
        """
        pcd_filename = f"{map_name}.pcd"
        pcd_path = os.path.join(self.maps_dir, pcd_filename)
        
        if not os.path.exists(pcd_path):
            raise FileNotFoundError(f"Map {map_name} not found.")

        meta_filename = f"{map_name}_metadata.json"
        meta_path = os.path.join(self.static_maps_dir, meta_filename)
        
        # If not processed or forced, process it
        if force_process or not os.path.exists(meta_path):
            print(f"Processing map {map_name} (Force: {force_process})...")
            # Re-use the processor logic
            # Assuming processor returns metadata dict
            metadata = process_pcd_to_image(pcd_path, self.static_maps_dir)
        else:
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
                
        return metadata
