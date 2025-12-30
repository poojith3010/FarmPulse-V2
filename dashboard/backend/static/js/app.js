// =========================================================
//  1. CONFIGURATION
// =========================================================

const API_CONFIG = {
    GEM1_YIELD:    "http://127.0.0.1:8004", // Yield
    GEM2_GUIDE:    "http://127.0.0.1:8001", // Research
    GEM3_TEXT:     "http://127.0.0.1:8002", // Doctor (Chat)
    GEM3_VISION:   "http://127.0.0.1:8003"  // Doctor (Vision)
};

var SUPABASE_URL = "https://zffgsatjlktigwytiyah.supabase.co";
var SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpmZmdzYXRqbGt0aWd3eXRpeWFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAwMjc2NTQsImV4cCI6MjA3NTYwMzY1NH0.qsfELirIeE2yDPnknnrgep-KT3jTVz_YeqsFcGwiDtc";
var supabaseClient = window.supabaseClient || window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);


// =========================================================
//  2. AUTHENTICATION
// =========================================================

async function checkAuth() {
    const { data: { session } } = await supabaseClient.auth.getSession();
    const path = window.location.pathname;
    
    const isAuthPage = path === '/' || path.includes('login') || path.includes('signup') || path.includes('forgot'); 
    const isProtectedPage = path.includes('dashboard') || path.includes('prediction') || path.includes('research') || path.includes('doctor');
    const isSetupPage = path.includes('setup-hardware');

    if (!session) {
        if (isProtectedPage || isSetupPage) window.location.href = '/'; 
        return;
    }

    const { data: profile } = await supabaseClient.from('profiles').select('mac_address').eq('id', session.user.id).single();
    const hasDevice = profile && profile.mac_address;

    if (hasDevice) {
        window.currentUserMac = profile.mac_address;
        localStorage.setItem('user_mac', profile.mac_address);
    } else {
        localStorage.removeItem('user_mac');
    }

    if (!hasDevice && (isProtectedPage || isAuthPage)) {
        window.location.href = '/setup-hardware';
    } else if (hasDevice && (isAuthPage || isSetupPage)) {
        window.location.href = '/dashboard';
    }
}


// =========================================================
//  3. UI HELPERS
// =========================================================

function textScramble(element, endText, unit = '') {
    if(!element) return;
    let iteration = 0;
    const chars = '0123456789';
    const originalText = String(endText);
    
    if (element.dataset.scrambleInterval) clearInterval(parseInt(element.dataset.scrambleInterval));

    const interval = setInterval(() => {
        element.innerText = originalText.split("").map((letter, index) => {
            if(index < iteration) return originalText[index];
            return chars[Math.floor(Math.random() * 10)];
        }).join("") + unit;
        
        if(iteration >= originalText.length) { 
            clearInterval(interval);
            element.innerText = originalText + unit;
        }
        iteration += 1/3;
    }, 30);
    element.dataset.scrambleInterval = interval;
}

// SENSOR HELPERS
function scaleSoilMoisture(val) {
    if (val > 1023) val = 1023; 
    if (val < 400) val = 400;
    let pct = ((1023 - val) * 100) / (1023 - 400);
    return pct < 0 ? 0 : pct > 100 ? 100 : pct.toFixed(0);
}

function convertVoltageToPh(voltage) {
    let ph = 7.0 + (voltage - 2.5) * ((7.0 - 4.0) / (2.5 - 3.0));
    return ph < 0 ? 0 : ph > 14 ? 14 : ph.toFixed(1);
}

function updateSensorUI(data) {
    if (!data) return;
    
    // 1. Temperature
    if(document.getElementById("sensorTemp")) {
        textScramble(document.getElementById("sensorTemp"), data.temperature ? data.temperature.toFixed(1) : '--', '°C');
    }

    // 2. Humidity
    if(document.getElementById("sensorHumidity")) {
        textScramble(document.getElementById("sensorHumidity"), data.humidity ? data.humidity.toFixed(1) : '--', '%');
    }

    // 3. Soil Moisture (keeping existing scaling logic)
    if(document.getElementById("sensorSoil")) {
        textScramble(document.getElementById("sensorSoil"), data.soil_moisture ? scaleSoilMoisture(data.soil_moisture) : '--', '%');
    }
    
    // 4. pH Value (Direct value for RS485, or keep conversion if using analog simulator)
    const phEl = document.getElementById("sensorPh");
    if(phEl) {
        // RS485 usually sends actual pH (e.g. 7.2). If you still send raw voltage, keep convertVoltageToPh.
        // Assuming raw value for now based on your existing code:
        phEl.textContent = data.ph_value ? convertVoltageToPh(data.ph_value) : '--';
    }

    // --- NEW: ELECTRICAL CONDUCTIVITY (Replaces Rain) ---
    const ecEl = document.getElementById("sensorEc");
    if(ecEl) {
        // RS485 sensors return integer values (e.g., 500, 1200)
        const ecVal = data.electrical_conductivity ? data.electrical_conductivity : '--';
        textScramble(ecEl, ecVal);
    }

    // 5. NPK
    const npkEl = document.getElementById("sensorNPK");
    if(npkEl) {
        npkEl.textContent = `${data.nitrogen || '--'} / ${data.phosphorus || '--'} / ${data.potassium || '--'}`;
    }
}

