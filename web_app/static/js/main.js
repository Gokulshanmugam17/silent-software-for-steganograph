let state = {
    mediaType: 'text',
    operation: 'hide',
    dataType: 'text'
};


// This will be initialized at the end of the file in a single consolidated listener

// --- State Management ---

function setMediaType(type) {
    state.mediaType = type;
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.type === type);
    });

    // Update Header (Title, Desc, Icon)
    const config = {
        text: { title: 'Text Steganography', icon: 'fa-file-lines', desc: 'Hide messages using zero-width characters' },
        image: { title: 'Image Steganography', icon: 'fa-image', desc: 'LSB encoding in PNG, BMP, TIFF' },
        audio: { title: 'Audio Steganography', icon: 'fa-music', desc: 'Hide data in MP3, WAV, MPEG, etc.' },
        video: { title: 'Video Steganography', icon: 'fa-film', desc: 'Frame-based data embedding' },
        multilayer: { title: 'Multi-Layer Steganography', icon: 'fa-layer-group', desc: 'Recursive hiding across multiple layers' },
        history: { title: 'Operation History', icon: 'fa-clock-rotate-left', desc: 'Track your secure transmissions' }
    };

    const current = config[type] || config.text;

    const titleEl = document.getElementById('page-title');
    const descEl = document.getElementById('page-desc');
    const iconEl = document.getElementById('header-icon');

    if (titleEl) titleEl.textContent = current.title;
    if (descEl) descEl.textContent = current.desc;
    if (iconEl) iconEl.className = `fa-solid ${current.icon}`;

    // Show/hide appropriate inputs based on media type
    const isText = type === 'text';
    const isImage = type === 'image';
    const isMulti = type === 'multilayer';

    // Hide section
    const coverTextGroup = document.getElementById('cover-text-group');
    const sourceUploadGroup = document.getElementById('source-upload-group');
    if (coverTextGroup) coverTextGroup.style.display = isText ? 'block' : 'none';
    if (sourceUploadGroup) sourceUploadGroup.style.display = isText ? 'none' : 'block';

    // Show/hide image comparison container
    const imageComparison = document.getElementById('image-comparison-display');
    if (imageComparison) {
        imageComparison.style.display = isImage ? 'none' : 'none'; // Hidden by default, shown after processing
    }

    // Extract section
    const stegoTextGroup = document.getElementById('stego-text-group');
    const stegoUploadGroup = document.getElementById('stego-upload-group');
    if (stegoTextGroup) stegoTextGroup.style.display = isText ? 'block' : 'none';
    if (stegoUploadGroup) stegoUploadGroup.style.display = isText ? 'none' : 'block';

    // Toggle main visibility
    const hideSection = document.getElementById('hide-section');
    const extractSection = document.getElementById('extract-section');
    const multilayerSection = document.getElementById('multilayer-section');
    const historySection = document.getElementById('history-section');
    const tabs = document.querySelector('.tabs');
    const opTabs = document.getElementById('operation-tabs');

    // Reset all sections first
    if (hideSection) hideSection.style.display = 'none';
    if (extractSection) extractSection.style.display = 'none';
    if (multilayerSection) multilayerSection.style.display = 'none';
    if (historySection) historySection.style.display = 'none';
    if (tabs) tabs.style.display = 'none';
    if (opTabs) opTabs.style.display = 'none';

    if (type === 'multilayer') {
        if (multilayerSection) multilayerSection.style.display = 'block';
    } else if (type === 'history') {
        if (historySection) historySection.style.display = 'block';
        fetchHistory();
    } else {
        // Normal modes (text, image, audio, video)
        if (state.operation === 'hide' && hideSection) hideSection.style.display = 'block';
        if (state.operation === 'extract' && extractSection) extractSection.style.display = 'block';
        if (tabs) tabs.style.display = 'flex';
        if (opTabs) opTabs.style.display = 'flex';
    }

    updateSwitchers(type, state.operation);

    updateUI();
}

function updateSwitchers(mediaType, operation) {
    const dataSwitchers = document.querySelectorAll('.data-type-switch');
    dataSwitchers.forEach(switcher => {
        const isExtractCard = switcher.closest('#extract-section') !== null;
        const isText = mediaType === 'text';
        const isMulti = mediaType === 'multilayer';

        if (isExtractCard) {
            // Extraction: Always hide for all types (now automatic like Multi-Layer)
            switcher.style.display = 'none';
        } else {
            // Hide: hide for text/multi, show for others
            switcher.style.display = (isText || isMulti) ? 'none' : 'flex';
        }
    });
}

function setOperation(op) {
    state.operation = op;
    document.querySelectorAll('.tab-btn').forEach((btn, index) => {
        btn.classList.toggle('active', (index === 0 && op === 'hide') || (index === 1 && op === 'extract'));
    });

    // Toggle Sections
    if (state.mediaType !== 'multilayer') {
        document.getElementById('hide-section').classList.toggle('active', op === 'hide');
        document.getElementById('extract-section').classList.toggle('active', op === 'extract');

        // Ensure display block/none is set alongside active class
        document.getElementById('hide-section').style.display = op === 'hide' ? 'block' : 'none';
        document.getElementById('extract-section').style.display = op === 'extract' ? 'block' : 'none';
    }

    updateSwitchers(state.mediaType, op);
}

function setDataType(type) {
    state.dataType = type;
    const isHide = state.operation === 'hide';
    const container = isHide ? document.getElementById('hide-section') : document.getElementById('extract-section');

    container.querySelectorAll('.switch-label').forEach((label, index) => {
        label.classList.toggle('active', (index === 0 && type === 'text') || (index === 1 && type === 'media'));
    });

    if (isHide) {
        document.getElementById('text-input-group').style.display = type === 'text' ? 'block' : 'none';
        document.getElementById('media-input-group').style.display = type === 'media' ? 'block' : 'none';
    }
}

function updateUI() {
    // Media-specific adjustments can go here if needed
}

