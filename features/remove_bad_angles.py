import os
import cv2
import numpy as np
from PIL import Image

def remove_bad_angles(image_paths, output_dir):
    """
    Remove images with bad angles using face detection and pose estimation.
    """
    print(f"Processing {len(image_paths)} images for bad angle detection")
    
    # Create a directory for good angle images
    good_angles_dir = os.path.join(output_dir, "good_angles")
    os.makedirs(good_angles_dir, exist_ok=True)
    
    # Load face detector
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    good_angle_images = []
    
    for img_path in image_paths:
        try:
            # Read image
            img = cv2.imread(img_path)
            if img is None:
                print(f"Could not read {os.path.basename(img_path)}")
                continue
                
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            # If no faces detected, consider it a bad angle
            if len(faces) == 0:
                print(f"No faces detected in {os.path.basename(img_path)}")
                continue
            
            # Check face size and position
            img_height, img_width = img.shape[:2]
            good_angle = False
            
            for (x, y, w, h) in faces:
                # Calculate face area ratio
                face_area = w * h
                img_area = img_width * img_height
                face_ratio = face_area / img_area
                
                # Calculate face position (center of the face)
                face_center_x = x + w/2
                face_center_y = y + h/2
                
                # Calculate distance from image center
                img_center_x = img_width / 2
                img_center_y = img_height / 2
                center_distance = np.sqrt((face_center_x - img_center_x)**2 + (face_center_y - img_center_y)**2)
                center_distance_ratio = center_distance / (np.sqrt(img_width**2 + img_height**2) / 2)
                
                # Check if face is reasonably sized and centered
                if face_ratio > 0.05 and center_distance_ratio < 0.5:
                    good_angle = True
                    break
            
            if good_angle:
                filename = os.path.basename(img_path)
                new_path = os.path.join(good_angles_dir, filename)
                
                # Save the image to the new path
                cv2.imwrite(new_path, img)
                good_angle_images.append(new_path)
                print(f"Good angle image: {filename}")
            else:
                print(f"Bad angle image: {os.path.basename(img_path)}")
                
        except Exception as e:
            print(f"Error processing {os.path.basename(img_path)}: {e}")
    
    print(f"Bad angle detection complete. Found {len(image_paths) - len(good_angle_images)} bad angle images.")
    return good_angle_images