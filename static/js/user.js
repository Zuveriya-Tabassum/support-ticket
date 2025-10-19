const userId = /* fetch this from Flask session injected in HTML */
async function loadUserDashboard() {
    // Fetch user tickets and comments
    const resp = await fetch(`/tickets?user_id=${userId}`);
    const userTickets = await resp.json();
    // Render ticket stats/cards accordingly
}
window.onload = loadUserDashboard;