function setMLDataType(type) {
    const container = document.getElementById('multilayer-section');
    if (!container) return;

    // Target only the hide card labels
    const labels = container.querySelectorAll('.glass-card:first-child .switch-label');
    labels.forEach((label, index) => {
        label.classList.toggle('active', (index === 0 && type === 'text') || (index === 1 && type === 'media'));
    });

    const textGroup = document.getElementById('ml-text-input-group');
    const mediaGroup = document.getElementById('ml-media-input-group');

    if (textGroup) textGroup.style.display = type === 'text' ? 'block' : 'none';
    if (mediaGroup) mediaGroup.style.display = type === 'media' ? 'block' : 'none';

    state.mlDataType = type;
}

function setMLExtractDataType(type) {
    const container = document.getElementById('multilayer-section');
    if (!container) return;

    // Target only the extract card labels
    const labels = container.querySelectorAll('.glass-card:last-child .switch-label');
    labels.forEach((label, index) => {
        label.classList.toggle('active', (index === 0 && type === 'text') || (index === 1 && type === 'media'));
    });

    state.mlExtractDataType = type;
}

function toggleMLManualConfig(isAuto) {
    const manualConfig = document.getElementById('ml-manual-extract-config');
    const autoKeys = document.getElementById('ml-auto-extract-keys');

    if (manualConfig) manualConfig.style.display = isAuto ? 'none' : 'block';
    if (autoKeys) autoKeys.style.display = isAuto ? 'block' : 'none';
}

// --- File Handling ---

function displayFileInfo(info, file) {
    if (!info || !file) return;
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
    info.innerHTML =
        `<span style="font-weight:600;">${file.name}</span>` +
        `<span style="margin-left:8px;font-size:0.78em;opacity:0.65;">${sizeMB} MB</span>`;
}

function initDragAndDrop() {
    const areas = document.querySelectorAll('.upload-area');

    areas.forEach(area => {
        const input = area.querySelector('input');
        const info = area.querySelector('.file-info');

        area.addEventListener('click', () => input.click());

        input.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                displayFileInfo(info, e.target.files[0]);
                area.classList.add('has-file');
            }
        });

        area.addEventListener('dragover', (e) => {
            e.preventDefault();
            area.classList.add('dragover');
        });

        area.addEventListener('dragleave', () => {
            area.classList.remove('dragover');
        });

        area.addEventListener('drop', (e) => {
            e.preventDefault();
            area.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                input.files = e.dataTransfer.files;
                displayFileInfo(info, e.dataTransfer.files[0]);
                area.classList.add('has-file');
            }
        });
    });
}

// --- Helpers ---

