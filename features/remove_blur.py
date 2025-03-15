import os
import cv2
import numpy as np
from PIL import Image

# Configuration / Tunable Parameters
# Global threshold for the combined focus measure (tuned based on validation data)
DEFAULT_BLUR_THRESHOLD = 120

# Local (patch-based) threshold: base value and required fraction of blurry patches
LOCAL_BLUR_THRESHOLD = 100  
FRACTION_BLURRY = 0.4  
PATCH_GRID = (5, 5)  # You might experiment with 4x4, 5x5, etc.

# Weights for the combined global focus measure (should be normalized to sum to 1)
LAPLACIAN_WEIGHT = 0.35
TENENGRAD_WEIGHT = 0.30
FFT_WEIGHT = 0.35

# Improved FFT: high-pass filter size (fraction of smaller dimension)
SIZE_PERCENT = 0.1

def multi_scale_laplacian_variance(gray, levels=3):
    """
    Computes Laplacian variance over multiple scales.
    This captures both fine and coarse blur details.
    """
    score = 0.0
    current = gray.copy()
    for _ in range(levels):
        lap = cv2.Laplacian(current, cv2.CV_64F)
        score += np.var(lap)
        if current.shape[0] > 1 and current.shape[1] > 1:
            current = cv2.pyrDown(current)
    return score / levels

def improved_fft_blur_detection(gray_image, size_percent=0.1):
    """
    Enhanced FFT-based focus measure:
      - Computes FFT and shifts it to center low frequencies.
      - Zeros out a central square (size determined by size_percent).
      - Returns the mean log-magnitude of the remaining high-frequency components.
    """
    dft = np.fft.fft2(gray_image)
    dft_shift = np.fft.fftshift(dft)
    h, w = gray_image.shape
    half_size = int(min(h, w) * size_percent // 2)
    cy, cx = h // 2, w // 2
    dft_shift[cy - half_size : cy + half_size, cx - half_size : cx + half_size] = 0
    f_ishift = np.fft.ifftshift(dft_shift)
    img_back = np.fft.ifft2(f_ishift)
    img_back = np.abs(img_back)
    eps = 1e-10
    magnitude = 20 * np.log10(img_back + eps)
    return np.mean(magnitude)

def patch_based_blur_check(gray, patch_grid=(4, 4), local_threshold=80, fraction_blurry=0.3):
    """
    Divides the image into patches and computes Laplacian variance for each.
    The threshold for each patch is dynamically adjusted based on its mean intensity.
    If the fraction of patches below the dynamic threshold exceeds fraction_blurry,
    the image is flagged as blurry locally.
    """
    rows, cols = patch_grid
    h, w = gray.shape
    patch_h = h // rows
    patch_w = w // cols

    blurry_patches = 0
    total_patches = rows * cols

    for r in range(rows):
        for c in range(cols):
            y1 = r * patch_h
            y2 = (r + 1) * patch_h if (r < rows - 1) else h
            x1 = c * patch_w
            x2 = (c + 1) * patch_w if (c < cols - 1) else w
            patch = gray[y1:y2, x1:x2]
            patch_mean = np.mean(patch)
            patch_factor = 1.0
            if patch_mean < 50:
                patch_factor = 0.8
            elif patch_mean > 200:
                patch_factor = 1.2
            dynamic_threshold = local_threshold * patch_factor

            lap = cv2.Laplacian(patch, cv2.CV_64F)
            lap_var = np.var(lap)
            if lap_var < dynamic_threshold:
                blurry_patches += 1

    return (blurry_patches / total_patches) > fraction_blurry

def resize_image(image, width=1024):
    """
    Resizes the image to the specified maximum width while preserving aspect ratio.
    """
    h, w = image.shape[:2]
    if w <= width:
        return image
    aspect_ratio = h / w
    new_height = int(width * aspect_ratio)
    return cv2.resize(image, (width, new_height), interpolation=cv2.INTER_AREA)

def enhanced_blur_detection(image_path, threshold=DEFAULT_BLUR_THRESHOLD):
    """
    Computes a combined focus score using:
      - Multi-scale Laplacian variance,
      - Tenengrad gradient magnitude, and
      - FFT-based high-frequency energy.
    The final score is compared against an adaptive threshold based on image brightness.
    Additionally, a patch-based method computes local blur scores with dynamic thresholds.
    The image is classified as blurry if either the global or the local measure indicates blur.
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            return 0, True

        # Resize image to a max width of 1024 (preserving aspect ratio)
        image = resize_image(image, width=1024)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Global focus measures:
        laplacian_var = multi_scale_laplacian_variance(gray, levels=3)
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        tenengrad = np.mean(sobel_x**2 + sobel_y**2)
        fft_score = improved_fft_blur_detection(gray, size_percent=SIZE_PERCENT)

        # Combine the global measures using the tuned weights.
        combined_score = (LAPLACIAN_WEIGHT * laplacian_var) + (TENENGRAD_WEIGHT * tenengrad) + (FFT_WEIGHT * fft_score)

        # Adaptive scaling based on overall brightness (mean intensity).
        mean_intensity = np.mean(gray)
        adaptive_factor = 1.0
        if mean_intensity < 50:
            adaptive_factor = 0.8
        elif mean_intensity > 200:
            adaptive_factor = 1.2
        final_threshold = threshold * adaptive_factor

        global_blurry = bool(combined_score < final_threshold)

        # Local (patch-based) focus measure.
        local_blurry = patch_based_blur_check(
            gray,
            patch_grid=PATCH_GRID,
            local_threshold=LOCAL_BLUR_THRESHOLD,
            fraction_blurry=FRACTION_BLURRY
        )

        # Classify image as blurry if either global or local measures indicate blur.
        is_blurry = (global_blurry or local_blurry)
        return float(combined_score), is_blurry

    except Exception as e:
        print(f"Error processing image {image_path}: {str(e)}")
        return 0, True

def remove_blur_images(image_paths, output_dir):
    """
    Remove blurry images using enhanced blur detection methods:
    - Multi-scale Laplacian variance
    - Tenengrad gradient magnitude
    - FFT-based high-frequency energy analysis
    - Patch-based blur checking with dynamic thresholds
    """
    print(f"Processing {len(image_paths)} images for blur detection")
    
    # Create a directory for sharp images
    sharp_dir = os.path.join(output_dir, "sharp_images")
    os.makedirs(sharp_dir, exist_ok=True)
    
    sharp_images = []
    
    for img_path in image_paths:
        try:
            # Run enhanced blur detection on the image
            blur_score, is_blurry = enhanced_blur_detection(img_path)
            
            # If image is sharp enough, keep it
            if not is_blurry:
                filename = os.path.basename(img_path)
                new_path = os.path.join(sharp_dir, filename)
                
                # Read and save the image to the new path
                img = cv2.imread(img_path)
                cv2.imwrite(new_path, img)
                sharp_images.append(new_path)
                print(f"Sharp image: {filename}, Blur score: {blur_score:.2f}")
            else:
                print(f"Blurry image: {os.path.basename(img_path)}, Blur score: {blur_score:.2f}")
                
        except Exception as e:
            print(f"Error processing {os.path.basename(img_path)}: {e}")
    
    print(f"Blur detection complete. Found {len(image_paths) - len(sharp_images)} blurry images.")
    return sharp_images