// Dashboard real-time monitoring and control
// Handles temperature gauges, fan controls, email alerts, and history charts

// Prevent multiple script executions
if (window.dashboardInitialized) {
    console.warn("Dashboard already initialized, skipping duplicate execution");
} else {
    window.dashboardInitialized = true;

    // Update date and time display
    function updateDateTime() {
        const now = new Date();
        const day = now.getDate();
        const daySuffix = d => (d > 3 && d < 21) ? 'th' : (d % 10 === 1 ? 'st' : d % 10 === 2 ? 'nd' : d % 10 === 3 ? 'rd' : 'th');
        const options = { year: "numeric", month: "long", day: "numeric" };
        const formattedDate = now.toLocaleDateString("en-US", options).replace(/\d+/, day + daySuffix(day));
        const dateEl = document.getElementById("date");
        if (dateEl) dateEl.textContent = formattedDate;
        const hours = now.getHours().toString().padStart(2, "0");
        const minutes = now.getMinutes().toString().padStart(2, "0");
        const clockEl = document.getElementById("clock");
        if (clockEl) clockEl.textContent = `${hours}:${minutes}`;
    }
    setInterval(updateDateTime, 1000);
    updateDateTime();

    // Auto-dismiss alert messages after 3 seconds
    setTimeout(() => { document.querySelectorAll(".alert").forEach(a => { a.classList.add("hide-slide"); a.addEventListener("transitionend", () => a.remove(), { once: true }) }) }, 3000);

    // Animate cards on page load
    document.querySelectorAll(".Customer, .fridge-card, .email-card").forEach((el, i) => setTimeout(() => el.classList.add("visible"), i * 150));

    // Fan control functions
    const fanTogglesInProgress = new Set(); // Track toggles being changed

    function updateFanAnimation(fridgeId, isOn) {
        const fanIcon = document.getElementById(`fanIcon${fridgeId}`);
        if (fanIcon) { fanIcon.classList.toggle("fan-spinning", isOn); fanIcon.classList.toggle("fan-off", !isOn); }
    }

    function initializeFanToggles() {
        fetch("/dashboard/fan/states").then(res => res.json()).then(data => {
            if (data.success) {
                document.querySelectorAll(".fanToggle").forEach(toggle => {
                    const id = parseInt(toggle.getAttribute("data-fridge"));
                    toggle.checked = data.fan_states[id] || false;
                    updateFanAnimation(id, data.fan_states[id] || false);
                });
            }
        }).catch(err => console.error("Error fetching fan states:", err));
    }
    initializeFanToggles();

    // Use event delegation on document to avoid multiple listeners
    document.addEventListener("change", function (e) {
        if (!e.target.classList.contains("fanToggle")) return; // Only handle fan toggles

        const toggle = e.target;
        const id = parseInt(toggle.getAttribute("data-fridge"));
        const newState = toggle.checked;

        console.log(`Fan toggle change event - fridge ${id}, new state: ${newState}`);

        // Prevent multiple simultaneous toggles for the SAME fridge
        if (fanTogglesInProgress.has(id)) {
            console.log("Toggle already in progress, reverting");
            toggle.checked = !newState; // Revert the visual change
            return;
        }

        fanTogglesInProgress.add(id);
        toggle.disabled = true;

        console.log(`Sending POST to /dashboard/fan/${id}`);
        fetch(`/dashboard/fan/${id}`, { method: "POST", headers: { "Content-Type": "application/json" } })
            .then(res => res.json()).then(data => {
                console.log("Fan toggle response:", data);
                if (data.success) {
                    toggle.checked = data.fan_state;
                    updateFanAnimation(id, data.fan_state);
                } else {
                    toggle.checked = !newState;
                    alert("Failed to toggle fan: " + (data.error || "Unknown error"));
                }
            }).catch(err => {
                console.error("Fan toggle error:", err);
                toggle.checked = !newState;
                alert("Network error: " + err.message);
            }).finally(() => {
                toggle.disabled = false;
                fanTogglesInProgress.delete(id);
            });
    });

    // ===================== EMAIL TEST =====================
    const testEmailBtn = document.getElementById("testEmailBtn");
    if (testEmailBtn) testEmailBtn.addEventListener("click", () => {
        testEmailBtn.disabled = true; testEmailBtn.textContent = "Sending...";
        fetch("/dashboard/api/email/test", { method: "POST", headers: { "Content-Type": "application/json" } })
            .then(res => res.json()).then(data => {
                if (data.success) {
                    showNotification('Test email sent! Reply "YES" to activate fan.', "success");
                } else {
                    showNotification("Failed to send email: " + (data.error || "Unknown error"), "danger");
                }
            }).catch(err => {
                showNotification("Network error: " + err.message, "danger");
            }).finally(() => { testEmailBtn.disabled = false; testEmailBtn.textContent = "Send Test Email"; });
    });

    function showNotification(msg, type = "info") {
        const n = document.createElement("div");
        n.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        n.style.cssText = "top:20px;right:20px;z-index:9999;max-width:300px;";
        n.innerHTML = `${msg}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
        document.body.appendChild(n);
        setTimeout(() => { n.classList.add("hide-slide"); setTimeout(() => n.remove(), 500); }, 5000);
    }

    function checkEmailSignals() {
        fetch("/dashboard/api/email/check-signals").then(res => res.json()).then(data => {
            if (data.success && data.fan_activated) {
                const id = data.fridge_id;
                const toggle = document.querySelector(`.fanToggle[data-fridge="${id}"]`);
                if (toggle) { toggle.checked = true; updateFanAnimation(id, true); }
                showNotification(`Fan activated for Fridge ${id} via email reply!`, "success");
            }
        }).catch(err => console.error("Error checking email signals:", err));
    }
    setInterval(checkEmailSignals, 10000);
    setTimeout(checkEmailSignals, 2000);

    // ===================== MODAL / CHARTS =====================
    // Modal Page Navigation
    const toHistoryBtn = document.getElementById("toHistoryBtn");
    const toCurrentBtn = document.getElementById("toCurrentBtn");
    const modalPage1 = document.getElementById("modalPage1");
    const modalPage2 = document.getElementById("modalPage2");
    const fridgeModal = document.getElementById("fridgeModal");

    if (toHistoryBtn && toCurrentBtn && modalPage1 && modalPage2) {
        toHistoryBtn.addEventListener("click", () => {
            modalPage1.style.display = "none";
            modalPage2.style.display = "block";
        });

        toCurrentBtn.addEventListener("click", () => {
            modalPage2.style.display = "none";
            modalPage1.style.display = "block";
        });
    }

    const fridgeDataEl = document.getElementById("fridge-data");
    const historicalDataEl = document.getElementById("historical-data");
    let fridgeData = {}, historicalData = {};

    console.log("Raw fridge data text:", fridgeDataEl ? fridgeDataEl.textContent : null);
    console.log("Raw history data text:", historicalDataEl ? historicalDataEl.textContent : null);

    if (fridgeDataEl) {
        try {
            fridgeData = JSON.parse(fridgeDataEl.textContent);
            console.log("Fridge Data loaded:", fridgeData);
            console.log("Fridge Data type:", typeof fridgeData);
            console.log("Fridge Data keys:", Object.keys(fridgeData));
        } catch (e) {
            console.error("Error parsing fridge data:", e);
        }
    }
    if (historicalDataEl) {
        try {
            historicalData = JSON.parse(historicalDataEl.textContent);
            console.log("Historical Data loaded:", historicalData);
        } catch (e) {
            console.error("Error parsing historical data:", e);
        }
    }

    if (fridgeModal) {
        fridgeModal.addEventListener("show.bs.modal", event => {
            const button = event.relatedTarget;
            if (!button) {
                console.warn("No relatedTarget on modal event");
                return;
            }
            const fridgeId = button.getAttribute("data-fridge");
            if (!fridgeId) {
                console.warn("No data-fridge attribute found");
                return;
            }

            console.log("Opening modal for fridge:", fridgeId);
            console.log("All fridge data keys:", Object.keys(fridgeData));
            console.log("Fridge data for", fridgeId, ":", fridgeData[fridgeId]);
            console.log("Fridge data for (as number)", parseInt(fridgeId), ":", fridgeData[parseInt(fridgeId)]);
            console.log("History data:", historicalData[fridgeId]);

            fridgeModal.setAttribute("data-current-fridge", fridgeId);

            // Reset to page 1
            if (modalPage1 && modalPage2) {
                modalPage1.style.display = "block";
                modalPage2.style.display = "none";
            }

            // Convert fridgeId to number to match Python dict keys
            const data = fridgeData[parseInt(fridgeId)] || fridgeData[fridgeId];
            const history = historicalData[parseInt(fridgeId)] || historicalData[fridgeId];

            if (!data) {
                console.error("No data found for fridge", fridgeId);
                return;
            }
            if (!history) {
                console.error("No history found for fridge", fridgeId);
            }

            const thresholdLabel = fridgeModal.querySelector(".current-threshold-label");
            if (thresholdLabel) {
                const currentText = thresholdLabel.textContent.split('--')[0]; // Get translated prefix
                thresholdLabel.textContent = currentText + (data && data.threshold ? data.threshold : "N/A") + "°C";
            }

            document.getElementById("currentTempModal").textContent = data.temperature + "°C";
            document.getElementById("currentHumidityModal").textContent = data.humidity + "%";

            if (window.tempGaugeInstance) window.tempGaugeInstance.destroy();
            if (window.humidityGaugeInstance) window.humidityGaugeInstance.destroy();
            if (window.historyChartInstance) window.historyChartInstance.destroy();

            const tempCanvas = document.getElementById("tempGaugeModal");
            const ctxTemp = tempCanvas ? tempCanvas.getContext("2d") : null;
            if (ctxTemp) {
                window.tempGaugeInstance = new Chart(ctxTemp, {
                    type: "doughnut",
                    data: {
                        datasets: [{
                            data: [data.temperature || 0, Math.max(0, 50 - (data.temperature || 0))],
                            backgroundColor: ["#ff4d4d", "#555"]
                        }]
                    },
                    options: { responsive: true, cutout: "70%", plugins: { legend: { display: false } } }
                });
            }

            const humCanvas = document.getElementById("humidityGaugeModal");
            const ctxHum = humCanvas ? humCanvas.getContext("2d") : null;
            if (ctxHum) {
                window.humidityGaugeInstance = new Chart(ctxHum, {
                    type: "doughnut",
                    data: {
                        datasets: [{
                            data: [data.humidity || 0, Math.max(0, 100 - (data.humidity || 0))],
                            backgroundColor: ["#3399ff", "#555"]
                        }]
                    },
                    options: { responsive: true, cutout: "70%", plugins: { legend: { display: false } } }
                });
            }

            const histCanvas = document.getElementById("iotChartModal");
            const ctxHist = histCanvas ? histCanvas.getContext("2d") : null;
            if (ctxHist && history) {
                window.historyChartInstance = new Chart(ctxHist, {
                    type: "line",
                    data: {
                        labels: history.timestamps || [],
                        datasets: [
                            {
                                label: "Temperature (°C)",
                                data: history.temperature || [],
                                borderColor: "rgba(255,99,132,1)",
                                backgroundColor: "rgba(255,99,132,0.2)",
                                tension: 0.4,
                                fill: true,
                                yAxisID: "y1"
                            },
                            {
                                label: "Humidity (%)",
                                data: history.humidity || [],
                                borderColor: "rgba(54,162,235,1)",
                                backgroundColor: "rgba(54,162,235,0.2)",
                                tension: 0.4,
                                fill: true,
                                yAxisID: "y2"
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        interaction: { mode: "index", intersect: false },
                        stacked: false,
                        scales: {
                            y1: { type: "linear", position: "left", title: { display: true, text: "Temperature (°C)" } },
                            y2: { type: "linear", position: "right", title: { display: true, text: "Humidity (%)" }, grid: { drawOnChartArea: false } },
                            x: { title: { display: true, text: "Time" } }
                        },
                        plugins: { legend: { labels: { color: "#fff" } } }
                    }
                });
            }
        });
    }

    // ===================== REAL-TIME FRIDGE DATA =====================
    document.addEventListener("DOMContentLoaded", () => {
        const modal = fridgeModal;
        async function refreshFridgeData() {
            try {
                const res = await fetch("/dashboard/api/latest");
                const result = await res.json();
                if (result.success && result.data) {
                    for (const fridgeId in result.data) {
                        const entry = result.data[fridgeId];
                        if (!entry || entry.temperature == null || entry.humidity == null) continue;

                        const tempEl = document.querySelector(`#fridgeCard${fridgeId} .temperature`);
                        const humEl = document.querySelector(`#fridgeCard${fridgeId} .humidity`);
                        if (tempEl) tempEl.textContent = entry.temperature + '°C';
                        if (humEl) humEl.textContent = entry.humidity + '%';

                        // Update fan toggle state from server
                        const fanToggle = document.querySelector(`.fanToggle[data-fridge="${fridgeId}"]`);
                        if (fanToggle && !fanToggle.disabled && !fanTogglesInProgress.has(parseInt(fridgeId))) {
                            const serverState = entry.fan_on || false;
                            if (fanToggle.checked !== serverState) {
                                console.log(`Syncing fan ${fridgeId} toggle from server: ${serverState}`);
                                fanToggle.checked = serverState;
                                updateFanAnimation(fridgeId, serverState);
                            }
                        }

                        const isOpen = modal.classList.contains('show');
                        const currentFridge = modal.getAttribute('data-current-fridge');
                        if (isOpen && currentFridge == fridgeId) {
                            document.getElementById('currentTempModal').textContent = entry.temperature + '°C';
                            document.getElementById('currentHumidityModal').textContent = entry.humidity + '%';
                            if (window.tempGaugeInstance && window.humidityGaugeInstance) {
                                window.tempGaugeInstance.data.datasets[0].data = [entry.temperature, 50 - entry.temperature];
                                window.humidityGaugeInstance.data.datasets[0].data = [entry.humidity, 100 - entry.humidity];
                                window.tempGaugeInstance.update(); window.humidityGaugeInstance.update();
                            }
                        }
                    }
                }
            } catch (err) { console.error("Error refreshing fridge data:", err); }
        }
        setInterval(refreshFridgeData, 3000);
        refreshFridgeData();
    });

} // End of dashboardInitialized guard