function togglePassword(icon) {
    const input = icon.previousElementSibling;
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

function showToast(msg, isError = false) {
    const toast = document.getElementById('toast');
    const msgEl = document.getElementById('toast-message');
    msgEl.textContent = msg;
    toast.style.borderLeft = isError ? '4px solid #ef4444' : '4px solid #10b981';
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

function toggleLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = show ? 'flex' : 'none';
}

// --- Dynamic Layer UI Management ---

function updateLayerUploadUI(layer) {
    const typeSelect = document.getElementById(`ml-${layer}-type`);
    const uploadArea = document.getElementById(`ml-${layer}-upload`);
    const textArea = document.getElementById(`ml-${layer}-text`);
    const icon = uploadArea?.querySelector('i');
    const previewContainer = document.getElementById(`ml-${layer === 'layer1' ? 'l1' : 'l2'}-preview-container`);

    if (!typeSelect || !uploadArea) return;

    // Reset preview on type change
    if (previewContainer) previewContainer.style.display = 'none';

    const type = typeSelect.value;

    // Update icon based on type
    const icons = {
        image: 'fa-file-image',
        audio: 'fa-file-audio',
        video: 'fa-file-video'
    };

    if (icon && icons[type]) {
        icon.className = `fa-solid ${icons[type]}`;
    }

    if (type === 'text') {
        uploadArea.style.display = 'none';
        if (textArea) textArea.style.display = 'block';
    } else {
        uploadArea.style.display = 'block';
        if (textArea) textArea.style.display = 'none';
    }
}

function updateExtractLayerUI(layer) {
    const typeSelect = document.getElementById(`ml-ex-${layer}-type`);
    if (!typeSelect) return;

    const type = typeSelect.value;
}

function initLayerPreviews() {
    ['layer1', 'layer2'].forEach(layer => {
        const input = document.getElementById(`ml-${layer}-file`);
        const previewImg = document.getElementById(`ml-${layer === 'layer1' ? 'l1' : 'l2'}-preview`);
        const previewContainer = document.getElementById(`ml-${layer === 'layer1' ? 'l1' : 'l2'}-preview-container`);

        if (input) {
            input.addEventListener('change', (e) => {
                if (e.target.files && e.target.files[0] && e.target.files[0].type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function (event) {
                        if (previewImg) {
                            previewImg.src = event.target.result;
                            if (previewContainer) previewContainer.style.display = 'block';
                        }
                    };
                    reader.readAsDataURL(e.target.files[0]);
                } else {
                    if (previewContainer) previewContainer.style.display = 'none';
                }
            });
        }
    });
}

// --- Helper Functions for Output Display ---

function displayHideOutput(result, mediaType) {
    // Hide all output areas first
    const stegoOutputArea = document.getElementById('stego-output-area');
    const imageComparisonArea = document.getElementById('image-comparison-display');
    const audioDisplayArea = document.getElementById('audio-output-display');
    const videoDisplayArea = document.getElementById('video-output-display');

    if (stegoOutputArea) stegoOutputArea.style.display = 'none';
    if (imageComparisonArea) imageComparisonArea.style.display = 'none';
    if (audioDisplayArea) audioDisplayArea.style.display = 'none';
    if (videoDisplayArea) videoDisplayArea.style.display = 'none';

    // Show image comparison for image media type
    if (mediaType === 'image' && result.download_url) {
        const sourceFileInput = document.getElementById('source-file');
        let coverImageUrl = null;

        // Get cover image preview if available
        if (sourceFileInput && sourceFileInput.files && sourceFileInput.files[0]) {
            const coverFile = sourceFileInput.files[0];
            if (coverFile.type.startsWith('image/')) {
                coverImageUrl = URL.createObjectURL(coverFile);
            }
        }

        // Convert relative URL to absolute if needed
        let hiddenImageUrl = result.download_url;
        if (hiddenImageUrl && !hiddenImageUrl.startsWith('http') && !hiddenImageUrl.startsWith('data:')) {
            // If it's a relative path, make it absolute
            if (hiddenImageUrl.startsWith('/')) {
                hiddenImageUrl = window.location.origin + hiddenImageUrl;
            } else {
                hiddenImageUrl = window.location.origin + '/' + hiddenImageUrl;
            }
        }

        // Show image comparison with cover and hidden images
        showImageComparison(coverImageUrl, hiddenImageUrl, result);
    }
    else if (mediaType === 'audio' && result.download_url) {
        if (audioDisplayArea) {
            audioDisplayArea.style.display = 'block';
            const audioPlayer = document.getElementById('stego-audio-player');
            const downloadBtn = document.getElementById('audio-download-btn');

            if (audioPlayer) {
                audioPlayer.src = result.download_url;
                audioPlayer.load();
            }

            if (downloadBtn) {
                downloadBtn.href = result.download_url;
                downloadBtn.download = result.download_url.split('/').pop();
            }

            // Update Audio Specific Share Buttons
            const audioShareBtn = document.getElementById('audio-share-btn');
            if (audioShareBtn) {
                audioShareBtn.dataset.url = result.download_url ? (window.location.origin + result.download_url) : '';
                audioShareBtn.dataset.text = 'Secure Audio via SILENT';
            }

            const audioNativeBtn = document.getElementById('audio-native-share-btn');
            if (audioNativeBtn) {
                if (navigator.share) {
                    audioNativeBtn.style.display = 'inline-flex';
                    audioNativeBtn.dataset.url = result.download_url;
                    audioNativeBtn.dataset.filename = result.download_url.split('/').pop();
                } else {
                    audioNativeBtn.style.display = 'none';
                }
            }

            audioDisplayArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    else if (mediaType === 'video' && result.download_url) {
        if (videoDisplayArea) {
            videoDisplayArea.style.display = 'block';
            const videoPlayer = document.getElementById('stego-video-player');
            const downloadBtn = document.getElementById('video-download-btn');

            if (videoPlayer) {
                videoPlayer.src = result.download_url;
                videoPlayer.load();
            }

            if (downloadBtn) {
                downloadBtn.href = result.download_url;
                downloadBtn.download = result.download_url.split('/').pop();
            }

            // Update Video Specific Share Buttons
            const videoShareBtn = document.getElementById('video-share-btn');
            if (videoShareBtn) {
                videoShareBtn.dataset.url = result.download_url ? (window.location.origin + result.download_url) : '';
                videoShareBtn.dataset.text = 'Secure Video via SILENT';
            }

            const videoNativeBtn = document.getElementById('video-native-share-btn');
            if (videoNativeBtn) {
                if (navigator.share) {
                    videoNativeBtn.style.display = 'inline-flex';
                    videoNativeBtn.dataset.url = result.download_url;
                    videoNativeBtn.dataset.filename = result.download_url.split('/').pop();
                } else {
                    videoNativeBtn.style.display = 'none';
                }
            }

            videoDisplayArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    else {
        // Show text output for non-image types
        if (stegoOutputArea) {
            stegoOutputArea.style.display = 'block';
            const outputContent = document.getElementById('stego-text-output');
            if (outputContent) {
                outputContent.textContent = result.data || result.message;
            }
            stegoOutputArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        hideImageComparison();
    }

    // Update share button visibility and data
    const shareBtn = document.getElementById('hide-share-btn');
    if (shareBtn) {
        shareBtn.style.display = 'block';
        // Store output data for sharing
        shareBtn.dataset.url = result.download_url ? (window.location.origin + result.download_url) : '';
        shareBtn.dataset.text = result.data || '';
    }

    const nativeBtn = document.getElementById('text-native-share-btn');
    if (nativeBtn) {
        if (navigator.share) {
            nativeBtn.style.display = 'inline-flex';
            nativeBtn.dataset.text = result.data || '';
            nativeBtn.dataset.url = result.download_url ? (window.location.origin + result.download_url) : '';
        } else {
            nativeBtn.style.display = 'none';
        }
    }
}

function displayExtractOutput(result) {
    // Hide all possible output areas first to avoid double-displays
    const resArea = document.getElementById('result-area');
    const stegoOutputArea = document.getElementById('stego-output-area');
    const audioDisplayArea = document.getElementById('audio-output-display');
    const videoDisplayArea = document.getElementById('video-output-display');

    if (stegoOutputArea) stegoOutputArea.style.display = 'none';
    if (audioDisplayArea) audioDisplayArea.style.display = 'none';
    if (videoDisplayArea) videoDisplayArea.style.display = 'none';
    hideImageComparison();

    // Check if result contains text data - prioritize text over image display
    if (result.data && typeof result.data === 'string') {
        // This is text data - show in text area
        if (resArea) {
            resArea.style.display = 'block';
            const textResult = document.getElementById('text-result');
            if (textResult) {
                textResult.textContent = result.data;
            }

            // Hide download button for text
            let downloadBtn = document.getElementById('download-btn');
            if (downloadBtn) downloadBtn.style.display = 'none';

            // Update share button for text
            const shareBtn = document.getElementById('extract-share-btn');
            if (shareBtn) {
                shareBtn.style.display = 'block';
                shareBtn.dataset.url = '';
                shareBtn.dataset.text = result.data;
            }

            const nativeBtn = document.getElementById('extract-native-share-btn');
            if (nativeBtn) {
                nativeBtn.style.display = navigator.share ? 'inline-flex' : 'none';
                nativeBtn.dataset.url = '';
                nativeBtn.dataset.text = result.data;
            }

            resArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        return;
    }

    // Check if result is a file with image extension - show in image panel
    const isImageFile = result.download_url && result.is_file && (
        result.download_url.match(/\.(png|jpg|jpeg|gif|bmp|webp|tiff|svg)$/i) ||
        (result.filename && result.filename.match(/\.(png|jpg|jpeg|gif|bmp|webp|tiff|svg)$/i))
    );

    // Handle image file extraction - show in image panel
    if (isImageFile && result.download_url) {
        // Hide text result area
        if (resArea) resArea.style.display = 'none';

        // Build the hidden image URL
        let hiddenImageUrl = result.download_url;
        if (hiddenImageUrl && !hiddenImageUrl.startsWith('http') && !hiddenImageUrl.startsWith('data:')) {
            if (hiddenImageUrl.startsWith('/')) {
                hiddenImageUrl = window.location.origin + hiddenImageUrl;
            } else {
                hiddenImageUrl = window.location.origin + '/' + hiddenImageUrl;
            }
        }

        // Show image comparison with extracted image (no cover image for extraction)
        showImageComparison(null, hiddenImageUrl, result);
        return;
    }

    // Check if it's audio or video for extraction playback
    const isAudioFile = result.download_url && result.is_file && result.download_url.match(/\.(wav|mp3|ogg|flac|m4a|mpeg)$/i);
    const isVideoFile = result.download_url && result.is_file && result.download_url.match(/\.(avi|mp4|mkv|mov|webm)$/i);

    if (isAudioFile && audioDisplayArea) {
        audioDisplayArea.style.display = 'block';
        const player = document.getElementById('stego-audio-player');
        if (player) { player.src = result.download_url; player.load(); }
        const dl = document.getElementById('audio-download-btn');
        if (dl) { dl.href = result.download_url; dl.style.display = 'inline-flex'; }
        audioDisplayArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // Also show result area msg
        if (resArea) {
            resArea.style.display = 'block';
            const textResult = document.getElementById('text-result');
            if (textResult) textResult.textContent = 'Audio extracted and ready for playback.';
            const dlb = document.getElementById('download-btn');
            if (dlb) dlb.style.display = 'none';
        }
        return;
    }

    if (isVideoFile && videoDisplayArea) {
        videoDisplayArea.style.display = 'block';
        const player = document.getElementById('stego-video-player');
        if (player) { player.src = result.download_url; player.load(); }
        const dl = document.getElementById('video-download-btn');
        if (dl) { dl.href = result.download_url; dl.style.display = 'inline-flex'; }
        videoDisplayArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
        if (resArea) {
            resArea.style.display = 'block';
            const textResult = document.getElementById('text-result');
            if (textResult) textResult.textContent = 'Video extracted and ready for playback.';
            const dlb = document.getElementById('download-btn');
            if (dlb) dlb.style.display = 'none';
        }
        return;
    }

    // For other file types (audio, video, or unknown) - show download button
    if (resArea) {
        resArea.style.display = 'block';
        const textResult = document.getElementById('text-result');
        if (textResult) {
            textResult.textContent = result.data || 'Data extracted successfully';
        }

        // Show download link if it's a file result
        let downloadBtn = document.getElementById('download-btn');
        if (result.is_file && result.download_url) {
            if (downloadBtn) {
                downloadBtn.href = result.download_url;
                downloadBtn.style.display = 'block';
            }
        } else if (downloadBtn) {
            downloadBtn.style.display = 'none';
        }

        // Update share button
        const shareBtn = document.getElementById('extract-share-btn');
        if (shareBtn) {
            shareBtn.style.display = 'block';
            shareBtn.dataset.url = result.download_url ? (window.location.origin + result.download_url) : '';
            shareBtn.dataset.text = result.data || '';
        }

        const nativeBtn = document.getElementById('extract-native-share-btn');
        if (nativeBtn) {
            if (navigator.share) {
                nativeBtn.style.display = 'inline-flex';
                nativeBtn.dataset.url = result.download_url ? (window.location.origin + result.download_url) : '';
                nativeBtn.dataset.text = result.data || '';
                nativeBtn.dataset.isFile = result.is_file || false;
                nativeBtn.dataset.filename = result.download_url ? result.download_url.split('/').pop() : 'extracted_data';
            } else {
                nativeBtn.style.display = 'none';
            }
        }

        resArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function formatFileSize(bytes) {
    if (!bytes) return 'N/A';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

function copyToClipboard() {
    const content = document.getElementById('stego-text-output')?.textContent ||
        document.getElementById('text-result')?.textContent;
    if (content) {
        navigator.clipboard.writeText(content).then(() => {
            showToast('Copied to clipboard!');
        }).catch(() => {
            showToast('Failed to copy', true);
        });
    }
}

async function submitMultiLayer(op) {
    toggleLoading(true);
    const formId = op === 'hide' ? 'multilayer-hide-form' : 'multilayer-extract-form';
    const form = document.getElementById(formId);
    const formData = new FormData(form);
    formData.append('operation', op);

    const dataType = op === 'hide' ? (state.mlDataType || 'text') : (state.mlExtractDataType || 'text');
    formData.append('data_type', dataType);

    try {
        const response = await fetch('/multilayer', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            showToast(result.message);

            // Display output in interface
            if (op === 'hide') {
                displayHideOutput(result, 'Multi-Layer');
                displayMultiLayerHideResults(result);
            } else if (op === 'extract') {
                displayExtractOutput(result);
                displayMultiLayerResults(result);
            }

            // Download file if URL provided
            if (result.download_url) {
                setTimeout(() => {
                    const link = document.createElement('a');
                    link.href = result.download_url;
                    link.download = result.filename || `multilayer_output_${Date.now()}`;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }, 500);
            }

            // Refresh history if we're on the history page or just generally
            if (state.mediaType === 'history') fetchHistory();
        } else {
            showToast(result.message || result.error, true);
        }
    } catch (error) {
        showToast('Processing failed', true);
        console.error(error);
    } finally {
        toggleLoading(false);
    }
}

function displayMultiLayerHideResults(result) {
    const panel = document.getElementById('ml-hide-results');
    if (!panel) return;

    panel.style.display = 'block';

    // Smooth scroll to results
    setTimeout(() => {
        panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);

    // 1. Secret Content (Layer 0)
    const res1 = document.getElementById('ml-hide-res-1');
    if (res1) {
        if (state.mlDataType === 'text') {
            const text = document.getElementById('ml-secret-text').value;
            res1.innerHTML = `<div style="font-size:0.75rem; color:var(--text); padding:8px; text-align:left; line-height:1.2; width:100%; height:100%; overflow:hidden; word-break:break-all;">${text.substring(0, 150)}${text.length > 150 ? '...' : ''}</div>`;
        } else {
            res1.innerHTML = `<i class="fa-solid fa-file-shield" style="font-size:2.5rem; color:var(--primary);"></i>`;
        }
    }

    // 2. Layer 1 Media (Input Carrier)
    const res2 = document.getElementById('ml-hide-res-2');
    if (res2) {
        const l1Type = document.getElementById('ml-layer1-type').value;
        const l1Preview = document.getElementById('ml-l1-preview');

        if (l1Type === 'image' && l1Preview && l1Preview.src) {
            res2.innerHTML = `<img src="${l1Preview.src}" style="max-height:100%; max-width:100%; object-fit:contain; border-radius:8px;">`;
        } else if (l1Type === 'audio') {
            res2.innerHTML = `<i class="fa-solid fa-music" style="font-size:2.5rem; color:var(--primary-light);"></i>`;
        } else if (l1Type === 'video') {
            res2.innerHTML = `<i class="fa-solid fa-film" style="font-size:2.5rem; color:var(--primary-light);"></i>`;
        } else {
            res2.innerHTML = `<i class="fa-solid fa-quote-left" style="font-size:2.5rem; color:var(--primary-light);"></i>`;
        }
    }

    // 3. Final Output (Layer 2)
    const res3 = document.getElementById('ml-hide-res-3');
    if (res3 && result.download_url) {
        const l2Type = document.getElementById('ml-layer2-type').value;
        if (l2Type === 'image') {
            res3.innerHTML = `<img src="${result.download_url}" style="max-height:100%; max-width:100%; object-fit:contain; border-radius:8px;">`;
        } else if (l2Type === 'audio') {
            res3.innerHTML = `<i class="fa-solid fa-file-audio" style="font-size:2.5rem; color:var(--success);"></i>`;
        } else if (l2Type === 'video') {
            res3.innerHTML = `<i class="fa-solid fa-file-video" style="font-size:2.5rem; color:var(--success);"></i>`;
        } else {
            res3.innerHTML = `<i class="fa-solid fa-file-lines" style="font-size:2.5rem; color:var(--success);"></i>`;
        }
    }

    // Update actions
    const dlBtn = document.getElementById('ml-hide-download-btn');
    if (dlBtn && result.download_url) {
        dlBtn.href = result.download_url;
        dlBtn.style.display = 'inline-flex';
        dlBtn.download = result.filename || 'multilayer_stego';
    }

    const shareBtn = document.getElementById('ml-hide-share-btn');
    if (shareBtn) {
        shareBtn.dataset.url = result.download_url ? (window.location.origin + result.download_url) : '';
        shareBtn.dataset.text = 'Secure Multi-Layer Data via SILENT';
    }

    const nativeBtn = document.getElementById('ml-hide-native-share-btn');
    if (nativeBtn) {
        if (navigator.share) {
            nativeBtn.style.display = 'inline-flex';
            nativeBtn.dataset.url = result.download_url ? (window.location.origin + result.download_url) : '';
            nativeBtn.dataset.filename = result.filename || 'multilayer_output.png';
            nativeBtn.dataset.isFile = 'true';
        } else {
            nativeBtn.style.display = 'none';
        }
    }
}

async function shareMultiLayerHideNative() {
    return shareMultiLayerNative('ml-hide');
}
function displayMultiLayerResults(result) {
    const panel = document.getElementById('ml-results-panel');
    if (!panel) return;

    panel.style.display = 'block';

    // Helper to create preview content
    const createPreview = (url, isText = false, textContent = '') => {
        if (!url && !textContent) return '<span style="color:var(--text-muted)">N/A</span>';
        if (isText) return `<div style="font-size:0.7rem; overflow:hidden; padding:5px;">${textContent.substring(0, 50)}...</div>`;

        const ext = url.split('.').pop().toLowerCase();
        if (['png', 'jpg', 'jpeg', 'bmp', 'gif'].includes(ext)) {
            return `<img src="${url}" style="max-height:100%; max-width:100%; object-fit:contain;">`;
        } else if (['wav', 'mp3'].includes(ext)) {
            return `<i class="fa-solid fa-file-audio" style="font-size:2rem; color:var(--primary);"></i>`;
        } else if (['avi', 'mp4'].includes(ext)) {
            return `<i class="fa-solid fa-file-video" style="font-size:2rem; color:var(--primary);"></i>`;
        }
        return `<i class="fa-solid fa-file" style="font-size:2rem;"></i>`;
    };

    // 1. Cover
    const coverBox = document.getElementById('ml-res-cover-box');
    if (coverBox) coverBox.innerHTML = createPreview(result.cover_url);

    // 2. Inner Layer (Intermediate)
    const innerBox = document.getElementById('ml-res-inner-box');
    if (innerBox) {
        if (result.intermediates && result.intermediates.length > 0) {
            innerBox.innerHTML = createPreview(result.intermediates[0]);
        } else {
            innerBox.innerHTML = '<span style="font-size:0.8rem; color:var(--text-muted)">Direct</span>';
        }
    }

    // 3. Secret
    const secretBox = document.getElementById('ml-res-secret-box');
    const finalText = document.getElementById('ml-final-text');
    const dlBtn = document.getElementById('ml-download-btn');
    const shareBtn = document.getElementById('ml-share-btn');
    const nativeBtn = document.getElementById('ml-native-share-btn');

    let shareUrl = '';
    let shareText = '';
    let shareFilename = '';
    let isFile = false;

    if (result.is_file) {
        if (secretBox) secretBox.innerHTML = createPreview(result.download_url);
        if (finalText) finalText.style.display = 'none';
        if (dlBtn) { dlBtn.href = result.download_url; dlBtn.style.display = 'inline-flex'; }

        shareUrl = result.download_url ? (window.location.origin + result.download_url) : '';
        if (result.download_url) shareFilename = result.download_url.split('/').pop();
        shareText = 'Secure File via SILENT Multi-Layer';
        isFile = true;
    } else {
        if (secretBox) secretBox.innerHTML = '<i class="fa-solid fa-font" style="font-size:2rem; color:var(--success);"></i>';
        if (finalText) { finalText.textContent = result.raw_data || result.data; finalText.style.display = 'block'; }
        if (dlBtn) dlBtn.style.display = 'none';

        shareText = result.raw_data || result.data;
        isFile = false;
    }

    if (shareBtn) {
        shareBtn.style.display = 'inline-flex';
        shareBtn.dataset.url = shareUrl;
        shareBtn.dataset.text = shareText;
    }

    if (nativeBtn) {
        if (navigator.share) {
            nativeBtn.style.display = 'inline-flex';
            nativeBtn.dataset.url = shareUrl;
            nativeBtn.dataset.text = shareText;
            nativeBtn.dataset.filename = shareFilename || 'secret_data';
            nativeBtn.dataset.isFile = isFile;
        } else {
            nativeBtn.style.display = 'none';
        }
    }
}

async function shareMultiLayerNative(prefix = 'ml') {
    const btn = document.getElementById(`${prefix}-native-share-btn`);
    if (!btn) return;

    const isFile = btn.dataset.isFile === 'true';
    const url = btn.dataset.url;
    const text = btn.dataset.text;
    const filename = btn.dataset.filename || 'secure_data';

    try {
        if (isFile && url) {
            toggleLoading(true);
            const response = await fetch(url);
            const blob = await response.blob();
            const file = new File([blob], filename, { type: blob.type });

            if (navigator.canShare && navigator.canShare({ files: [file] })) {
                await navigator.share({
                    files: [file],
                    title: 'Secure Multi-Layer Sequence',
                    text: text || 'Secure Data via SILENT'
                });
            } else {
                // Fallback to URL sharing if file sharing not supported
                await navigator.share({
                    title: 'Secure Multi-Layer Sequence',
                    text: text || 'Secure Data via SILENT',
                    url: url
                });
            }
        } else {
            await navigator.share({
                title: 'Secure Multi-Layer Sequence',
                text: text || 'Secure Data via SILENT',
                url: (url && url !== window.location.href) ? url : undefined
            });
        }
    } catch (e) {
        console.error(e);
        if (e.name !== 'AbortError') {
            showToast('Share failed: ' + e.message, true);
        }
    } finally {
        toggleLoading(false);
    }
}

async function submitForm(type) {
    toggleLoading(true);
    const formData = new FormData(type === 'hide' ? document.getElementById('hide-form') : document.getElementById('extract-form'));

    formData.append('operation', state.operation);
    formData.append('media_type', state.mediaType);
    formData.append('data_type', state.dataType);

    try {
        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            // Capture original data for history
            let originalData = null;
            if (state.operation === 'hide') {
                if (state.dataType === 'text') {
                    originalData = document.getElementById('cover-text').value;
                }
            } else {
                if (state.dataType === 'text') {
                    originalData = document.getElementById('stego-text-input').value;
                }
            }


            showToast(result.message);

            // Display output in interface
            if (state.operation === 'hide') {
                displayHideOutput(result, state.mediaType);
            } else if (state.operation === 'extract') {
                displayExtractOutput(result);
            }

            // Download automatically if URL provided
            if (result.download_url) {
                setTimeout(() => {
                    const link = document.createElement('a');
                    link.href = result.download_url;
                    link.download = result.filename || `output_${Date.now()}`;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }, 500);
            }

            // Refresh history
            if (state.mediaType === 'history') fetchHistory();
        } else {

            showToast(result.message || result.error, true);
        }
    } catch (error) {
        console.error(error);
        if (error.message.includes('Failed to fetch')) {
            showToast('Connection Error: Server is unreachable. Please restart the app.', true);
        } else {
            showToast('An error occurred. Please check console.', true);
        }
    } finally {
        toggleLoading(false);
    }
}

// --- History Logic ---

async function fetchHistory() {
    try {
        const response = await fetch('/api/history');
        const history = await response.json();
        renderHistory(history);
    } catch (error) {
        console.error('Failed to fetch history:', error);
    }
}

function renderHistory(history) {
    const tableBody = document.getElementById('history-table-body');
    const emptyState = document.getElementById('history-empty');

    if (!tableBody) return;

    tableBody.innerHTML = '';

    if (!history || history.length === 0) {
        if (emptyState) emptyState.style.display = 'block';
        return;
    }

    if (emptyState) emptyState.style.display = 'none';

    history.forEach(item => {
        const row = document.createElement('tr');
        row.style.background = 'rgba(255, 255, 255, 0.03)';
        row.style.borderRadius = '8px';

        row.innerHTML = `
            <td style="padding: 1rem; color: var(--text-muted); font-family: 'Space Mono', monospace; font-size: 0.85rem;">${item.timestamp}</td>
            <td style="padding: 1rem; font-weight: 600;">
                <span style="padding: 0.25rem 0.6rem; border-radius: 4px; background: ${item.operation === 'Hide' ? 'rgba(245, 196, 0, 0.1)' : 'rgba(16, 185, 129, 0.1)'}; color: ${item.operation === 'Hide' ? 'var(--primary)' : 'var(--success)'};">
                    ${item.operation}
                </span>
            </td>
            <td style="padding: 1rem;">${item.media_type}</td>
            <td style="padding: 1rem;">
                <span style="display: flex; align-items: center; gap: 0.5rem; color: ${item.status === 'Success' ? 'var(--success)' : 'var(--error)'};">
                    <div style="width: 6px; height: 6px; border-radius: 50%; background: currentColor;"></div>
                    ${item.status}
                </span>
            </td>
            <td style="padding: 1rem; color: var(--text-muted); font-size: 0.9rem;">${item.result}</td>
        `;
        tableBody.appendChild(row);
    });
}

async function clearHistory() {
    if (!confirm('Are you sure you want to clear all operation history?')) return;

    try {
        const response = await fetch('/api/clear_history', { method: 'POST' });
        const result = await response.json();
        if (result.success) {
            showToast('History cleared');
            renderHistory([]);
        }
    } catch (error) {
        showToast('Failed to clear history', true);
    }
}





// ============================================
// CONSOLIDATED INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initDragAndDrop();

    // Set initial state
    setMediaType('text');

    // Initialize layer UI
    try {
        updateLayerUploadUI('layer1');
        updateLayerUploadUI('layer2');
        setMLDataType('text');
        setMLExtractDataType('text');
        initLayerPreviews();

        const select1 = document.getElementById('ml-layer1-type');
        const select2 = document.getElementById('ml-layer2-type');
        if (select1) select1.addEventListener('change', () => updateLayerUploadUI('layer1'));
        if (select2) select2.addEventListener('change', () => updateLayerUploadUI('layer2'));
    } catch (e) {
        console.log('Layer initialization:', e.message);
    }

    // Listeners
    const hideForm = document.getElementById('hide-form');
    if (hideForm) hideForm.addEventListener('submit', (e) => { e.preventDefault(); submitForm('hide'); });

    const extractForm = document.getElementById('extract-form');
    if (extractForm) extractForm.addEventListener('submit', (e) => { e.preventDefault(); submitForm('extract'); });

    const mlHideForm = document.getElementById('multilayer-hide-form');
    if (mlHideForm) mlHideForm.addEventListener('submit', (e) => { e.preventDefault(); submitMultiLayer('hide'); });

    const mlExtractForm = document.getElementById('multilayer-extract-form');
    if (mlExtractForm) mlExtractForm.addEventListener('submit', (e) => { e.preventDefault(); submitMultiLayer('extract'); });

    // File input previews
    const sourceFileInput = document.getElementById('source-file');
    if (sourceFileInput) {
        sourceFileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0] && e.target.files[0].type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function (event) {
                    const coverImagePreview = document.getElementById('cover-image-preview');
                    if (coverImagePreview) {
                        coverImagePreview.src = event.target.result;
                        coverImagePreview.style.display = 'block';
                    }
                };
                reader.readAsDataURL(e.target.files[0]);
            }
        });
    }

});


// Image Comparison Functions
function showImageComparison(coverUrl, hiddenUrl, result = null) {
    const container = document.getElementById('image-comparison-display');
    if (container) container.style.display = 'block';

    const coverPanel = document.querySelector('#image-comparison-display .comparison-panels .image-panel:first-child');
    const coverImg = document.getElementById('cover-image-preview');
    const hiddenImageTitle = document.getElementById('hidden-image-title');

    if (coverUrl && coverImg && coverPanel) {
        coverImg.src = coverUrl;
        coverImg.style.display = 'block';
        coverPanel.style.display = 'block';
        // Show "Cover Image" title for hide operation
        if (coverPanel.querySelector('h3')) {
            coverPanel.querySelector('h3').textContent = 'Cover Image';
        }
    } else if (coverPanel) {
        // Hide cover panel for extraction operations
        coverPanel.style.display = 'none';
    }

    // Update title based on operation
    if (hiddenImageTitle) {
        if (state.operation === 'extract') {
            hiddenImageTitle.textContent = 'Extracted Image';
        } else {
            hiddenImageTitle.textContent = 'Hidden Image Output';
        }
    }

    const hiddenImg = document.getElementById('hidden-image-preview');
    if (hiddenImg && hiddenUrl) {
        hiddenImg.src = hiddenUrl;
        hiddenImg.style.display = 'block';
    }

    // Show actions (Download/Share)
    const actionsDiv = document.getElementById('image-output-actions');
    if (actionsDiv && result) {
        actionsDiv.style.display = 'flex';
        const downloadBtn = document.getElementById('image-download-btn-direct');
        if (downloadBtn) {
            downloadBtn.href = hiddenUrl;
            downloadBtn.download = result.filename || 'stego_image.png';
        }
        const shareBtn = document.getElementById('image-share-btn');
        if (shareBtn) {
            shareBtn.dataset.url = hiddenUrl;
            shareBtn.dataset.text = result.data || 'Secure Image via SILENT';
        }

        const nativeBtn = document.getElementById('image-native-share-btn');
        if (nativeBtn) {
            if (navigator.share) {
                nativeBtn.style.display = 'inline-flex';
                nativeBtn.dataset.url = hiddenUrl;
                nativeBtn.dataset.filename = result.filename || 'stego_image.png';
            } else {
                nativeBtn.style.display = 'none';
            }
        }
    }
}

function hideImageComparison() {
    const container = document.getElementById('image-comparison-display');
    if (container) container.style.display = 'none';
    const actionsDiv = document.getElementById('image-output-actions');
    if (actionsDiv) actionsDiv.style.display = 'none';
}


// --- Sharing Logic ---

async function shareImageNative() {
    const btn = document.getElementById('image-native-share-btn');
    if (!btn || !btn.dataset.url) return;

    try {
        toggleLoading(true);
        const response = await fetch(btn.dataset.url);
        const blob = await response.blob();
        const file = new File([blob], btn.dataset.filename || 'image.png', { type: blob.type });

        if (navigator.canShare && navigator.canShare({ files: [file] })) {
            await navigator.share({
                files: [file],
                title: 'Secure Image',
                text: 'Secure Image via SILENT'
            });
        } else {
            showToast('Direct sharing not supported', true);
        }
    } catch (e) {
        console.error(e);
        showToast('Share failed: ' + e.message, true);
    } finally {
        toggleLoading(false);
    }
}

async function shareTextNative() {
    const btn = document.getElementById('text-native-share-btn');
    if (!btn) return;

    const text = btn.dataset.text;
    const url = btn.dataset.url;

    try {
        const shareData = {
            title: 'Secure Data',
            text: text || 'Secure Data via SILENT'
        };
        if (url && url.startsWith('http')) shareData.url = url;

        if (navigator.share) {
            await navigator.share(shareData);
        } else {
            showToast('Direct sharing not supported', true);
        }
    } catch (e) {
        console.error(e);
    }
}

async function shareAudioNative() {
    const btn = document.getElementById('audio-native-share-btn');
    if (!btn || !btn.dataset.url) return;

    try {
        toggleLoading(true);
        const response = await fetch(btn.dataset.url);
        const blob = await response.blob();
        const file = new File([blob], btn.dataset.filename || 'audio.wav', { type: blob.type });

        if (navigator.canShare && navigator.canShare({ files: [file] })) {
            await navigator.share({
                files: [file],
                title: 'Secure Audio',
                text: 'Secure Audio via SILENT'
            });
        } else {
            // Fallback to basic share
            await navigator.share({
                title: 'Secure Audio',
                url: window.location.origin + btn.dataset.url
            });
        }
    } catch (e) {
        console.error(e);
        showToast('Share failed: ' + e.message, true);
    } finally {
        toggleLoading(false);
    }
}

async function shareVideoNative() {
    const btn = document.getElementById('video-native-share-btn');
    if (!btn || !btn.dataset.url) return;

    try {
        toggleLoading(true);
        const response = await fetch(btn.dataset.url);
        const blob = await response.blob();
        const file = new File([blob], btn.dataset.filename || 'video.mp4', { type: blob.type });

        if (navigator.canShare && navigator.canShare({ files: [file] })) {
            await navigator.share({
                files: [file],
                title: 'Secure Video',
                text: 'Secure Video via SILENT'
            });
        } else {
            // Fallback to basic share
            await navigator.share({
                title: 'Secure Video',
                url: window.location.origin + btn.dataset.url
            });
        }
    } catch (e) {
        console.error(e);
        showToast('Share failed: ' + e.message, true);
    } finally {
        toggleLoading(false);
    }
}

async function shareExtractionNative() {
    const btn = document.getElementById('extract-native-share-btn');
    if (!btn) return;

    const isFile = btn.dataset.isFile === 'true';
    const text = btn.dataset.text;
    const url = btn.dataset.url;

    try {
        if (isFile && url) {
            toggleLoading(true);
            const response = await fetch(url);
            const blob = await response.blob();
            const file = new File([blob], btn.dataset.filename || 'extracted_file', { type: blob.type });

            if (navigator.canShare && navigator.canShare({ files: [file] })) {
                await navigator.share({
                    files: [file],
                    title: 'Extracted File',
                    text: 'Extracted via SILENT'
                });
            } else {
                await navigator.share({
                    title: 'Extracted File',
                    url: window.location.origin + url
                });
            }
        } else {
            await navigator.share({
                title: 'Extracted Message',
                text: text || 'Message extracted via SILENT'
            });
        }
    } catch (e) {
        console.error(e);
        showToast('Share failed', true);
    } finally {
        if (isFile) toggleLoading(false);
    }
}

function openShareModal(type) {
    const modal = document.getElementById('share-modal');
    const button = document.getElementById(`${type}-share-btn`);
    const urlInput = document.getElementById('share-url-input');

    if (!modal || !button) return;

    let url = button.dataset.url || window.location.href;
    let text = button.dataset.text || 'Check out this secure data from SILENT!';

    // Handle image type specifically - convert blob URLs and relative paths to absolute URLs
    if (type === 'image') {
        // If it's a blob URL, we need to handle it differently
        if (url && url.startsWith('blob:')) {
            // For blob URLs, we'll use the download attribute approach
            // Convert blob URL to a shareable format if possible
            text = 'Secure Image via SILENT - Steganography Output';
        } else if (url && !url.startsWith('http') && !url.startsWith('data:')) {
            // Handle relative URLs - make them absolute
            if (url.startsWith('/')) {
                url = window.location.origin + url;
            } else {
                url = window.location.origin + '/' + url;
            }
        }
    }

    if (urlInput) urlInput.value = url;

    // Update social links
    const encodedUrl = encodeURIComponent(url);
    const encodedText = encodeURIComponent(text);

    document.getElementById('share-whatsapp').href = `https://api.whatsapp.com/send?text=${encodedText}%20${encodedUrl}`;
    document.getElementById('share-telegram').href = `https://t.me/share/url?url=${encodedUrl}&text=${encodedText}`;
    document.getElementById('share-twitter').href = `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodedText}`;
    document.getElementById('share-email').href = `mailto:?subject=Secure Data via SILENT&body=${encodedText}%0A%0A${encodedUrl}`;

    // Reset QR View
    document.getElementById('qr-display').style.display = 'none';

    modal.style.display = 'flex';
}

function closeShareModal() {
    const modal = document.getElementById('share-modal');
    if (modal) modal.style.display = 'none';
}

function copyShareLink() {
    const urlInput = document.getElementById('share-url-input');
    if (urlInput) {
        urlInput.select();
        urlInput.setSelectionRange(0, 99999); // For mobile devices
        navigator.clipboard.writeText(urlInput.value).then(() => {
            showToast('Link copied to clipboard!');
        }).catch(() => {
            showToast('Failed to copy link', true);
        });
    }
}
