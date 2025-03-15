import os
import cv2
import shutil
import numpy as np
from PIL import Image

def cluster_by_face(image_paths, output_dir, face_sample_path=None):
    """
    Cluster images by face detection using OpenCV.
    If face_sample_path is provided, only keep images with detected faces.
    Otherwise, group all images with detected faces together.
    """
    print(f"Processing {len(image_paths)} images for face detection")
    
    # Load the pre-trained face detection classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Create output directory for images with faces
    faces_dir = os.path.join(output_dir, "images_with_faces")
    os.makedirs(faces_dir, exist_ok=True)
    
    result_paths = []
    for img_path in image_paths:
        try:
            # Read image using OpenCV
            img = cv2.imread(img_path)
            if img is None:
                print(f"Could not read image: {img_path}")
                continue
                
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect faces in the image
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # If faces are found, copy the image to the output directory
            if len(faces) > 0:
                filename = os.path.basename(img_path)
                new_path = os.path.join(faces_dir, filename)
                shutil.copy2(img_path, new_path)
                result_paths.append(new_path)
                
        except Exception as e:
            print(f"Error processing {os.path.basename(img_path)}: {e}")
    
    print(f"Face detection complete. Found faces in {len(result_paths)} images.")
    return result_paths