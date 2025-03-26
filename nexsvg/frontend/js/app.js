const API_URL = 'http://localhost:8000';

class ImageConverter {
    constructor() {
        this.dropZone = document.querySelector('.drop-zone');
        this.fileInput = document.getElementById('fileInput');
        this.preview = document.getElementById('preview');
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropZone.classList.add('border-blue-600');
        });

        this.dropZone.addEventListener('dragleave', () => {
            this.dropZone.classList.remove('border-blue-600');
        });

        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('border-blue-600');
            this.handleFiles(e.dataTransfer.files);
        });

        this.fileInput.addEventListener('change', () => {
            this.handleFiles(this.fileInput.files);
        });
    }

    async convertToSVG(fileData, container) {
        const button = container.querySelector('button');
        
        try {
            button.classList.add('loading');
            button.textContent = 'Converting...';

            // Convert base64 back to file
            const response = await fetch(fileData);
            const blob = await response.blob();
            const file = new File([blob], 'image.png', { type: 'image/png' });

            const formData = new FormData();
            formData.append('file', file);

            console.log('Sending request to backend...');
            const convertResponse = await fetch(`${API_URL}/convert`, {
                method: 'POST',
                body: formData
            });

            console.log('Received response:', convertResponse.status);
            const contentType = convertResponse.headers.get('content-type');
            
            if (!convertResponse.ok) {
                const errorData = await convertResponse.json();
                throw new Error(errorData.detail || errorData.error || 'Conversion failed');
            }

            let svgData;
            if (contentType && contentType.includes('application/json')) {
                const jsonResponse = await convertResponse.json();
                if (jsonResponse.error) {
                    throw new Error(jsonResponse.error);
                }
                svgData = jsonResponse.svg || jsonResponse;
            } else {
                svgData = await convertResponse.text();
            }

            console.log('Successfully received SVG data');
            this.displaySuccess(container, svgData, button);

        } catch (error) {
            console.error('Conversion error:', error);
            this.displayError(container, error, button);
        } finally {
            button.classList.remove('loading');
        }
    }

    displaySuccess(container, svgData, button) {
        const svgPreview = document.createElement('div');
        svgPreview.className = 'svg-preview';
        svgPreview.innerHTML = `
            <h3 class="text-sm font-medium text-gray-900 mb-2">SVG Preview:</h3>
            <div class="max-h-48 overflow-auto">
                ${svgData}
            </div>
            <a href="data:image/svg+xml;base64,${btoa(svgData)}" 
               download="converted.svg"
               class="download-button">
                Download SVG
            </a>
        `;
        
        container.appendChild(svgPreview);
        button.textContent = 'Converted!';
        button.disabled = true;
        button.classList.remove('bg-blue-600', 'hover:bg-blue-700');
        button.classList.add('bg-gray-400');
    }

    displayError(container, error, button) {
        button.textContent = 'Error';
        button.classList.remove('bg-blue-600', 'hover:bg-blue-700');
        button.classList.add('bg-red-600');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        errorDiv.textContent = `Error: ${error.message}`;
        container.appendChild(errorDiv);
    }

    handleFiles(files) {
        Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const div = document.createElement('div');
                    div.className = 'bg-white p-4 rounded-lg shadow-sm';
                    div.innerHTML = `
                        <img src="${e.target.result}" class="preview-image">
                        <p class="text-sm text-gray-500 truncate">${file.name}</p>
                        <button class="mt-2 w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition">
                            Convert to SVG
                        </button>
                    `;
                    const button = div.querySelector('button');
                    button.addEventListener('click', () => this.convertToSVG(e.target.result, div));
                    this.preview.appendChild(div);
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    new ImageConverter();
}); 