async function loadSensorData() {
    const { data: { user } } = await supabaseClient.auth.getUser();
    if (!user) return;
    const { data } = await supabaseClient.from("sensor_data").select("*").eq("user_id", user.id).order("created_at", { ascending: false }).limit(1).maybeSingle();
    updateSensorUI(data);
}


// =========================================================
//  4. AI MODULES
// =========================================================

// --- GEM 1: YIELD (RESTORED TO OLD WORKING LOGIC) ---
async function getSeasonalForecast() {
    const dateVal = document.getElementById('forecastDate').value;
    const sizeVal = document.getElementById('farmSize').value;
    const outputEl = document.getElementById('yieldOutput');
    const perAcreEl = document.getElementById('yieldPerAcre');
    const explanationEl = document.getElementById('aiExplanation');
    const metaEl = document.getElementById('yield-meta');

    if (!dateVal || !sizeVal) {
        explanationEl.innerHTML = "<span class='text-red-400'>Please provide both a Target Date and Farm Size.</span>";
        return;
    }

    // Loading State
    outputEl.innerText = "...";
    metaEl.innerText = "CALCULATING...";
    explanationEl.innerHTML = "<span class='animate-pulse text-emerald-400'>Connecting to Neural Engine...</span>";

    try {
        const response = await fetch(`${API_CONFIG.GEM1_YIELD}/forecast-yield`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                target_date: dateVal,
                farm_size_acres: parseFloat(sizeVal) 
            })
        });

        const data = await response.json();

        if (data.error) throw new Error(data.error);

        // Success Update
        textScramble(outputEl, data.predicted_yield_kg);
        perAcreEl.innerText = `${data.yield_per_acre} KG / Acre`;
        explanationEl.innerHTML = data.reply.replace(/\n/g, "<br>");
        metaEl.innerText = "COMPLETE";
        metaEl.className = "absolute top-4 right-4 text-xs font-mono text-emerald-500";

        // NO MEMORY SAVING HERE to prevent crashes

    } catch (e) {
        console.error(e);
        outputEl.innerText = "ERR";
        metaEl.innerText = "OFFLINE";
        metaEl.className = "absolute top-4 right-4 text-xs font-mono text-red-500";
        explanationEl.innerHTML = "<span class='text-red-400'>Error: AI Module is offline. Run 'run_gems.bat'.</span>";
    }
}

