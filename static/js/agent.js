const agentId = /* fetch this from Flask session injected in HTML */
async function loadAgentDashboard() {
    // Get agent assigned tickets
    const resp = await fetch(`/tickets/assigned/${agentId}`);
    const tickets = await resp.json();
    // Update cards: open, in-progress, resolved, high-priority
    // Suggest advances based on status
}
window.onload = loadAgentDashboard;
