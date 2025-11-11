document.addEventListener('DOMContentLoaded', () => {
    // ===================== ALERT AUTO-DISMISS =====================
    setTimeout(() => {
        document.querySelectorAll(".alert").forEach((alert) => {
            alert.classList.add("hide-slide");
            alert.addEventListener("transitionend", () => alert.remove(), {
                once: true,
            });
        });
    }, 3000);

    // Optional: intercept login to do client-side validation or switch to AJAX login
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', (ev) => {
            // Default: allow server POST - remove this block to keep default server submit.
            // Uncomment to enable AJAX login:
            // ev.preventDefault();
            // ajaxLogin();
        });
    }

    // Intercept account creation to optionally use AJAX and show in-page alerts
    const createForm = document.getElementById('createAccountForm');
    if (createForm) {
        createForm.addEventListener('submit', async (ev) => {
            // If you want full page POST handled by Flask, comment out the next two lines.
            ev.preventDefault();
            await ajaxCreateAccount(new FormData(createForm));
        });
    }
});

async function ajaxCreateAccount(formData) {
    const payload = Object.fromEntries(formData.entries());
    try {
        const res = await fetch('/auth/api/create_account', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const json = await res.json();
        showNotification(json.message, json.status === 'success' ? 'success' : 'danger');

        if (json.status === 'success') {
            // close modal (Bootstrap)
            const modalEl = document.getElementById('createAccountModal');
            const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
            modal.hide();
            // optionally clear the form
            document.getElementById('createAccountForm').reset();
        }
    } catch (err) {
        showNotification('Network error creating account', 'danger');
        console.error(err);
    }
}

function showNotification(message, category = 'info') {
    const container = document.querySelector('.alert-container') || document.body;
    const alert = document.createElement('div');
    alert.className = `alert alert-${category} alert-dismissible fade show alert-top`;
    alert.role = 'alert';
    alert.innerHTML = `${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>`;
    container.appendChild(alert);
    // auto-remove after 5s
    setTimeout(() => {
        if (alert && alert.parentNode) alert.parentNode.removeChild(alert);
    }, 5000);
}
