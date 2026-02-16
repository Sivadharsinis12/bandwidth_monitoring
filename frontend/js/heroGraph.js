const ctx = document.getElementById("heroChart");

new Chart(ctx, {
  type: "line",
  data: {
    labels: ["1","2","3","4","5","6","7"],
    datasets: [{
      data: [10,25,18,40,22,50,30],
      borderColor: "#7b61ff",
      fill: true,
      backgroundColor: "rgba(123,97,255,0.1)",
      tension: 0.4
    }]
  },
  options: {
    plugins: { legend: { display:false }},
    scales: {
      x: { display:false },
      y: { display:false }
    }
  }
});
