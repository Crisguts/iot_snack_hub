/* ========== App-level helpers & DOM ready ========== */
(function () {
    const $ = (sel, ctx = document) => ctx.querySelector(sel);
    const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

    // show notification in-page (bootstrap-style)
    function showNotification(message, type = "info", timeout = 5000) {
        const container = document.body;
        const notification = document.createElement("div");
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = "top: 20px; right: 20px; z-index: 9999; max-width: 320px;";
        notification.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
        container.appendChild(notification);
        setTimeout(() => {
            notification.classList.add("hide-slide");
            setTimeout(() => notification.remove(), 600);
        }, timeout);
    }

    // safe fetch wrapper with JSON
    async function fetchJson(url, opts = {}) {
        const fetchOpts = Object.assign({ credentials: "same-origin" }, opts);
        const res = await fetch(url, fetchOpts);
        if (!res.ok) {
            const text = await res.text();
            throw new Error(`HTTP ${res.status}: ${text}`);
        }
        return res.json().catch(() => ({}));
    }

    /* ========== Date & Time ========== */
    function updateDateTime() {
        const now = new Date();
        const day = now.getDate();
        const daySuffix = (d) => {
            if (d > 3 && d < 21) return "th";
            switch (d % 10) {
                case 1: return "st";
                case 2: return "nd";
                case 3: return "rd";
                default: return "th";
            }
        };
        const options = { year: "numeric", month: "long", day: "numeric" };
        // replace only the first numeric block for day
        const formattedDate = now.toLocaleDateString("en-US", options).replace(/\d+/, day + daySuffix(day));
        const dateEl = $("#date");
        if (dateEl) dateEl.textContent = formattedDate;

        const hours = now.getHours().toString().padStart(2, "0");
        const minutes = now.getMinutes().toString().padStart(2, "0");
        const clockEl = $("#clock");
        if (clockEl) clockEl.textContent = `${hours}:${minutes}`;
    }
    setInterval(updateDateTime, 1000);
    updateDateTime();

    /* ========== Auto-dismiss alerts ========== */
    setTimeout(() => {
        $$(".alert").forEach((alert) => {
            alert.classList.add("hide-slide");
            alert.addEventListener("transitionend", () => alert.remove(), { once: true });
        });
    }, 3000);

    /* ========== Show customer / card animations progressively ========== */
    $$(".Customer").forEach((row, index) => {
        setTimeout(() => row.classList.add("visible"), index * 100);
    });
    $$(".fridge-card").forEach((card, index) => {
        setTimeout(() => card.classList.add("visible"), index * 150);
    });
    $$(".email-card").forEach((card, index) => {
        setTimeout(() => card.classList.add("visible"), index * 150);
    });

    /* ========== Delete modal setup ========== */
    (function initDeleteModal() {
        const deleteModal = document.getElementById("deleteModal");
        const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
        if (!deleteModal || !confirmDeleteBtn) return;
        deleteModal.addEventListener("show.bs.modal", (event) => {
            const button = event.relatedTarget;
            if (!button) return;
            const deleteUrl = button.getAttribute("data-delete-url");
            confirmDeleteBtn.setAttribute("href", deleteUrl || "#");
        });
    })();

    /* ========== View / Edit client wiring ========== */
    (function initViewEditFlow() {
        const viewClientModal = document.getElementById("viewClientModal");
        const editClientModal = document.getElementById("editClientModal");
        const editClientForm = document.getElementById("editClientForm");
        const editFromViewBtn = document.getElementById("editFromViewBtn");

        if (viewClientModal) {
            viewClientModal.addEventListener("show.bs.modal", (event) => {
                const row = event.relatedTarget;
                if (!row) return;
                const customerId = row.getAttribute("data-id");
                const firstName = row.getAttribute("data-firstname");
                const lastName = row.getAttribute("data-lastname");
                const email = row.getAttribute("data-email");
                const phone_num = row.getAttribute("data-phone");
                const dob = row.getAttribute("data-dob");
                const membership = row.getAttribute("data-membership");
                const points = row.getAttribute("data-points");
                const dateStr = row.getAttribute("data-date");

                const setText = (id, text) => {
                    const el = document.getElementById(id);
                    if (el) el.textContent = text ?? "N/A";
                };
                setText("modalFirstName", firstName);
                setText("modalLastName", lastName);
                setText("modalEmail", email);
                setText("modalPhone", phone_num || "N/A");
                setText("modalDob", dob || "N/A");
                setText("modalMembership", membership || "N/A");
                setText("modalPoints", points || "0");
                setText("modalDate", dateStr ? new Date(dateStr).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }) : "N/A");

                const hidden = document.getElementById("editCustomerId");
                if (hidden) hidden.value = customerId;
            });
        }

        if (editFromViewBtn && editClientForm) {
            editFromViewBtn.addEventListener("click", () => {
                const customerId = document.getElementById("editCustomerId").value;
                editClientForm.action = `/client/update/${customerId}`;
                document.getElementById("editFirstName").value = document.getElementById("modalFirstName").textContent;
                document.getElementById("editLastName").value = document.getElementById("modalLastName").textContent;
                document.getElementById("editEmail").value = document.getElementById("modalEmail").textContent;
                const pointsEl = document.getElementById("editPoints");
                if (pointsEl) {
                    pointsEl.value = document.getElementById("modalPoints").textContent || "0";
                }
            });
        }

        const editCancelBtn = document.getElementById("editBackButton");
        if (editCancelBtn && editClientModal && viewClientModal) {
            editCancelBtn.addEventListener("click", () => {
                const editModalInstance = bootstrap.Modal.getInstance(editClientModal);
                if (editModalInstance) editModalInstance.hide();
                const viewModalInstance = new bootstrap.Modal(viewClientModal);
                viewModalInstance.show();
            });
        }

        // Optional: AJAX submit for edit form (fallback to regular POST if not desired)
        if (editClientForm) {
            editClientForm.addEventListener("submit", async (ev) => {
                // If you want server-side POST behavior, comment out the next two lines and let it submit.
                ev.preventDefault();
                const data = new FormData(editClientForm);
                const payload = Object.fromEntries(data.entries());
                try {
                    const url = editClientForm.action || `/update/${payload.customer_id}`;
                    const res = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                    });
                    const json = await res.json();
                    if (json.success) {
                        showNotification("Client updated", "success");
                        // refresh page to show latest (or update DOM directly)
                        setTimeout(() => location.reload(), 700);
                    } else {
                        showNotification(json.error || "Update failed", "danger");
                    }
                } catch (err) {
                    console.error(err);
                    showNotification("Network error updating client", "danger");
                }
            });
        }
    })();

    /* ========== Add client form - optional AJAX passthrough ========== */
    (function initAddClient() {
        const addForm = document.getElementById("addCustomerForm");
        if (!addForm) return;

        addForm.addEventListener("submit", async (ev) => {
            // default behavior is server POST to /add — comment out these lines to keep default
            ev.preventDefault();
            const data = new FormData(addForm);
            const payload = Object.fromEntries(data.entries());
            try {
                const res = await fetch(addForm.action || "/add", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
                const json = await res.json();
                if (json.success) {
                    showNotification("Client added", "success");
                    const modalEl = document.getElementById("add-customer");
                    const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                    modal.hide();
                    addForm.reset();
                    setTimeout(() => location.reload(), 700);
                } else {
                    showNotification(json.error || "Failed to add client", "danger");
                }
            } catch (err) {
                console.error(err);
                showNotification("Network error adding client", "danger");
            }
        });
    })();

    /* ========== Optional realtime refresh code (keeps client page responsive) ========== */
    (function initRealtimeRefresh() {
        // Only run on pages with fridge cards
        if (!document.querySelector('[id^="fridgeCard"]')) return;

        // The dashboard file uses /dashboard/api/latest. Clients page doesn't require it but leaving safety check.
        async function refreshFridgeData() {
            try {
                const result = await fetchJson("/dashboard/api/latest").catch(() => ({ success: false }));
                if (result && result.success && result.data) {
                    // safely update any matching UI fields (this page doesn't have fridge cards by id usually)
                    for (const fridgeId in result.data) {
                        const entry = result.data[fridgeId];
                        const tempEl = document.querySelector(`#fridgeCard${fridgeId} .temperature`);
                        const humEl = document.querySelector(`#fridgeCard${fridgeId} .humidity`);
                        if (tempEl && typeof entry.temperature !== "undefined") tempEl.textContent = entry.temperature + '°C';
                        if (humEl && typeof entry.humidity !== "undefined") humEl.textContent = entry.humidity + '%';
                    }
                }
            } catch (err) {
                // non-fatal
            }
        }
        // call every 3s if endpoint exists (safe to keep)
        setInterval(refreshFridgeData, 3000);
    })();

    /* ========== small accessibility helpers ========== */
    document.addEventListener("shown.bs.modal", (e) => {
        const dateInput = e.target && e.target.querySelector && e.target.querySelector('input[type="date"]');
        if (dateInput) dateInput.focus();
    });

    /* ========== finished init ========== */
})();