// --- GEM 2: RESEARCHER ---
async function askResearcher() {
    const input = document.getElementById('researchInput');
    const chatBox = document.getElementById('researchChat');
    const query = input.value.trim();
    if (!query) return;

    // 1. User Message
    chatBox.innerHTML += `<div class="flex justify-end mb-4"><div class="bg-emerald-600/20 border border-emerald-500/30 text-emerald-100 p-3 rounded-2xl rounded-tr-sm max-w-[80%]">${query}</div></div>`;
    input.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;

    // 2. Loading Bubble
    const loadingId = "loading-" + Date.now();
    chatBox.innerHTML += `
        <div id="${loadingId}" class="flex justify-start mb-4">
            <div class="bg-white/5 border border-white/10 text-gray-400 p-3 rounded-2xl rounded-tl-sm text-xs flex gap-1 items-center">
                <span class="animate-bounce">●</span><span class="animate-bounce" style="animation-delay: 0.1s">●</span><span class="animate-bounce" style="animation-delay: 0.2s">●</span>
            </div>
        </div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const res = await fetch(`${API_CONFIG.GEM2_GUIDE}/ask-advisor`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: query })
        });
        const data = await res.json();
        
        // 3. Remove Loading & Show Answer
        document.getElementById(loadingId).remove();
        
        const botReply = data.answer || data.reply || "No answer found.";
        chatBox.innerHTML += `<div class="flex justify-start mb-4"><div class="bg-white/5 border border-white/10 text-gray-300 p-3 rounded-2xl rounded-tl-sm max-w-[80%]">${botReply}</div></div>`;
        
    } catch (e) {
        document.getElementById(loadingId).remove();
        chatBox.innerHTML += `<div class="text-xs text-red-400 text-center my-2">Connection Failed</div>`;
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

// --- GEM 3A: DOCTOR TEXT CHAT ---
async function askDoctorText() {
    const input = document.getElementById('doctorInput');
    const chatBox = document.getElementById('doctorChat');
    const query = input.value.trim();
    if (!query) return;

    // FIX: Get Real MAC
    const realMac = window.currentUserMac || localStorage.getItem('user_mac');
    if (!realMac) {
        alert("Error: No Device Linked. Please go to 'Setup Hardware' first.");
        return;
    }

    // UI: Add User Message
    chatBox.innerHTML += `<div class="flex justify-end mb-4"><div class="bg-red-600/20 border border-red-500/30 text-red-100 p-3 rounded-2xl rounded-tr-sm max-w-[80%]">${query}</div></div>`;
    input.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;
    
    // UI: Loading Bubble
    const loadingId = "doc-loading-" + Date.now();
    chatBox.innerHTML += `
        <div id="${loadingId}" class="flex justify-start mb-4">
            <div class="bg-white/5 border border-white/10 text-gray-400 p-3 rounded-2xl rounded-tl-sm text-xs flex gap-1 items-center">
                <span class="material-icons text-xs animate-spin">sync</span> Checking device ${realMac}...
            </div>
        </div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const payload = {
            query_text: query,
            mac_address: realMac
        };

        const res = await fetch(`${API_CONFIG.GEM3_TEXT}/ask`, {
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' }, 
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        document.getElementById(loadingId).remove();
        
        const reply = data.reply || "No response.";
        chatBox.innerHTML += `<div class="flex justify-start mb-4"><div class="bg-white/5 border border-white/10 text-gray-300 p-3 rounded-2xl rounded-tl-sm max-w-[80%]">${reply}</div></div>`;

    } catch (e) {
        document.getElementById(loadingId).remove();
        chatBox.innerHTML += `<div class="text-xs text-red-400 text-center my-2">Doctor Offline</div>`;
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

// --- GEM 3B: DOCTOR VISION ---
async function uploadLeaf() {
    const fileInput = document.getElementById('leafUpload');
    const file = fileInput.files[0];
    if (!file) return;

    // 1. Show Image Preview
    const previewContainer = document.getElementById('previewContainer');
    const uploadLabel = document.getElementById('uploadLabel');
    const objectUrl = URL.createObjectURL(file);
    
    uploadLabel.classList.add('hidden'); 
    previewContainer.classList.remove('hidden');
    previewContainer.innerHTML = `<img src="${objectUrl}" class="w-full h-48 object-cover rounded-xl border border-white/20 shadow-lg">`;

    // 2. Show Loading UI
    const loader = document.getElementById('visionLoader');
    const resultBox = document.getElementById('visionResult');
    const placeholder = document.getElementById('visionPlaceholder');
    
    placeholder.classList.add('hidden');
    loader.classList.remove('hidden');
    resultBox.classList.add('hidden');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`${API_CONFIG.GEM3_VISION}/analyze-leaf`, { method: 'POST', body: formData });
        const data = await res.json();
        
        // 3. Show Results
        loader.classList.add('hidden');
        resultBox.classList.remove('hidden');
        
        document.getElementById('diagnosisTitle').innerText = data.diagnosis || data.prediction || "Unknown";
        document.getElementById('diagnosisText').innerText = data.confidence ? `${Math.round(parseFloat(data.confidence))}% Match` : "";
        
        const adviceText = data.treatment || data.doctor_note || data.reply;
        document.getElementById('doctorAdvice').innerHTML = `
            <div class="bg-white/5 p-3 rounded-lg border border-white/10 mt-2">
                <strong class="text-red-400 text-xs uppercase tracking-wide">Doctor's Note:</strong>
                <p class="mt-1 text-gray-300">${adviceText}</p>
            </div>
        `;

    } catch (e) {
        loader.classList.add('hidden');
        alert("Vision AI Offline");
        uploadLabel.classList.remove('hidden');
        previewContainer.classList.add('hidden');
    }
}


// =========================================================
//  5. INIT (CLEAN STATE)
// =========================================================

document.addEventListener("DOMContentLoaded", async () => {
    await checkAuth();

    // 1. Dashboard Sensors Live Update
    if(document.getElementById("sensorTemp")) {
        loadSensorData();
        setInterval(loadSensorData, 5000); 
    }

    // 2. Default Date for Prediction (UI Polish only)
    if(document.getElementById('forecastDate')) {
        document.getElementById('forecastDate').valueAsDate = new Date();
    }
});