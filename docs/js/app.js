// Main application logic

let compareImages = { img1: null, img2: null };
let decodeImageData = null;

// Tab switching
function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(el => {
        el.classList.remove('active');
        el.classList.add('glass');
    });

    // Show selected tab
    document.getElementById(`content-${tabName}`).classList.remove('hidden');
    document.getElementById(`tab-${tabName}`).classList.remove('glass');
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

// Decode tab: File upload handlers
function setupDecodeUpload() {
    const dropZone = document.getElementById('decode-drop-zone');
    const fileInput = document.getElementById('decode-file');

    dropZone.addEventListener('click', () => fileInput.click());

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
        if (e.dataTransfer.files.length) {
            handleDecodeFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleDecodeFile(e.target.files[0]);
        }
    });
}

// Handle file upload for decoding
function handleDecodeFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            decodeImageData = { img, file };
            document.getElementById('decode-image').src = e.target.result;
            document.getElementById('decode-preview').classList.remove('hidden');
            document.getElementById('decode-btn').disabled = false;
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

// Load example QR codes
async function loadExample(example) {
    const exampleFiles = {
        'challenge1': '../ctf_challenges/challenge1_qr.png',
        'challenge2': '../ctf_challenges/challenge2_qr.png'
    };

    try {
        const response = await fetch(`examples/${example}.png`);
        const blob = await response.blob();
        const file = new File([blob], `${example}.png`, { type: 'image/png' });
        handleDecodeFile(file);
    } catch (error) {
        alert('Example not found. Make sure example files are in docs/examples/');
        console.error(error);
    }
}

// Decode QR code and extract secrets
async function decodeQR() {
    if (!decodeImageData) return;

    const extractPadding = document.getElementById('decode-padding').checked;
    const extractECC = document.getElementById('decode-ecc').checked;
    const kPerBlock = parseInt(document.getElementById('decode-k-per-block').value);

    try {
        const result = await QRStego.decode({
            image: decodeImageData.img,
            extractPadding,
            extractECC,
            kPerBlock
        });

        displayDecodeResults(result);
        document.getElementById('export-decode-btn').disabled = false;
    } catch (error) {
        alert('Error decoding QR code: ' + error.message);
        console.error(error);
    }
}

// Display decode results
function displayDecodeResults(result) {
    const resultsDiv = document.getElementById('decode-results');
    resultsDiv.classList.remove('hidden');

    let html = '';

    // Visible message
    html += `
        <div class="glass rounded-lg p-4">
            <div class="text-sm font-semibold text-accent-primary mb-2">Visible Message</div>
            <div class="code-block rounded p-3">${escapeHtml(result.decoy || '(unable to decode)')}</div>
        </div>
    `;

    // QR properties
    html += `
        <div class="glass rounded-lg p-4">
            <div class="text-sm font-semibold text-accent-primary mb-2">QR Properties</div>
            <div class="text-xs space-y-1">
                <div><span class="text-dark-muted">Version:</span> ${result.version}</div>
                <div><span class="text-dark-muted">Size:</span> ${result.size}×${result.size}</div>
                <div><span class="text-dark-muted">ECC Level:</span> ${result.eccLevel}</div>
                <div><span class="text-dark-muted">Mask:</span> ${result.mask}</div>
            </div>
        </div>
    `;

    // Padding secret
    if (result.paddingSecret !== null) {
        const found = result.paddingSecret !== '';
        html += `
            <div class="glass rounded-lg p-4 ${found ? 'border-l-4 border-accent-success' : ''}">
                <div class="text-sm font-semibold ${found ? 'text-accent-success' : 'text-dark-muted'} mb-2">
                    ${found ? '✓ Padding Secret Found' : 'No Padding Secret'}
                </div>
                ${found ? `<div class="code-block rounded p-3 break-all">${escapeHtml(result.paddingSecret)}</div>` : ''}
            </div>
        `;
    }

    // ECC secret
    if (result.eccSecret !== null) {
        const found = result.eccSecret !== '';
        html += `
            <div class="glass rounded-lg p-4 ${found ? 'border-l-4 border-accent-secondary' : ''}">
                <div class="text-sm font-semibold ${found ? 'text-accent-secondary' : 'text-dark-muted'} mb-2">
                    ${found ? '✓ ECC Secret Found' : 'No ECC Secret'}
                </div>
                ${found ? `<div class="code-block rounded p-3 break-all">${escapeHtml(result.eccSecret)}</div>` : ''}
                ${found ? `<div class="text-xs text-dark-muted mt-2">Extracted using k=${result.kPerBlock} bytes per block</div>` : ''}
            </div>
        `;
    }

    resultsDiv.innerHTML = html;
}

