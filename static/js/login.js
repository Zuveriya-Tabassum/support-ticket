const alertBox = document.getElementById("alert");

function showAlert(message, type="error") {
    alertBox.innerText = message;
    alertBox.className = `alert ${type}`;
    alertBox.style.display = "block";
    setTimeout(() => { alertBox.style.display="none"; }, 4000);
}

async function login() {
    const email = document.getElementById("login_email").value.trim();
    const password = document.getElementById("login_password").value;

    if (!email || !password) {
        showAlert("Please fill in all fields!");
        return;
    }

    try {
        const response = await fetch("/users/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        if (response.ok) {
            showAlert(data.message, "success");

            // redirect after login (dashboard/home)
            setTimeout(() => {
                window.location.href = "/dashboard";
            }, 1500);
        } else {
            showAlert(data.message, "error");
        }
    } catch (err) {
        showAlert("Server error. Try again!", "error");
    }
}
