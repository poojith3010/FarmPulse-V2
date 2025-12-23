const API_URLS = {
    gem1: "http://127.0.0.1:8004",
    gem2: "http://127.0.0.1:8001",
    gem3a: "http://127.0.0.1:8002",
    gem3b: "http://127.0.0.1:8003"
};

// --- TABS & NAVIGATION ---
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
    
    document.getElementById(tabId).classList.add('active');
    document.getElementById('nav-' + tabId).classList.add('active');
}

function switchDoctor(mode) {
    // Reset buttons
    document.getElementById('btn-doc-text').classList.remove('active');
    document.getElementById('btn-doc-vision').classList.remove('active');
    
    // Hide panels
    document.getElementById('doc-text-panel').classList.add('hidden');
    document.getElementById('doc-vision-panel').classList.add('hidden');

    if (mode === 'text') {
        document.getElementById('btn-doc-text').classList.add('active');
        document.getElementById('doc-text-panel').classList.remove('hidden');
    } else {
        document.getElementById('btn-doc-vision').classList.add('active');
        document.getElementById('doc-vision-panel').classList.remove('hidden');
    }
}

// --- UTILS: LOADING & REPORTS ---
function showLoading(chatId) {
    const chat = document.getElementById(chatId);
    const loaderId = `loader-${Date.now()}`;
    chat.innerHTML += `<div class="loading-bubble" id="${loaderId}"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
    chat.scrollTop = chat.scrollHeight;
    return loaderId;
}

function removeLoading(loaderId) {
    const el = document.getElementById(loaderId);
    if (el) el.remove();
}

function toggleReport(reportId) {
    const report = document.getElementById(reportId);
    report.classList.toggle('visible');
}

// --- GEM 1: SEASONAL FORECAST ---

// Auto-set date to today
document.addEventListener('DOMContentLoaded', () => {
    const dateInput = document.getElementById('forecast-date');
    if(dateInput) {
        dateInput.valueAsDate = new Date();
    }
});

async function getSeasonalForecast() {
    const dateVal = document.getElementById('forecast-date').value;
    const sizeVal = document.getElementById('farm-size').value; // <--- Get Size

    if (!dateVal || !sizeVal) {
        alert("Please enter both date and farm size.");
        return;
    }

    const loader = showLoading('yield-chat'); 

    try {
        const response = await fetch(`${API_URLS.gem1}/forecast-yield`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                target_date: dateVal,
                farm_size_acres: parseFloat(sizeVal) // <--- Send Size
            })
        });

        const data = await response.json();
        removeLoading(loader);

        if (data.error) { alert(data.error); return; }

        document.getElementById('yield-output').innerText = `${data.predicted_yield_kg} KG`;

        const chat = document.getElementById('yield-chat');
        chat.innerHTML = `
            <div class="bot-msg">
                <div style="font-weight:bold; margin-bottom:5px;">
                    <i class="fas fa-ruler-combined"></i> Rate: ${data.yield_per_acre} KG/Acre
                </div>
                <div class="msg-text">${data.reply}</div>
            </div>`;

    } catch (e) {
        removeLoading(loader);
        alert("Error connecting to Gem 1.");
    }
}

// --- GEM 2: RESEARCHER ---
async function askResearcher() {
    const input = document.getElementById('researcher-input');
    const chat = document.getElementById('researcher-chat');
    const q = input.value;
    if (!q) return;

    chat.innerHTML += `<div class="user-msg">${q}</div>`;
    input.value = "";
    const loader = showLoading('researcher-chat');

    try {
        const response = await fetch(`${API_URLS.gem2}/ask-advisor`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: q })
        });
        const res = await response.json();
        removeLoading(loader);
        
        // Simple response for researcher
        chat.innerHTML += `
            <div class="bot-msg">
                <i class="fas fa-robot"></i>
                <div class="msg-text">${res.answer.replace(/\n/g, '<br>')}</div>
            </div>`;
    } catch (e) {
        removeLoading(loader);
        chat.innerHTML += `<div class="bot-msg">Error connecting to Gem 2.</div>`;
    }
    chat.scrollTop = chat.scrollHeight;
}

// --- GEM 3A: NUTRIENT ADVISOR ---
// --- GEM 3A: NUTRIENT ADVISOR ---
async function askNutrient() {
    const input = document.getElementById('nutrient-input');
    const chat = document.getElementById('nutrient-chat');
    const q = input.value;
    if (!q) return;

    // 1. GET THE KEY
    const userMac = localStorage.getItem('user_mac');

    if (!userMac) {
        alert("⚠️ No Device Found! Please log in.");
        return;
    }

    chat.innerHTML += `<div class="user-msg">${q}</div>`;
    input.value = "";
    const loader = showLoading('nutrient-chat');

    try {
        const response = await fetch(`${API_URLS.gem3a}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                query_text: q,
                mac_address: userMac // <--- DYNAMIC KEY USED HERE
            })
        });
        const res = await response.json();
        removeLoading(loader);

        const reportId = `rep-3a-${Date.now()}`;
        const techReport = JSON.stringify({
            intent: res.intent,
            rule_output: res.technical_rule
        }, null, 2);

        chat.innerHTML += `
            <div class="bot-msg" style="flex-direction:column; align-items:flex-start;">
                <div style="display:flex; gap:10px;">
                    <i class="fas fa-seedling" style="margin-top:5px;"></i>
                    <div class="msg-text">${res.reply.replace(/\n/g, '<br>')}</div>
                </div>
                <button class="toggle-report-btn" onclick="toggleReport('${reportId}')">View Technical Details</button>
                <div id="${reportId}" class="tech-report">${techReport}</div>
            </div>`;
            
    } catch (e) {
        removeLoading(loader);
        chat.innerHTML += `<div class="bot-msg">Error connecting to Gem 3A.</div>`;
    }
    chat.scrollTop = chat.scrollHeight;
}

