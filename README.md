# Image Processing

## Description

This repository contains various Python scripts for image processing, including face clustering, duplicate removal, blur detection, bad angle removal, date sorting, and background removal. The project uses FastAPI for the backend and includes a frontend with HTML, CSS, and JavaScript files.

## Features

- **Face Clustering**: Cluster images by face detection using OpenCV.
- **Duplicate Removal**: Remove duplicate images based on perceptual hashing.
- **Blur Detection**: Remove blurry images using enhanced blur detection methods.
- **Bad Angle Removal**: Remove images with bad angles using face detection and pose estimation.
- **Date Sorting**: Sort images by date and organize them into folders by year/month.
- **Background Removal**: Remove background from images using the rembg library.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/uditya2004/imageProcessing.git
   cd imageProcessing
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Backend

1. Activate the virtual environment:
   ```bash
   venv\Scripts\activate
   ```

2. Start the FastAPI server:
   ```bash
   python main.py
   ```

### API Endpoints

- **Upload Images**: `POST /api/upload`
  - Upload multiple images to the server.
  - Request: `files` (List of image files)
  - Response: `session_id` (string), `file_count` (integer)

- **Process Images**: `POST /api/process`
  - Process images with selected features.
  - Request: 
    - `session_id` (string)
    - `cluster_face` (boolean)
    - `remove_duplicates_flag` (boolean)
    - `remove_blur` (boolean)
    - `remove_bad_angles_flag` (boolean)
    - `sort_date` (boolean)
    - `remove_background_flag` (boolean)
    - `face_sample` (optional, image file)
  - Response: `session_id` (string), `processed_images` (list of image metadata)

- **Download Results**: `GET /api/download/{session_id}`
  - Download processed images as a ZIP file.
  - Request: `session_id` (string)
  - Response: ZIP file containing processed images

### Frontend Usage

1. Open `index.html` in a web browser.
2. Upload images and select the features you want to apply.
3. Click "Process Images" to start processing.
4. View the results and download the processed images as a ZIP file.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [OpenCV](https://opencv.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [rembg](https://github.com/danielgatis/rembg)
- [ImageHash](https://github.com/JohannesBuchner/imagehash)
