const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileReady = document.getElementById('file-ready');
const fileNameDisplay = document.querySelector('.file-name');
const fileSizeDisplay = document.querySelector('.file-size');
const transcribeBtn = document.getElementById('transcribe-btn');
const resultSection = document.getElementById('result-section');
const transcriptionText = document.getElementById('transcription-text');
const loading = document.getElementById('loading');
const copyBtn = document.getElementById('copy-btn');
const clearBtn = document.getElementById('clear-btn');

let selectedFile = null;

// Drag and drop handlers
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
    }
});

dropZone.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

function handleFile(file) {
    if (!file.type.startsWith('audio/')) {
        alert('Please upload an audio file.');
        return;
    }
    
    selectedFile = file;
    fileNameDisplay.textContent = file.name;
    fileSizeDisplay.textContent = formatBytes(file.size);
    
    dropZone.classList.add('hidden');
    fileReady.classList.remove('hidden');
    resultSection.classList.add('hidden');
}

transcribeBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    // Show UI states
    fileReady.classList.add('hidden');
    resultSection.classList.remove('hidden');
    loading.classList.remove('hidden');
    transcriptionText.textContent = '';
    transcribeBtn.disabled = true;
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
        const response = await fetch('/transcribe', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Transcription failed on the server.');
        }
        
        const data = await response.json();
        transcriptionText.textContent = data.text;
        
    } catch (error) {
        console.error('Error:', error);
        transcriptionText.innerHTML = `<span style="color: #ef4444;">Error: ${error.message}</span>`;
    } finally {
        loading.classList.add('hidden');
        transcribeBtn.disabled = false;
    }
});

copyBtn.addEventListener('click', () => {
    const text = transcriptionText.textContent;
    navigator.clipboard.writeText(text).then(() => {
        const originalText = copyBtn.textContent;
        copyBtn.textContent = 'Copied!';
        setTimeout(() => copyBtn.textContent = originalText, 2000);
    });
});

clearBtn.addEventListener('click', () => {
    selectedFile = null;
    dropZone.classList.remove('hidden');
    fileReady.classList.add('hidden');
    resultSection.classList.add('hidden');
    fileInput.value = '';
});

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}
