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