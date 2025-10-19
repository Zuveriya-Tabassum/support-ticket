// Fetch and render analytics cards for admin
async function loadAdminDashboard() {
    const ticketsResp = await fetch('/reports/ticket_counts');
    const ticketsStats = await ticketsResp.json();

    const perfResp = await fetch('/reports/agent_performance');
    const agents = await perfResp.json();

    // Update card UI accordingly
    document.querySelector("#totalTickets").innerText = `Total Tickets: ${Object.values(ticketsStats).reduce((a,b)=>a+b,0)}`;
    document.querySelector("#highPriority").innerText = `${ticketsStats.High||0} high priority tickets`;
    document.querySelector("#agents").innerText = `${agents.length} active agents`;
    document.querySelector("#reportPerf").innerText = "Report generated!";
}

window.onload = loadAdminDashboard;
