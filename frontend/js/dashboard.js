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
        animation: false
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

// Connect WebSocket
const socket = new WebSocket("ws://127.0.0.1:8000/ws");

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);

    // Update the UI Text Cards
    document.getElementById("download").innerText = data.download + " Mbps";
    document.getElementById("upload").innerText = data.upload + " Mbps";
    document.getElementById("currentSpeed").innerText = data.total_bandwidth + " Mbps";

    // Update active devices count (non-blocked devices)
    const activeCount = data.devices ? data.devices.filter(d => !d.is_blocked).length : 0;
    document.getElementById("activeDevices").innerText = activeCount;

    // Update high usage alerts
    document.getElementById("alerts").innerText = data.high_usage_alerts || 0;
    
    // Update blocked devices count
    const blockedCount = data.blocked_devices ? data.blocked_devices.length : 0;
    document.getElementById("blockedCount").innerText = blockedCount;

    // Update Device Table
    const deviceTable = document.getElementById("deviceTable");
    if (data.devices && data.devices.length > 0) {
        deviceTable.innerHTML = "";
        data.devices.forEach(device => {
            const statusClass = device.is_blocked ? "blocked" : "online";
            const statusText = device.is_blocked ? "Blocked" : "Online";
            const usagePercent = device.usage_percent || 0;
            
            deviceTable.innerHTML += `
            <tr>
                <td>${device.name}</td>
                <td>${device.ip}</td>
                <td><span class="status ${statusClass}">${statusText}</span></td>
                <td>${usagePercent}%</td>
                <td>
                    <button onclick="setLimit('${device.name}', '${device.ip}')" style="padding:4px 8px; background:#7c5dfa; color:white; border:none; border-radius:4px; cursor:pointer;">Set Limit</button>
                </td>
                <td>
                    ${device.is_blocked ? `<button onclick="unblockDevice('${device.name}')" style="padding:4px 8px; background:#ff6b6b; color:white; border:none; border-radius:4px; cursor:pointer;">Unblock</button>` : '-'}
                </td>
            </tr>
            `;
        });
    }

    // Update High Usage Alerts Section
    const highUsageSection = document.getElementById("highUsageSection");
    const highUsageTable = document.getElementById("highUsageTable");
    if (data.high_usage_alerts > 0 && data.devices) {
        highUsageSection.style.display = "block";
        const highUsageDevices = data.devices.filter(d => d.usage_percent >= 80);
        highUsageTable.innerHTML = "";
        highUsageDevices.forEach(device => {
            highUsageTable.innerHTML += `
            <tr>
                <td>${device.name}</td>
                <td>${device.ip}</td>
                <td style="color:#ff6b6b; font-weight:bold;">${device.usage_percent}%</td>
                <td>${(device.usage_percent / 100 * 1000).toFixed(2)}</td>
                <td>1000 MB</td>
                <td><span class="status warning">High Usage</span></td>
            </tr>
            `;
        });
    } else {
        highUsageSection.style.display = "none";
    }

    // Update Blocked Devices Section
    const blockedSection = document.getElementById("blockedSection");
    const blockedTable = document.getElementById("blockedTable");
    if (data.blocked_devices && data.blocked_devices.length > 0) {
        blockedSection.style.display = "block";
        blockedTable.innerHTML = "";
        data.blocked_devices.forEach(device => {
            blockedTable.innerHTML += `
            <tr>
                <td>${device.device_name}</td>
                <td>${device.ip}</td>
                <td>${device.current_usage_mb} MB</td>
                <td>${device.data_limit_mb} MB</td>
                <td>
                    <button onclick="unblockDevice('${device.device_name}')" style="padding:4px 8px; background:#28a745; color:white; border:none; border-radius:4px; cursor:pointer;">Unblock & Reset</button>
                </td>
            </tr>
            `;
        });
    } else {
        blockedSection.style.display = "none";
    }

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

// Function to set device data limit
function setLimit(deviceName, deviceIP) {
    const limit = prompt(`Enter data limit in MB for ${deviceName}:`, "1000");
    if (limit && !isNaN(limit) && limit > 0) {
        fetch("http://127.0.0.1:8000/api/device-limits?device_name=" + encodeURIComponent(deviceName) + 
              "&ip=" + encodeURIComponent(deviceIP) + "&data_limit_mb=" + parseFloat(limit), {
            method: "POST"
        })
        .then(res => res.json())
        .then(data => {
            alert("Data limit set successfully!");
        })
        .catch(err => {
            console.error(err);
            alert("Failed to set data limit");
        });
    }
}

// Function to unblock device
function unblockDevice(deviceName) {
    if (confirm(`Are you sure you want to unblock ${deviceName}? This will also reset their data usage.`)) {
        fetch("http://127.0.0.1:8000/api/device-limits/unblock?device_name=" + encodeURIComponent(deviceName), {
            method: "POST"
        })
        .then(res => res.json())
        .then(data => {
            alert("Device unblocked successfully!");
        })
        .catch(err => {
            console.error(err);
            alert("Failed to unblock device");
        });
    }
}

// Handle form submission for setting device limits
document.getElementById("limitForm").addEventListener("submit", function(e) {
    e.preventDefault();
    const deviceName = document.getElementById("deviceName").value;
    const deviceIP = document.getElementById("deviceIP").value;
    const dataLimit = document.getElementById("dataLimit").value;
    
    if (deviceName && deviceIP && dataLimit) {
        fetch("http://127.0.0.1:8000/api/device-limits?device_name=" + encodeURIComponent(deviceName) + 
              "&ip=" + encodeURIComponent(deviceIP) + "&data_limit_mb=" + parseFloat(dataLimit), {
            method: "POST"
        })
        .then(res => res.json())
        .then(data => {
            alert("Data limit set successfully!");
            document.getElementById("deviceName").value = "";
            document.getElementById("deviceIP").value = "";
            document.getElementById("dataLimit").value = "";
        })
        .catch(err => {
            console.error(err);
            alert("Failed to set data limit");
        });
    } else {
        alert("Please fill in all fields");
    }
});
