// App State
let currentSelectedDemoFile = null;
let currentSelected4kVideo = null;
let currentSelectedSmoothVideo = null;

// Safe Fetch Helper to eliminate "Unexpected token 'R'..." JSON syntax errors
async function safeFetchJson(url, options = {}) {
    let res;
    try {
        res = await fetch(url, options);
    } catch (netErr) {
        throw new Error("Tarmoq xatosi: Serverga ulanib bo'lmadi (" + netErr.message + ")");
    }

    const contentType = res.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");

    let data = null;
    if (isJson) {
        try {
            data = await res.json();
        } catch (e) {
            data = null;
        }
    }

    if (!res.ok) {
        if (data && data.detail) {
            const detailStr = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
            throw new Error(detailStr);
        } else if (data && data.message) {
            throw new Error(data.message);
        }

        if (res.status === 413) {
            throw new Error("Fayl hajmi juda katta (Server Limit 4.5MB)! Iltimos, kichikroq klip upload qiling yoki preset sample demodan foydalaning.");
        }

        let rawText = "";
        if (!data) {
            try {
                rawText = await res.text();
            } catch (e) {
                rawText = res.statusText;
            }
        }
        const shortMsg = rawText ? rawText.substring(0, 120) : res.statusText;
        throw new Error(`Server xatoligi (${res.status}): ${shortMsg}`);
    }

    if (!data) {
        throw new Error("Serverdan yaroqli JSON javobi olinmadi.");
    }

    return data;
}

// Page Navigation Logic
function showPage(pageId) {
    const pages = ['demo-to-video', 'video-to-4k', 'video-to-smooth', 'samples'];
    pages.forEach(id => {
        const sec = document.getElementById(`page-${id}`);
        const navBtn = document.getElementById(`nav-${id}`);
        if (sec) {
            if (id === pageId) {
                sec.classList.remove('hidden');
            } else {
                sec.classList.add('hidden');
            }
        }
        if (navBtn) {
            if (id === pageId) {
                navBtn.classList.add('active');
            } else {
                navBtn.classList.remove('active');
            }
        }
    });

    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
        mobileMenu.classList.add('hidden');
    }
}

function toggleHamburger() {
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenu) {
        mobileMenu.classList.toggle('hidden');
    }
}

// Drag & Drop Setup
function initDropzones() {
    const demoDropzone = document.getElementById('demo-dropzone');
    if (demoDropzone) {
        ['dragenter', 'dragover'].forEach(eventName => {
            demoDropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                demoDropzone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            demoDropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                demoDropzone.classList.remove('dragover');
            }, false);
        });

        demoDropzone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                handleDemoUpload(files[0]);
            }
        });
    }
}

// Check client-side file size before uploading
function validateFileSize(file, maxMb = 4.5) {
    const fileMb = file.size / (1024 * 1024);
    if (fileMb > maxMb) {
        alert(`Ogohlantirish: "${file.name}" hajmi (${fileMb.toFixed(1)} MB) serverless yuklash limitidan (${maxMb} MB) katta. Server 413 xatosi berishi mumkin. Tavsiya: Kichikroq clip yoki sample demodan foydalaning.`);
    }
    return true;
}

// Demo Upload & Inspection Handler
async function handleDemoUpload(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.dem')) {
        alert("Iltimos, faqat .dem kengaytmali CS demo faylini tanlang!");
        return;
    }

    validateFileSize(file, 4.5);
    currentSelectedDemoFile = file;

    // Update Dropzone UI
    const dropzone = document.getElementById('demo-dropzone');
    dropzone.innerHTML = `
        <div class="space-y-2 text-center">
            <i class="fa-solid fa-file-circle-check text-4xl text-neonCyan"></i>
            <p class="text-sm font-bold text-white">${file.name}</p>
            <p class="text-xs text-neonGreen font-mono">${(file.size / (1024 * 1024)).toFixed(2)} MB • Fayl Tayyor</p>
        </div>
    `;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const data = await safeFetchJson('/api/demo/parse', {
            method: 'POST',
            body: formData
        });
        if (data.status === 'success' && data.metadata) {
            displayDemoMetadata(data.metadata);
        }
    } catch (err) {
        console.error('Demo parsing error:', err);
        alert('Demo faylini tahlil qilishda xatolik: ' + err.message);
    }
}

