// LOAD HISTORY TABLE
fetch("/api/history")
.then(res => res.json())
.then(data => {

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
