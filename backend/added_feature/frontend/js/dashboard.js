const ctx = document.getElementById("networkChart").getContext("2d");

// Initialize Chart with empty data
let labels = [];
let downloadData = [];

const chart = new Chart(ctx, {
    type: "line",
    data: {
        labels: labels,
        datasets: [{
            label: "Current Usage (Mbps)",
            data: downloadData,
            borderColor: "#7c5dfa",
            backgroundColor: "rgba(124,93,250,0.1)",
            tension: 0.4,
            fill: true,
            pointRadius: 2
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                min: 0,
                max: 100,
                title: { display: true, text: 'Mbps' }
            }
        },
        animation: false // Disable animation for smoother real-time updates
    }
});

// Fetch analytics for total bandwidth
fetch("http://127.0.0.1:8000/api/analytics")
.then(res => res.json())
.then(data => {
    document.getElementById("totalBandwidth").innerText = data.total_bandwidth_30d + " GB";
});

// Fetch history for initial chart data
fetch("http://127.0.0.1:8000/api/history")
.then(res => res.json())
.then(data => {
    data.slice(-20).forEach(item => {
        const time = new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        labels.push(time);
        downloadData.push(item.download + item.upload);
    });
    chart.update();
});

// Connect WebSocket - Ensure port 8000 matches your FastAPI port
const socket = new WebSocket("ws://127.0.0.1:8000/ws");

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);

    // Update the UI Text Cards (keep real-time for current speed, but total is from analytics)
    document.getElementById("download").innerText = data.download + " Mbps";
    document.getElementById("upload").innerText = data.upload + " Mbps";
    document.getElementById("currentSpeed").innerText = data.total_bandwidth + " Mbps";

    // Update active devices and logic
    document.getElementById("activeDevices").innerText = data.devices.length;

    // Update Chart with real-time data
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    labels.push(now);
    downloadData.push(data.total_bandwidth);

    // Keep the graph moving by removing old data (last 20 points)
    if (labels.length > 20) {
        labels.shift();
        downloadData.shift();
    }

    chart.update();
};

socket.onerror = function(error) {
    console.error("WebSocket Error: Check if FastAPI is running on port 8000");
};

// Data Limit Functions
function loadSettings() {
    fetch("http://127.0.0.1:8000/api/settings")
    .then(res => res.json())
    .then(data => {
        document.getElementById("dailyLimit").value = data.daily_limit_gb || '';
        document.getElementById("monthlyLimit").value = data.monthly_limit_gb || '';
        document.getElementById("dailyLimitDisplay").innerText = data.daily_limit_gb || 0;
        document.getElementById("monthlyLimitDisplay").innerText = data.monthly_limit_gb || 0;
        document.getElementById("dailyUsage").innerText = data.daily_usage_gb || 0;
        document.getElementById("monthlyUsage").innerText = data.monthly_usage_gb || 0;
        
        // Update progress bars
        updateProgressBars(data.daily_usage_gb, data.daily_limit_gb, 'daily');
        updateProgressBars(data.monthly_usage_gb, data.monthly_limit_gb, 'monthly');
        
        // Show block status
        if (data.is_blocked) {
            document.getElementById("blockStatus").style.display = "block";
        } else {
            document.getElementById("blockStatus").style.display = "none";
        }
    })
    .catch(err => console.error("Error loading settings:", err));
}

function updateProgressBars(usage, limit, type) {
    const progressBar = document.getElementById(type + 'Progress');
    const percentage = limit > 0 ? (usage / limit) * 100 : 0;
    progressBar.style.width = Math.min(percentage, 100) + '%';
    
    // Change color based on percentage
    progressBar.classList.remove('warning', 'danger');
    if (percentage >= 90) {
        progressBar.classList.add('danger');
    } else if (percentage >= 70) {
        progressBar.classList.add('warning');
    }
}

function saveLimits() {
    const dailyLimit = parseFloat(document.getElementById("dailyLimit").value) || 0;
    const monthlyLimit = parseFloat(document.getElementById("monthlyLimit").value) || 0;
    
    fetch("http://127.0.0.1:8000/api/settings", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `daily_limit_gb=${dailyLimit}&monthly_limit_gb=${monthlyLimit}`
    })
    .then(res => res.json())
    .then(data => {
        alert("Limits saved successfully!");
        loadSettings();
    })
    .catch(err => console.error("Error saving settings:", err));
}

function resetUsage() {
    if (confirm("Are you sure you want to reset all usage data? This cannot be undone.")) {
        fetch("http://127.0.0.1:8000/api/reset-usage", {
            method: "POST"
        })
        .then(res => res.json())
        .then(data => {
            alert("Usage data has been reset!");
            loadSettings();
        })
        .catch(err => console.error("Error resetting usage:", err));
    }
}

// Load settings on page load
loadSettings();

// Update settings and block status from WebSocket data
const originalOnMessage = socket.onmessage;
socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    // Call original handler
    if (originalOnMessage) {
        originalOnMessage(event);
    }
    
    // Update block status from WebSocket
    if (data.is_blocked !== undefined) {
        if (data.is_blocked) {
            document.getElementById("blockStatus").style.display = "block";
        } else {
            document.getElementById("blockStatus").style.display = "none";
        }
    }
    
    // Update usage from WebSocket
    if (data.usage) {
        document.getElementById("dailyUsage").innerText = data.usage.daily_gb || 0;
        document.getElementById("monthlyUsage").innerText = data.usage.monthly_gb || 0;
        
        const dailyLimit = data.data_limit ? data.data_limit.daily_limit_gb : 0;
        const monthlyLimit = data.data_limit ? data.data_limit.monthly_limit_gb : 0;
        
        updateProgressBars(data.usage.daily_gb, dailyLimit, 'daily');
        updateProgressBars(data.usage.monthly_gb, monthlyLimit, 'monthly');
    }
};