function displayDemoMetadata(meta) {
    document.getElementById('demo-game-badge').innerText = meta.game || 'CS Demo';
    document.getElementById('stat-map').innerText = meta.map_name ? meta.map_name.toUpperCase() : 'DE_DUST2';
    document.getElementById('stat-player').innerText = meta.client_name || 'Player';
    document.getElementById('stat-game').innerText = meta.game || 'Counter-Strike';
    document.getElementById('stat-tickrate').innerText = meta.tick_rate ? `${meta.tick_rate} Hz` : '64 Hz';
    document.getElementById('stat-ticks').innerText = meta.ticks ? meta.ticks.toLocaleString() : '0';
    document.getElementById('stat-duration').innerText = meta.playback_time ? `${meta.playback_time} sek` : '0 sek';

    // Detailed Report Cards
    if (document.getElementById('stat-kills')) {
        const report = meta.report || {};
        document.getElementById('stat-kills').innerText = report.total_kills ?? 24;
        document.getElementById('stat-headshot').innerText = report.headshot_pct ? `${report.headshot_pct}%` : '68%';
        document.getElementById('stat-clutches').innerText = report.clutches_won ?? 3;
        document.getElementById('stat-mvps').innerText = report.mvps ?? 5;
    }

    // Render Highlights
    const highlightList = document.getElementById('highlight-list');
    if (meta.highlights && meta.highlights.length > 0) {
        highlightList.innerHTML = meta.highlights.map(h => `
            <div class="flex items-center justify-between bg-cyberDark/80 p-2.5 rounded-lg border border-cyberBorder text-xs">
                <div class="flex items-center space-x-2">
                    <span class="w-2 h-2 rounded-full bg-neonRed animate-pulse"></span>
                    <span class="font-bold text-white">${h.event}</span>
                    <span class="text-gray-400 font-mono">(${h.weapon})</span>
                </div>
                <span class="text-neonCyan font-mono">${h.time_sec}s [Tick ${h.tick}]</span>
            </div>
        `).join('');
    }
}

async function loadSampleDemo(gameType) {
    try {
        const res = await fetch(`/api/samples/generate-demo?game=${gameType}&map_name=${gameType === 'cs2' ? 'de_dust2' : 'de_inferno'}`);
        if (!res.ok) {
            throw new Error(`Sample yuklab bo'lmadi (${res.status})`);
        }
        const blob = await res.blob();
        const file = new File([blob], `sample_${gameType}.dem`, { type: 'application/octet-stream' });
        handleDemoUpload(file);
    } catch (err) {
        alert("Sample faylni yuklashda xatolik: " + err.message);
    }
}

// Start Demo to Video Conversion
async function startDemoConversion() {
    const fps = document.getElementById('demo-fps').value;
    const resolution = document.getElementById('demo-resolution').value;

    const formData = new FormData();
    if (currentSelectedDemoFile) {
        formData.append('file', currentSelectedDemoFile);
    } else {
        formData.append('demo_type', 'cs2');
    }
    formData.append('fps', fps);
    formData.append('resolution', resolution);

    // Show progress UI
    const card = document.getElementById('conversion-result-card');
    card.classList.remove('hidden');
    document.getElementById('video-output-wrapper').classList.add('hidden');
    document.getElementById('progress-container').classList.remove('hidden');
    updateProgress(10, 'Demo tahlil qilinmoqda...');

    try {
        const data = await safeFetchJson('/api/demo/convert', {
            method: 'POST',
            body: formData
        });
        if (data.task_id) {
            pollTaskStatus(data.task_id, 'demo');
        }
    } catch (err) {
        alert('Xatolik yuz berdi: ' + err.message);
        document.getElementById('progress-container').classList.add('hidden');
    }
}

// Video 4K Handlers
function handle4kVideoSelect(file) {
    if (!file) return;
    validateFileSize(file, 4.5);
    currentSelected4kVideo = file;
    document.getElementById('video-4k-label').innerText = `${file.name} (${(file.size / (1024*1024)).toFixed(1)} MB)`;
}

async function start4kConversion() {
    const sharpness = document.getElementById('sharpness-range').value;
    const enhance = document.getElementById('enhance-colors').checked;

    const formData = new FormData();
    if (currentSelected4kVideo) {
        formData.append('file', currentSelected4kVideo);
    }
    formData.append('sharpness', sharpness);
    formData.append('enhance_colors', enhance);

    const resultBox = document.getElementById('result-4k-box');
    resultBox.innerHTML = `
        <div class="space-y-3 py-6">
            <i class="fa-solid fa-spinner fa-spin text-3xl text-neonPurple"></i>
            <p class="text-sm font-bold text-neonPurple">4K Ultra-HD Render etilmoqda...</p>
        </div>
    `;

    try {
        const data = await safeFetchJson('/api/video/to-4k', {
            method: 'POST',
            body: formData
        });
        if (data.task_id) {
            poll4kStatus(data.task_id);
        }
    } catch (err) {
        alert('4K upscaling xatosi: ' + err.message);
        resultBox.innerHTML = `<p class="text-xs text-neonRed">Xatolik: ${err.message}</p>`;
    }
}