// Export decode report
function exportDecodeReport() {
    // This will be implemented with detailed JSON export
    const report = {
        timestamp: new Date().toISOString(),
        filename: decodeImageData.file.name,
        results: document.getElementById('decode-results').innerText
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'qr-decode-report.json';
    link.click();
    URL.revokeObjectURL(url);
}

// Compare tab: Setup file uploads
function setupCompareUploads() {
    setupCompareDropZone(1);
    setupCompareDropZone(2);
}

function setupCompareDropZone(num) {
    const dropZone = document.getElementById(`compare-drop-zone-${num}`);
    const fileInput = document.getElementById(`compare-file-${num}`);

    dropZone.addEventListener('click', () => fileInput.click());

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
        if (e.dataTransfer.files.length) {
            handleCompareFile(num, e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleCompareFile(num, e.target.files[0]);
        }
    });
}

function handleCompareFile(num, file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            compareImages[`img${num}`] = { img, file };
            document.getElementById(`compare-image-${num}`).src = e.target.result;
            document.getElementById(`compare-preview-${num}`).classList.remove('hidden');

            // Enable compare button if both images loaded
            if (compareImages.img1 && compareImages.img2) {
                document.getElementById('compare-btn').disabled = false;
            }
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

// Compare two QR codes
async function compareQRs() {
    if (!compareImages.img1 || !compareImages.img2) return;

    try {
        const result = await QRStego.compare(compareImages.img1.img, compareImages.img2.img);
        displayCompareResults(result);
        document.getElementById('export-compare-btn').disabled = false;
    } catch (error) {
        alert('Error comparing QR codes: ' + error.message);
        console.error(error);
    }
}

// Display comparison results
function displayCompareResults(result) {
    const resultsDiv = document.getElementById('compare-results');
    resultsDiv.classList.remove('hidden');

    const percentDiff = (result.diffPixels / result.totalPixels * 100).toFixed(2);
    const isDifferent = result.diffPixels > 0;

    let html = `
        <div class="glass rounded-lg p-6">
            <div class="text-xl font-bold mb-4 ${isDifferent ? 'text-accent-warning' : 'text-accent-success'}">
                ${isDifferent ? '⚠ QR Codes are Different' : '✓ QR Codes are Identical'}
            </div>
            <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                    <div class="text-dark-muted">Total Pixels</div>
                    <div class="text-2xl font-bold">${result.totalPixels.toLocaleString()}</div>
                </div>
                <div>
                    <div class="text-dark-muted">Different Pixels</div>
                    <div class="text-2xl font-bold ${isDifferent ? 'text-accent-warning' : 'text-accent-success'}">
                        ${result.diffPixels.toLocaleString()}
                    </div>
                </div>
                <div>
                    <div class="text-dark-muted">Difference</div>
                    <div class="text-2xl font-bold">${percentDiff}%</div>
                </div>
                <div>
                    <div class="text-dark-muted">Same Visible Message</div>
                    <div class="text-2xl font-bold">${result.sameDecoy ? '✓' : '✗'}</div>
                </div>
            </div>
        </div>
    `;

    if (isDifferent && result.diffImageURL) {
        html += `
            <div class="glass rounded-lg p-6">
                <div class="font-semibold mb-3">Visual Difference</div>
                <img src="${result.diffImageURL}" alt="Difference visualization" class="w-full max-w-md mx-auto rounded-lg border border-dark-border">
                <p class="text-xs text-dark-muted mt-3 text-center">White pixels indicate differences</p>
            </div>
        `;
    }

    resultsDiv.innerHTML = html;
}

// Export comparison report
function exportCompareReport() {
    const report = {
        timestamp: new Date().toISOString(),
        file1: compareImages.img1.file.name,
        file2: compareImages.img2.file.name,
        results: document.getElementById('compare-results').innerText
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'qr-comparison-report.json';
    link.click();
    URL.revokeObjectURL(url);
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setupDecodeUpload();
    setupCompareUploads();
});
