import os
import numpy as np
from PIL import Image
import imagehash
import logging
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_hash_distance(hash1, hash2):
    """
    Calculate normalized hamming distance between two image hashes
    """
    try:
        # Convert string hashes back to imagehash objects if they're strings
        if isinstance(hash1, str):
            h1 = imagehash.hex_to_hash(hash1)
        else:
            h1 = hash1
            
        if isinstance(hash2, str):
            h2 = imagehash.hex_to_hash(hash2)
        else:
            h2 = hash2

        # Calculate distance
        distance = abs(h1 - h2)
        logger.debug(f"Hash distance: {distance}")
        return distance
    except Exception as e:
        logger.error(f"Error calculating hash distance: {str(e)}")
        return float('inf')

def remove_duplicates(image_paths, output_dir):
    """
    Remove duplicate images based on perceptual hashing.
    Uses both difference hash and perceptual hash for better accuracy.
    """
    logger.info(f"Processing {len(image_paths)} images for duplicate removal")
    
    # Create a directory for unique images
    unique_dir = os.path.join(output_dir, "unique_images")
    os.makedirs(unique_dir, exist_ok=True)
    
    # Dictionary to store image hashes
    image_hashes = {}
    
    # Calculate hashes for all images
    for img_path in image_paths:
        try:
            if not os.path.exists(img_path):
                logger.warning(f"File not found: {img_path}")
                continue

            with Image.open(img_path) as img:
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Use both difference hash and perceptual hash for better accuracy
                dhash_value = imagehash.dhash(img)
                phash_value = imagehash.phash(img)
                image_hashes[img_path] = {'dhash': dhash_value, 'phash': phash_value}

        except Exception as e:
            logger.error(f"Error processing image {img_path}: {e}")
            continue

    if not image_hashes:
        logger.warning("No valid images could be processed")
        return []

    # Find duplicates using both hash types
    DHASH_THRESHOLD = 8
    PHASH_THRESHOLD = 12
    groups = []
    processed = set()
    
    # Group similar images
    for img_path in image_hashes.keys():
        if img_path in processed:
            continue

        current_group = [img_path]
        processed.add(img_path)

        # Compare with other images
        for other_path in image_hashes.keys():
            if other_path != img_path and other_path not in processed:
                dhash_distance = calculate_hash_distance(image_hashes[img_path]['dhash'], 
                                                       image_hashes[other_path]['dhash'])
                phash_distance = calculate_hash_distance(image_hashes[img_path]['phash'], 
                                                       image_hashes[other_path]['phash'])
                
                # Consider images duplicate if either hash is within threshold
                if dhash_distance <= DHASH_THRESHOLD or phash_distance <= PHASH_THRESHOLD:
                    current_group.append(other_path)
                    processed.add(other_path)

        if len(current_group) >= 1:  # Add all groups
            groups.append(current_group)
    
    # Process the groups to save unique images
    unique_images = []
    duplicate_count = 0
    
    for group in groups:
        if not group:  # Skip empty groups
            continue
            
        # Get the first image as the unique one
        original_path = group[0]
        
        try:
            # Save the unique image
            with Image.open(original_path) as img:
                filename = os.path.basename(original_path)
                new_path = os.path.join(unique_dir, filename)
                img.save(new_path, quality=95)
                unique_images.append(new_path)
                
            # Log duplicates
            if len(group) > 1:
                duplicate_count += len(group) - 1
                logger.info(f"Found {len(group)-1} duplicates of {os.path.basename(original_path)}")
                for dup in group[1:]:
                    logger.debug(f"  Duplicate: {os.path.basename(dup)}")
        except Exception as e:
            logger.error(f"Error saving unique image {original_path}: {e}")
    
    logger.info(f"Duplicate removal complete. Found {duplicate_count} duplicates out of {len(image_paths)} images.")
    return unique_images