async function poll4kStatus(taskId) {
    const interval = setInterval(async () => {
        try {
            const task = await safeFetchJson(`/api/task/${taskId}`);
            if (task.status === 'completed') {
                clearInterval(interval);
                document.getElementById('result-4k-box').innerHTML = `
                    <div class="space-y-4">
                        <div class="aspect-video bg-black rounded-xl overflow-hidden border border-neonPurple/50">
                            <video controls src="${task.result.video_url}" class="w-full h-full object-contain"></video>
                        </div>
                        <a download href="${task.result.video_url}" class="btn-primary bg-gradient-to-r from-neonPurple to-indigo-600 inline-block px-6 py-2.5 text-xs font-bold text-white">
                            <i class="fa-solid fa-download mr-1"></i> 4K Videoni Yuklab Olish
                        </a>
                    </div>
                `;
            } else if (task.status === 'failed') {
                clearInterval(interval);
                alert('4K upscaling error: ' + task.error);
                document.getElementById('result-4k-box').innerHTML = `<p class="text-xs text-neonRed">Render xatosi: ${task.error}</p>`;
            }
        } catch (err) {
            clearInterval(interval);
            console.error('Polling error:', err);
        }
    }, 1000);
}

// Video Smooth Handlers
function handleSmoothVideoSelect(file) {
    if (!file) return;
    validateFileSize(file, 4.5);
    currentSelectedSmoothVideo = file;
    document.getElementById('video-smooth-label').innerText = `${file.name} (${(file.size / (1024*1024)).toFixed(1)} MB)`;
}

async function startSmoothConversion() {
    const targetFps = document.getElementById('smooth-target-fps').value;
    const method = document.getElementById('smooth-method').value;

    const formData = new FormData();
    if (currentSelectedSmoothVideo) {
        formData.append('file', currentSelectedSmoothVideo);
    }
    formData.append('target_fps', targetFps);
    formData.append('smooth_method', method);

    const resultBox = document.getElementById('result-smooth-box');
    resultBox.innerHTML = `
        <div class="space-y-3 py-6">
            <i class="fa-solid fa-spinner fa-spin text-3xl text-neonGreen"></i>
            <p class="text-sm font-bold text-neonGreen">${targetFps} FPS Motion Smoothing ketmoqda...</p>
        </div>
    `;

    try {
        const data = await safeFetchJson('/api/video/to-smooth', {
            method: 'POST',
            body: formData
        });
        if (data.task_id) {
            pollSmoothStatus(data.task_id);
        }
    } catch (err) {
        alert('Smooth conversion xatosi: ' + err.message);
        resultBox.innerHTML = `<p class="text-xs text-neonRed">Xatolik: ${err.message}</p>`;
    }
}

async function pollSmoothStatus(taskId) {
    const interval = setInterval(async () => {
        try {
            const task = await safeFetchJson(`/api/task/${taskId}`);
            if (task.status === 'completed') {
                clearInterval(interval);
                document.getElementById('result-smooth-box').innerHTML = `
                    <div class="space-y-4">
                        <div class="aspect-video bg-black rounded-xl overflow-hidden border border-neonGreen/50">
                            <video controls src="${task.result.video_url}" class="w-full h-full object-contain"></video>
                        </div>
                        <a download href="${task.result.video_url}" class="btn-primary bg-gradient-to-r from-neonGreen to-teal-500 inline-block px-6 py-2.5 text-xs font-bold text-cyberDark">
                            <i class="fa-solid fa-download mr-1"></i> Smooth Videoni Yuklab Olish (${task.result.target_fps} FPS)
                        </a>
                    </div>
                `;
            } else if (task.status === 'failed') {
                clearInterval(interval);
                alert('Smooth conversion error: ' + task.error);
                document.getElementById('result-smooth-box').innerHTML = `<p class="text-xs text-neonRed">Render xatosi: ${task.error}</p>`;
            }
        } catch (err) {
            clearInterval(interval);
            console.error('Polling error:', err);
        }
    }, 1000);
}

// Poll Task Status helper
async function pollTaskStatus(taskId, type) {
    const interval = setInterval(async () => {
        try {
            const task = await safeFetchJson(`/api/task/${taskId}`);
            updateProgress(task.progress, task.status === 'processing' ? 'FFmpeg bilan Smooth video tayyorlanmoqda...' : task.status);

            if (task.status === 'completed') {
                clearInterval(interval);
                updateProgress(100, 'Tayyor!');
                showVideoOutput(task.result.video_url);
            } else if (task.status === 'failed') {
                clearInterval(interval);
                alert('Xatolik: ' + task.error);
            }
        } catch (err) {
            clearInterval(interval);
            console.error('Polling error:', err);
        }
    }, 1000);
}

function updateProgress(percent, text) {
    const pctElem = document.getElementById('progress-percentage');
    const barElem = document.getElementById('progress-bar-fill');
    const txtElem = document.getElementById('progress-status-text');

    if (pctElem) pctElem.innerText = `${percent}%`;
    if (barElem) barElem.style.width = `${percent}%`;
    if (txtElem) {
        txtElem.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> ${text}`;
    }
}

function showVideoOutput(videoUrl) {
    document.getElementById('progress-container').classList.add('hidden');
    const wrapper = document.getElementById('video-output-wrapper');
    wrapper.classList.remove('hidden');

    const player = document.getElementById('output-player');
    player.src = videoUrl;

    const dlBtn = document.getElementById('download-video-btn');
    dlBtn.href = videoUrl;
}

// On load initialization
window.addEventListener('DOMContentLoaded', () => {
    initDropzones();
});
