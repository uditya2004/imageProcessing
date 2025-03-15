import os
import numpy as np
from PIL import Image
from rembg import remove

def remove_background(image_paths, output_dir):
    """
    Remove background from images using rembg library.
    """
    print(f"Processing {len(image_paths)} images for background removal")
    
    # Create a directory for background-removed images
    nobg_dir = os.path.join(output_dir, "no_background")
    os.makedirs(nobg_dir, exist_ok=True)
    
    processed_images = []
    
    for img_path in image_paths:
        try:
            # Open image
            with Image.open(img_path) as img:
                # Remove background
                output = remove(img)
                
                # Save to new path
                filename = os.path.basename(img_path)
                base_name, ext = os.path.splitext(filename)
                
                # Save as PNG to preserve transparency
                new_filename = f"{base_name}_nobg.png"
                new_path = os.path.join(nobg_dir, new_filename)
                
                output.save(new_path)
                processed_images.append(new_path)
                
                print(f"Removed background from: {filename}")
                
        except Exception as e:
            print(f"Error processing {os.path.basename(img_path)}: {e}")
    
    print(f"Background removal complete. Processed {len(processed_images)} images.")
    return processed_images