// --- GEM 3B: VISION DOCTOR ---

// NEW: Image Preview Function
function previewImage(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = document.getElementById('image-preview');
            img.src = e.target.result;
            img.classList.remove('hidden');
            
            // Hide placeholder text
            document.getElementById('upload-placeholder').classList.add('hidden');
            // Add 'has-image' class for CSS styling if needed
            document.querySelector('.upload-zone').classList.add('has-image');
        }
        reader.readAsDataURL(file);
    }
}

async function scanLeaf() {
    const fileInput = document.getElementById('leaf-upload');
    if (fileInput.files.length === 0) return alert("Please select an image!");

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const resultDiv = document.getElementById('vision-result');
    resultDiv.innerHTML = '<i class="fas fa-spinner fa-spin fa-3x"></i><p>Analyzing Leaf...</p>';
    resultDiv.classList.remove('empty-state');

    try {
        const response = await fetch(`${API_URLS.gem3b}/analyze-leaf`, {
            method: 'POST',
            body: formData
        });
        const res = await response.json();
        
        const statusColor = res.prediction.toLowerCase().includes('healthy') ? '#00b894' : '#e17055';
        const reportId = `rep-3b-${Date.now()}`;
        const techReport = JSON.stringify(res.technical_facts, null, 2);

        resultDiv.innerHTML = `
            <div style="text-align:left; width:100%;">
                <div style="display:flex; justify-content:space-between; align-items:center; padding-bottom:10px; border-bottom:1px solid #eee;">
                    <h3 style="margin:0; color:#2d3436;">${res.prediction}</h3>
                    <span style="background:${statusColor}; color:white; padding:4px 10px; border-radius:15px; font-size:0.8rem;">
                        ${res.confidence}
                    </span>
                </div>
                
                <div style="margin-top:15px; font-size:0.95rem; line-height:1.6; color:#2d3436;">
                    ${res.doctor_note.replace(/\n/g, '<br>')}
                </div>

                <button class="toggle-report-btn" onclick="toggleReport('${reportId}')">View Medical Report</button>
                <div id="${reportId}" class="tech-report">${techReport}</div>
            </div>
        `;
    } catch (e) {
        resultDiv.innerHTML = '<p style="color:red;">Error connecting to Gem 3B.</p>';
    }
}