// PDF Merger JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // File upload handling
    const fileInput = document.getElementById('files');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }

    // Drag and drop functionality
    setupDragAndDrop();
    
    // File reordering
    setupFileReordering();
    
    // Progress tracking
    setupProgressTracking();
});

function handleFileSelect(event) {
    const files = event.target.files;
    const fileList = document.getElementById('selected-files');
    
    if (fileList) {
        fileList.innerHTML = '';
        let totalSize = 0;
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (file.type === 'application/pdf') {
                totalSize += file.size;
                
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item d-flex justify-content-between align-items-center mb-2';
                fileItem.innerHTML = `
                    <div>
                        <i class="fas fa-file-pdf text-danger me-2"></i>
                        <strong>${file.name}</strong>
                        <small class="text-muted d-block">${(file.size / 1024).toFixed(1)} KB</small>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeFile(${i})">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                fileList.appendChild(fileItem);
            }
        }
        
        // Update total size display
        const totalSizeElement = document.getElementById('total-size');
        if (totalSizeElement) {
            totalSizeElement.textContent = `${(totalSize / 1024).toFixed(1)} KB`;
        }
    }
}

function removeFile(index) {
    // Remove file from input (simplified)
    const fileInput = document.getElementById('files');
    const dt = new DataTransfer();
    const files = fileInput.files;
    
    for (let i = 0; i < files.length; i++) {
        if (i !== index) {
            dt.items.add(files[i]);
        }
    }
    
    fileInput.files = dt.files;
    handleFileSelect({ target: fileInput });
}

function setupDragAndDrop() {
    const dropZone = document.querySelector('.file-drop-zone');
    if (!dropZone) return;

    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        console.log('Dropped files:', files.length);
        
        // TODO: Handle dropped files
    });
}

function setupFileReordering() {
    const fileList = document.getElementById('file-list');
    if (!fileList) return;

    // TODO: Add sortable functionality
    // TODO: Update order when files are moved
}

function setupProgressTracking() {
    // TODO: Track upload progress
    // TODO: Track merge progress
    // TODO: Show real-time status updates
}

function updateTotalPages() {
    const files = document.querySelectorAll('.file-item');
    let totalPages = 0;
    
    files.forEach(file => {
        const pagesText = file.querySelector('.pages-count');
        if (pagesText) {
            totalPages += parseInt(pagesText.textContent) || 0;
        }
    });
    
    const totalPagesElement = document.getElementById('total-pages');
    if (totalPagesElement) {
        totalPagesElement.textContent = totalPages;
    }
}

function updateEstimatedSize() {
    const files = document.querySelectorAll('.file-item');
    let totalSize = 0;
    
    files.forEach(file => {
        const sizeText = file.querySelector('.file-size');
        if (sizeText) {
            const sizeKB = parseFloat(sizeText.textContent.replace(' KB', ''));
            totalSize += sizeKB || 0;
        }
    });
    
    const estimatedSizeElement = document.getElementById('estimated-size');
    if (estimatedSizeElement) {
        estimatedSizeElement.textContent = `${(totalSize / 1024).toFixed(1)} MB`;
    }
}

// API helper functions
async function uploadFiles(files) {
    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Upload error:', error);
        throw error;
    }
}

async function mergePDFs(options) {
    try {
        const response = await fetch('/api/merge', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(options)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Merge error:', error);
        throw error;
    }
}

async function checkStatus(taskId) {
    try {
        const response = await fetch(`/api/status/${taskId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Status check error:', error);
        throw error;
    }
}

// Show upload progress
function showUploadProgress() {
    const progressBar = document.getElementById('upload-progress');
    if (progressBar) {
        progressBar.style.display = 'block';
        progressBar.querySelector('.progress-bar').style.width = '0%';
        
        // Simulate progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 30;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
            }
            progressBar.querySelector('.progress-bar').style.width = progress + '%';
        }, 200);
    }
}

// Hide upload progress
function hideUploadProgress() {
    const progressBar = document.getElementById('upload-progress');
    if (progressBar) {
        progressBar.style.display = 'none';
    }
}