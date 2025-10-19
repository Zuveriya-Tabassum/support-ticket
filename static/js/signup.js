// Password strength
const passwordInput = document.getElementById("password");
const strengthText = document.getElementById("strength-text");
const alertBox = document.getElementById("alert");
const roleInput = document.getElementById("role");

// Update password strength indicator
passwordInput.addEventListener("input", () => {
    const val = passwordInput.value;
    let strength = "Weak";

    if (val.length >= 8 && /[A-Z]/.test(val) && /[0-9]/.test(val) && /[!@#$%^&*]/.test(val)) {
        strength = "Strong";
        strengthText.style.color = "green";
    } else if (val.length >= 6) {
        strength = "Medium";
        strengthText.style.color = "orange";
    } else {
        strengthText.style.color = "red";
    }
    strengthText.innerText = `Password strength: ${strength}`;
});

// Show custom alert
function showAlert(message, type="error") {
    alertBox.innerText = message;
    alertBox.className = `alert ${type}`;
    alertBox.style.display = "block";
    setTimeout(() => { alertBox.style.display = "none"; }, 4000);
}

// Role selection buttons
document.getElementById("userBtn").addEventListener("click", () => {
    roleInput.value = "user";
    document.getElementById("userBtn").classList.add("selected");
    document.getElementById("adminBtn").classList.remove("selected");
    document.getElementById("agentBtn").classList.remove("selected");
});
document.getElementById("adminBtn").addEventListener("click", () => {
    roleInput.value = "admin";
    document.getElementById("adminBtn").classList.add("selected");
    document.getElementById("userBtn").classList.remove("selected");
    document.getElementById("agentBtn").classList.remove("selected");
});
document.getElementById("agentBtn").addEventListener("click", () => {
    roleInput.value = "agent";
    document.getElementById("agentBtn").classList.add("selected");
    document.getElementById("adminBtn").classList.remove("selected");
    document.getElementById("userBtn").classList.remove("selected");
});
// Signup function
async function signup() {
    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm_password").value;
    const role = roleInput.value;

    // Client-side validation
    if (!name || !email || !password || !confirmPassword) {
        showAlert("Please fill in all required fields!");
        return;
    }
    if (password !== confirmPassword) {
        showAlert("Passwords do not match!");
        return;
    }

    try {
        const response = await fetch("/users/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, password, role })
        });

        const data = await response.json();

        if (response.ok) {
            // Success alert
            showAlert(`✅ ${data.message} as ${role}`, "success");
            // Redirect to login after 1.5s
            setTimeout(() => { window.location.href = "/"; }, 1500);
        } else {
            // Error alert
            showAlert(data.message || "Signup failed", "error");
        }
    } catch (err) {
        showAlert("Server error. Try again!", "error");
        console.error(err);
    }
}
