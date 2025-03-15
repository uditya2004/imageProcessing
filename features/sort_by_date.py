import os
import shutil
from datetime import datetime
import time
from PIL import Image

def sort_by_date(image_paths, output_dir):
    """
    Sort images by date and organize them into folders by year/month.
    """
    print(f"Processing {len(image_paths)} images for date sorting")
    
    # Dictionary to store sorted images
    sorted_images = []
    
    # Create a base directory for date-sorted images
    date_dir = os.path.join(output_dir, "date_sorted")
    os.makedirs(date_dir, exist_ok=True)
    
    for img_path in image_paths:
        try:
            # Get image creation/modification date
            stat = os.stat(img_path)
            
            # Try to get date from EXIF data first
            date_taken = None
            try:
                with Image.open(img_path) as img:
                    exif_data = img._getexif()
                    if exif_data and 36867 in exif_data:  # 36867 is DateTimeOriginal tag
                        date_taken = datetime.strptime(exif_data[36867], "%Y:%m:%d %H:%M:%S")
            except Exception as e:
                print(f"Could not read EXIF data from {os.path.basename(img_path)}: {e}")
            
            # If no EXIF data, use file modification time
            if not date_taken:
                date_taken = datetime.fromtimestamp(stat.st_mtime)
            
            # Create year/month directory structure
            year_dir = os.path.join(date_dir, str(date_taken.year))
            month_dir = os.path.join(year_dir, f"{date_taken.month:02d}")
            
            os.makedirs(year_dir, exist_ok=True)
            os.makedirs(month_dir, exist_ok=True)
            
            # Copy image to appropriate directory
            filename = os.path.basename(img_path)
            new_path = os.path.join(month_dir, filename)
            
            shutil.copy2(img_path, new_path)
            sorted_images.append(new_path)
            
            print(f"Sorted image: {filename} to {date_taken.year}/{date_taken.month:02d}")
                
        except Exception as e:
            print(f"Error processing {os.path.basename(img_path)}: {e}")
    
    print(f"Date sorting complete. Sorted {len(sorted_images)} images.")
    return sorted_images