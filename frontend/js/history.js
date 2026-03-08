// Global variable to store history data
let historyData = [];

// LOAD HISTORY TABLE
fetch("/api/history")
.then(res => res.json())
.then(data => {
    // Store the data globally for export functions
    historyData = data;
    
    const table = document.getElementById("historyTable");

    data.slice(0,10).forEach(item => {
        table.innerHTML += `
        <tr>
            <td>${item.timestamp}</td>
            <td>${item.device}</td>
            <td>${item.ip}</td>
            <td>
                <span style="color:#6a4cff">${item.download} GB</span> /
                <span style="color:#ff7a00">${item.upload} GB</span>
            </td>
            <td>${item.action}</td>
            <td>${item.remarks}</td>
        </tr>
        `;
    });
});


// LOAD ANALYTICS
fetch("/api/analytics")
.then(res => res.json())
.then(data => {

    // Daily Peak Chart
    const ctx = document.getElementById("dailyPeakChart").getContext("2d");

    new Chart(ctx, {
        type:"bar",
        data:{
            labels:["Mon","Tue","Wed","Thu","Fri"],
            datasets:[{
                data:data.daily_peak,
                backgroundColor:"#8a6cff",
                borderRadius: 10
            }]
        },
        options: {
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { grid: { color: '#eee' } }
            }
        }
    });

    // Top Consumers
    const container = document.getElementById("topConsumers");

    data.top_consumers.forEach(d => {
        container.innerHTML += `
            <p>${d.name} - ${d.usage} GB</p>
        `;
    });

    // Total 30D
    document.getElementById("totalBandwidth").innerText =
        data.total_bandwidth_30d + " TB";
});


// Export as CSV Function
function exportCsv() {
    if (historyData.length === 0) {
        alert("No data available to export");
        return;
    }
    
    // Create CSV content
    let csvContent = "Timestamp,Device,IP,Download (GB),Upload (GB),Action,Remarks\n";
    
    historyData.forEach(item => {
        csvContent += `${item.timestamp},${item.device},${item.ip},${item.download},${item.upload},${item.action},${item.remarks}\n`;
    });
    
    // Use data URI for download
    const date = new Date().toISOString().split("T")[0];
    const uri = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvContent);
    
    // Create link and trigger download
    const link = document.createElement("a");
    link.setAttribute("href", uri);
    link.setAttribute("download", `bandwidth_history_${date}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}


// Download Report Function
function downloadReport() {
    if (historyData.length === 0) {
        alert("No data available to download");
        return;
    }
    
    // Get analytics data
    fetch("/api/analytics")
    .then(res => res.json())
    .then(analyticsData => {
        const date = new Date().toISOString().split("T")[0];
        
        // Build HTML report
        let reportHtml = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Bandwidth Usage Report - ${date}</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 40px; max-width: 1200px; margin: 0 auto; }
        h1 { color: #8a6cff; }
        h2 { color: #333; border-bottom: 2px solid #8a6cff; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
        th { background-color: #8a6cff; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .summary-card { background: #f6f5fb; padding: 20px; border-radius: 10px; flex: 1; }
        .summary-card h3 { margin: 0 0 10px 0; color: #666; }
        .summary-card p { font-size: 24px; font-weight: bold; color: #8a6cff; margin: 0; }
    </style>
</head>
<body>
    <h1>Bandwidth Usage Report</h1>
    <p>Generated: ${new Date().toLocaleString()}</p>
    <h2>Summary</h2>
    <div class="summary">
        <div class="summary-card"><h3>Total Bandwidth (30 Days)</h3><p>${analyticsData.total_bandwidth_30d} TB</p></div>
        <div class="summary-card"><h3>Total Records</h3><p>${historyData.length}</p></div>
    <h2>Top Consumers</h2>
    <table><tr><th>Device</th><th>Usage (GB)</th></tr>`;
        
        analyticsData.top_consumers.forEach(d => {
            reportHtml += `<tr><td>${d.name}</td><td>${d.usage}</td></tr>`;
        });
        
        reportHtml += `</table>
    <h2>Detailed History</h2>
    <table>
        <tr><th>Timestamp</th><th>Device</th><th>IP</th><th>Download (GB)</th><th>Upload (GB)</th><th>Action</th><th>Remarks</th></tr>`;
        
        historyData.forEach(item => {
            reportHtml += `<tr><td>${item.timestamp}</td><td>${item.device}</td><td>${item.ip}</td><td>${item.download}</td><td>${item.upload}</td><td>${item.action}</td><td>${item.remarks}</td></tr>`;
        });
        
        reportHtml += `</table></body></html>`;
        
        // Use data URI for download
        const uri = 'data:text/html;charset=utf-8,' + encodeURIComponent(reportHtml);
        
        const link = document.createElement("a");
        link.setAttribute("href", uri);
        link.setAttribute("download", `bandwidth_report_${date}.html`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });
}
</parameter>
</create_file>
