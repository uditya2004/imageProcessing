document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const imagesCount = document.getElementById('images-count');
    const featuresContainer = document.getElementById('features-container');
    const processButton = document.getElementById('process-button');
    const resultsContainer = document.getElementById('results-container');
    const resultsGrid = document.getElementById('results-grid');
    const downloadButton = document.getElementById('download-button');
    const cameraButton = document.getElementById('camera-button');
    const cameraModal = document.getElementById('camera-modal');
    const cameraPreview = document.getElementById('camera-preview');
    const captureButton = document.getElementById('capture-button');
    const retakeButton = document.getElementById('retake-button');
    const addPhotoButton = document.getElementById('add-photo-button');
    const photoCanvas = document.getElementById('photo-canvas');
    
    // Feature toggles
    const clusterFace = document.getElementById('cluster-face');
    const removeDuplicates = document.getElementById('remove-duplicates');
    const removeBlur = document.getElementById('remove-blur');
    const removeBadAngles = document.getElementById('remove-bad-angles');
    const sortDate = document.getElementById('sort-date');
    const removeBackground = document.getElementById('remove-background');
    
    // Uploaded images storage
    let uploadedImages = [];
    let stream = null;
    
    // Event Listeners
    uploadArea.addEventListener('click', (e) => {
        // Prevent click from propagating to the camera button
        if (e.target !== cameraButton && !cameraButton.contains(e.target)) {
            fileInput.click();
        }
    });
    fileInput.addEventListener('change', handleFileUpload);
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    processButton.addEventListener('click', processImages);
    downloadButton.addEventListener('click', downloadResults);
    cameraButton.addEventListener('click', openCameraModal);
    captureButton.addEventListener('click', capturePhoto);
    retakeButton.addEventListener('click', retakePhoto);
    addPhotoButton.addEventListener('click', addCapturedPhoto);
    
    // Close modals when clicking on the close button or outside the modal
    document.querySelectorAll('.modal .close').forEach(closeBtn => {
        closeBtn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal);
        });
    });
    
    window.addEventListener('click', function(e) {
        document.querySelectorAll('.modal').forEach(modal => {
            if (e.target === modal) {
                closeModal(modal);
            }
        });
    });
    
    // Handle file upload via input
    function handleFileUpload(e) {
        const files = e.target.files;
        if (files.length > 0) {
            addImagesToCollection(files);
        }
    }
    
    // Handle drag over
    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.add('drag-over');
    }
    
    // Handle drag leave
    function handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.remove('drag-over');
    }
    
    // Handle drop
    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            addImagesToCollection(files);
        }
    }
    
    // Add images to collection
    function addImagesToCollection(files) {
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (file.type.startsWith('image/')) {
                uploadedImages.push({
                    file: file,
                    id: Date.now() + i,
                    preview: URL.createObjectURL(file)
                });
            }
        }
        
        updateImagesCount();
        showFeaturesAndProcessButton();
    }
    
    // Update images count
    function updateImagesCount() {
        imagesCount.textContent = `${uploadedImages.length} images selected`;
    }
    
    // Show features and process button
    function showFeaturesAndProcessButton() {
        if (uploadedImages.length > 0) {
            featuresContainer.style.display = 'block';
            processButton.style.display = 'flex';
        } else {
            featuresContainer.style.display = 'none';
            processButton.style.display = 'none';
        }
    }
    
    // Process images based on selected features
    function processImages() {
        // Show loading state
        processButton.disabled = true;
        processButton.textContent = 'Processing...';
        
        // Create form data for the API request
        const formData = new FormData();
        
        // Add all images to the form data
        uploadedImages.forEach(img => {
            formData.append('files', img.file);
        });
        
        // First upload the images
        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            const sessionId = data.session_id;
            
            // Create form data for processing
            const processFormData = new FormData();
            processFormData.append('session_id', sessionId);
            processFormData.append('cluster_face', clusterFace.checked);
            processFormData.append('remove_duplicates_flag', removeDuplicates.checked);
            processFormData.append('remove_blur', removeBlur.checked);
            processFormData.append('remove_bad_angles_flag', removeBadAngles.checked);
            processFormData.append('sort_date', sortDate.checked);
            processFormData.append('remove_background_flag', removeBackground.checked);
            
            // If face clustering is selected and we have a sample face, add it
            if (clusterFace.checked && uploadedImages.length > 0) {
                // Use the first image as a sample face
                processFormData.append('face_sample', uploadedImages[0].file);
            }
            
            // Process the images
            return fetch('/api/process', {
                method: 'POST',
                body: processFormData
            });
        })
        .then(response => response.json())
        .then(data => {
            // Store the session ID for download
            window.currentSessionId = data.session_id;
            
            // Display the processing statistics
            displayStats(data.stats);
            
            // Display the processed images
            displayResults(data.processed_images);
            
            // Reset button state
            processButton.disabled = false;
            processButton.innerHTML = '<img src="assets/process-icon.svg" alt="Process" class="process-icon">Process Images';
        })
        .catch(error => {
            console.error('Error processing images:', error);
            alert('Error processing images. Please try again.');
            
            // Reset button state
            processButton.disabled = false;
            processButton.innerHTML = '<img src="assets/process-icon.svg" alt="Process" class="process-icon">Process Images';
        });
    }
    
    // Simulate processing based on selected features
    function simulateProcessing() {
        // In a real app, this would be handled by the backend
        // For now, we'll just return the uploaded images with some metadata
        return uploadedImages.map(img => {
            return {
                id: img.id,
                preview: img.preview,
                filename: img.file.name,
                size: formatFileSize(img.file.size),
                date: new Date(img.file.lastModified).toLocaleDateString()
            };
        });
    }
    
    // Display statistics
    function displayStats(stats) {
        const statsGrid = document.getElementById('stats-grid');
        statsGrid.innerHTML = '';
        
        // If stats is not provided, show default message
        if (!stats) {
            const noStatsItem = document.createElement('div');
            noStatsItem.className = 'stat-item';
            noStatsItem.innerHTML = '<p>No statistics available</p>';
            statsGrid.appendChild(noStatsItem);
            return;
        }
        
        // Create stat items for each statistic
        const statItems = [
            { label: 'Total Images', value: stats.total_images || 0 },
            { label: 'Duplicates Removed', value: stats.duplicates_removed || 0 },
            { label: 'Blur Images Removed', value: stats.blur_removed || 0 },
            { label: 'Bad Angles Removed', value: stats.bad_angles_removed || 0 },
            { label: 'Face Clusters', value: stats.face_clusters || 0 },
            { label: 'Backgrounds Removed', value: stats.backgrounds_removed || 0 }
        ];
        
        statItems.forEach(item => {
            const statItem = document.createElement('div');
            statItem.className = 'stat-item';
            
            const statValue = document.createElement('div');
            statValue.className = 'stat-value';
            statValue.textContent = item.value;
            
            const statLabel = document.createElement('div');
            statLabel.className = 'stat-label';
            statLabel.textContent = item.label;
            
            statItem.appendChild(statValue);
            statItem.appendChild(statLabel);
            
            statsGrid.appendChild(statItem);
        });
    }
    
    // Display results
    function displayResults(images) {
        resultsGrid.innerHTML = '';
        
        // Store images for modal navigation
        window.galleryImages = images;
        window.currentImageIndex = 0;
        
        images.forEach((img, index) => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            
            // Create image element
            const imgElement = document.createElement('img');
            
            // Check if we have a preview URL (from local) or need to create one from path (from server)
            if (img.preview) {
                imgElement.src = img.preview;
            } else if (img.path) {
                // For images from the server, create a URL using the filename
                imgElement.src = `/temp/processed/${window.currentSessionId}/${img.filename}`;
            }
            
            imgElement.alt = img.filename;
            
            // Add click event for modal preview
            imgElement.addEventListener('click', () => {
                openImageModal(index);
            });
            
            // Create info div
            const infoDiv = document.createElement('div');
            infoDiv.className = 'result-info';
            
            // Add filename
            const filenamePara = document.createElement('p');
            filenamePara.textContent = img.filename;
            
            // Add size
            const sizePara = document.createElement('p');
            if (typeof img.size === 'number') {
                sizePara.textContent = formatFileSize(img.size);
            } else {
                sizePara.textContent = img.size;
            }
            
            // Add date
            const datePara = document.createElement('p');
            datePara.textContent = img.date;
            
            // Append all elements
            infoDiv.appendChild(filenamePara);
            infoDiv.appendChild(sizePara);
            infoDiv.appendChild(datePara);
            
            resultItem.appendChild(imgElement);
            resultItem.appendChild(infoDiv);
            
            resultsGrid.appendChild(resultItem);
        });
        
        resultsContainer.style.display = 'block';
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Download results
    function downloadResults() {
        if (window.currentSessionId) {
            // Create download URL
            const downloadUrl = `/api/download/${window.currentSessionId}`;
            
            // Create a temporary link element
            const downloadLink = document.createElement('a');
            downloadLink.href = downloadUrl;
            downloadLink.download = `processed_images_${window.currentSessionId}.zip`;
            
            // Append to body, click and remove
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
        } else {
            alert('No processed images available for download. Please process images first.');
        }
    }
    
    // Modal functionality
    const modal = document.getElementById('image-modal');
    const modalImg = document.getElementById('modal-image');
    const closeBtn = document.querySelector('.close');
    const prevBtn = document.querySelector('.prev');
    const nextBtn = document.querySelector('.next');
    
    // Open image modal
    function openImageModal(index) {
        window.currentImageIndex = index;
        const img = window.galleryImages[index];
        
        // Set the image source
        if (img.preview) {
            modalImg.src = img.preview;
        } else if (img.path) {
            modalImg.src = `/temp/processed/${window.currentSessionId}/${img.filename}`;
        }
        
        modal.style.display = 'block';
    }
    
    // Close modal
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    // Close modal when clicking outside the image
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Navigate to previous image
    prevBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        navigateImage(-1);
    });
    
    // Navigate to next image
    nextBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        navigateImage(1);
    });
    
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (modal.style.display === 'block') {
            if (e.key === 'ArrowLeft') {
                navigateImage(-1);
            } else if (e.key === 'ArrowRight') {
                navigateImage(1);
            } else if (e.key === 'Escape') {
                modal.style.display = 'none';
            }
        }
    });
    
    // Navigate to next or previous image
    function navigateImage(step) {
        if (!window.galleryImages || window.galleryImages.length === 0) return;
        
        window.currentImageIndex = (window.currentImageIndex + step + window.galleryImages.length) % window.galleryImages.length;
        openImageModal(window.currentImageIndex);
    }

    // Open camera modal and initialize camera
    function openCameraModal() {
        cameraModal.style.display = 'block';
        initCamera();
    }
    
    // Initialize camera
    function initCamera() {
        // Reset UI state
        captureButton.style.display = 'block';
        retakeButton.style.display = 'none';
        addPhotoButton.style.display = 'none';
        cameraPreview.style.display = 'block';
        photoCanvas.style.display = 'none';
        
        // Check if browser supports getUserMedia
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(function(mediaStream) {
                    stream = mediaStream;
                    cameraPreview.srcObject = mediaStream;
                    cameraPreview.play();
                })
                .catch(function(error) {
                    console.error('Error accessing camera:', error);
                    alert('Unable to access camera. Please make sure you have granted camera permissions.');
                    closeModal(cameraModal);
                });
        } else {
            alert('Your browser does not support camera access. Please try a different browser.');
            closeModal(cameraModal);
        }
    }
    
    // Capture photo from camera
    function capturePhoto() {
        const context = photoCanvas.getContext('2d');
        
        // Set canvas dimensions to match the video
        photoCanvas.width = cameraPreview.videoWidth;
        photoCanvas.height = cameraPreview.videoHeight;
        
        // Draw the current video frame to the canvas
        context.drawImage(cameraPreview, 0, 0, photoCanvas.width, photoCanvas.height);
        
        // Hide video and show canvas with captured image
        cameraPreview.style.display = 'none';
        photoCanvas.style.display = 'block';
        
        // Update buttons
        captureButton.style.display = 'none';
        retakeButton.style.display = 'inline-block';
        addPhotoButton.style.display = 'inline-block';
    }
    
    // Retake photo
    function retakePhoto() {
        // Show video preview again
        cameraPreview.style.display = 'block';
        photoCanvas.style.display = 'none';
        
        // Update buttons
        captureButton.style.display = 'inline-block';
        retakeButton.style.display = 'none';
        addPhotoButton.style.display = 'none';
    }
    
    // Add captured photo to the collection
    function addCapturedPhoto() {
        // Convert canvas to blob
        photoCanvas.toBlob(function(blob) {
            // Create a file from the blob
            const fileName = `camera_photo_${Date.now()}.jpg`;
            const file = new File([blob], fileName, { type: 'image/jpeg' });
            
            // Add to uploaded images collection
            uploadedImages.push({
                file: file,
                id: Date.now(),
                preview: URL.createObjectURL(blob)
            });
            
            // Update UI
            updateImagesCount();
            showFeaturesAndProcessButton();
            
            // Close the camera modal
            closeModal(cameraModal);
        }, 'image/jpeg', 0.9);
    }
    
    // Close modal and stop camera if needed
    function closeModal(modal) {
        modal.style.display = 'none';
        
        // If closing camera modal, stop the camera stream
        if (modal === cameraModal && stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
    }
});