// ===================== DATE & TIME DISPLAY =====================
function updateDateTime() {
  const now = new Date();

  // Date formatting
  const day = now.getDate();
  const daySuffix = (d) => {
    if (d > 3 && d < 21) return "th";
    switch (d % 10) {
      case 1:
        return "st";
      case 2:
        return "nd";
      case 3:
        return "rd";
      default:
        return "th";
    }
  };
  const options = { year: "numeric", month: "long", day: "numeric" };
  const formattedDate = now
    .toLocaleDateString("en-US", options)
    .replace(/\d+/, day + daySuffix(day));
  const dateEl = document.getElementById("date");
  if (dateEl) dateEl.textContent = formattedDate;

  // Time formatting
  const hours = now.getHours().toString().padStart(2, "0");
  const minutes = now.getMinutes().toString().padStart(2, "0");
  const clockEl = document.getElementById("clock");
  if (clockEl) clockEl.textContent = `${hours}:${minutes}`;
}
setInterval(updateDateTime, 1000);
updateDateTime();

// ===================== ALERT AUTO-DISMISS =====================
setTimeout(() => {
  document.querySelectorAll(".alert").forEach((alert) => {
    alert.classList.add("hide-slide");
    alert.addEventListener("transitionend", () => alert.remove(), {
      once: true,
    });
  });
}, 3000);

// ===================== CUSTOMER TABLE ANIMATION =====================
document.querySelectorAll(".Customer").forEach((row, index) => {
  setTimeout(() => row.classList.add("visible"), index * 150);
});

// ===================== FRIDGE CARD ANIMATION =====================
document.querySelectorAll(".fridge-card").forEach((card, index) => {
  setTimeout(() => card.classList.add("visible"), index * 150);
});

// ===================== EMAIL TEST CARD ANIMATION =====================
document.querySelectorAll(".email-card").forEach((card, index) => {
  setTimeout(() => card.classList.add("visible"), index * 150);
});

// ===================== MODAL NAVIGATION (CURRENT / HISTORY) =====================
const toHistoryBtn = document.getElementById("toHistoryBtn");
const toCurrentBtn = document.getElementById("toCurrentBtn");
const modalPage1 = document.getElementById("modalPage1");
const modalPage2 = document.getElementById("modalPage2");

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

// ===================== DELETE MODAL =====================
const deleteModal = document.getElementById("deleteModal");
const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
if (deleteModal && confirmDeleteBtn) {
  deleteModal.addEventListener("show.bs.modal", (event) => {
    const button = event.relatedTarget;
    const deleteUrl = button.getAttribute("data-delete-url");
    confirmDeleteBtn.setAttribute("href", deleteUrl);
  });
}

// ===================== VIEW & EDIT CLIENT MODALS =====================
const viewClientModal = document.getElementById("viewClientModal");
const editClientModal = document.getElementById("editClientModal");
const editClientForm = document.getElementById("editClientForm");
const editFromViewBtn = document.getElementById("editFromViewBtn");

if (viewClientModal) {
  viewClientModal.addEventListener("show.bs.modal", (event) => {
    const row = event.relatedTarget;
    const customerId = row.getAttribute("data-id");
    const firstName = row.getAttribute("data-firstname");
    const lastName = row.getAttribute("data-lastname");
    const email = row.getAttribute("data-email");
    const phone_num = row.getAttribute("data-phone");
    const dob = row.getAttribute("data-dob");
    const dateStr = row.getAttribute("data-date");

    // Fill View Modal
    document.getElementById("modalFirstName").textContent = firstName;
    document.getElementById("modalLastName").textContent = lastName;
    document.getElementById("modalEmail").textContent = email;
    document.getElementById("modalPhone").textContent = phone_num || "N/A";
    document.getElementById("modalDob").textContent = dob || "N/A";
    document.getElementById("modalDate").textContent = dateStr
      ? new Date(dateStr).toLocaleDateString("en-US", {
          year: "numeric",
          month: "long",
          day: "numeric",
        })
      : "N/A";

    // Set hidden ID for Edit modal
    document.getElementById("editCustomerId").value = customerId;
  });
}

if (editFromViewBtn && editClientForm) {
  editFromViewBtn.addEventListener("click", () => {
    const customerId = document.getElementById("editCustomerId").value;
    editClientForm.action = `/update/${customerId}`;

    document.getElementById("editFirstName").value =
      document.getElementById("modalFirstName").textContent;
    document.getElementById("editLastName").value =
      document.getElementById("modalLastName").textContent;
    document.getElementById("editEmail").value =
      document.getElementById("modalEmail").textContent;
  });
}

const editCancelBtn = document.getElementById("editBackButton");
if (editCancelBtn) {
  editCancelBtn.addEventListener("click", () => {
    const editModalInstance = bootstrap.Modal.getInstance(editClientModal);
    editModalInstance.hide();

    const viewModalInstance = new bootstrap.Modal(viewClientModal);
    viewModalInstance.show();
  });
}

// ===================== FRIDGE & HISTORICAL DATA =====================
const fridgeDataEl = document.getElementById("fridge-data");
const historicalDataEl = document.getElementById("historical-data");
let fridgeData = {},
  historicalData = {};

if (fridgeDataEl) fridgeData = JSON.parse(fridgeDataEl.textContent);
if (historicalDataEl) historicalData = JSON.parse(historicalDataEl.textContent);

const fridgeModal = document.getElementById("fridgeModal");
if (fridgeModal) {
  fridgeModal.addEventListener("show.bs.modal", (event) => {
    const button = event.relatedTarget;
    const fridgeId = button.getAttribute("data-fridge");

    // Update threshold dynamically
    const thresholdLabel = fridgeModal.querySelector(
      ".current-threshold-label"
    );
    const threshold = fridgeData[fridgeId]?.threshold ?? "N/A";
    if (thresholdLabel) {
      thresholdLabel.textContent = "Current Threshold: " + threshold + "°C";
    }

    const data = fridgeData[fridgeId];
    const history = historicalData[fridgeId];

    // Update current readings
    document.getElementById("currentTempModal").textContent =
      data.temperature + "°C";
    document.getElementById("currentHumidityModal").textContent =
      data.humidity + "%";

    // Destroy existing charts
    if (window.tempGaugeInstance) window.tempGaugeInstance.destroy();
    if (window.humidityGaugeInstance) window.humidityGaugeInstance.destroy();
    if (window.historyChartInstance) window.historyChartInstance.destroy();

    // Temp Gauge
    const ctxTemp = document.getElementById("tempGaugeModal").getContext("2d");
    window.tempGaugeInstance = new Chart(ctxTemp, {
      type: "doughnut",
      data: {
        datasets: [
          {
            data: [data.temperature, 50 - data.temperature],
            backgroundColor: ["#ff4d4d", "#555"],
          },
        ],
      },
      options: {
        responsive: true,
        cutout: "70%",
        plugins: { legend: { display: false } },
      },
    });

    // Humidity Gauge
    const ctxHumidity = document
      .getElementById("humidityGaugeModal")
      .getContext("2d");
    window.humidityGaugeInstance = new Chart(ctxHumidity, {
      type: "doughnut",
      data: {
        datasets: [
          {
            data: [data.humidity, 100 - data.humidity],
            backgroundColor: ["#3399ff", "#555"],
          },
        ],
      },
      options: {
        responsive: true,
        cutout: "70%",
        plugins: { legend: { display: false } },
      },
    });

    // Historical Line Chart
    const ctxHistory = document
      .getElementById("iotChartModal")
      .getContext("2d");
    window.historyChartInstance = new Chart(ctxHistory, {
      type: "line",
      data: {
        labels: history.timestamps,
        datasets: [
          {
            label: "Temperature (°C)",
            data: history.temperature,
            borderColor: "rgba(255, 99, 132, 1)",
            backgroundColor: "rgba(255, 99, 132, 0.2)",
            tension: 0.4,
            fill: true,
            yAxisID: "y1",
          },
          {
            label: "Humidity (%)",
            data: history.humidity,
            borderColor: "rgba(54, 162, 235, 1)",
            backgroundColor: "rgba(54, 162, 235, 0.2)",
            tension: 0.4,
            fill: true,
            yAxisID: "y2",
          },
        ],
      },
      options: {
        responsive: true,
        interaction: { mode: "index", intersect: false },
        stacked: false,
        scales: {
          y1: {
            type: "linear",
            position: "left",
            title: { display: true, text: "Temperature (°C)" },
          },
          y2: {
            type: "linear",
            position: "right",
            title: { display: true, text: "Humidity (%)" },
            grid: { drawOnChartArea: false },
          },
          x: { title: { display: true, text: "Time" } },
        },
        plugins: { legend: { labels: { color: "#fff" } } },
      },
    });
  });
}

// ===================== FAN CONTROL SYSTEM =====================
function updateFanAnimation(fridgeId, isOn) {
  const fanIcon = document.getElementById(`fanIcon${fridgeId}`);
  if (fanIcon) {
    fanIcon.classList.toggle("fan-spinning", isOn);
    fanIcon.classList.toggle("fan-off", !isOn);
  }
}

function initializeFanToggles() {
  fetch("/fan/states")
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        document.querySelectorAll(".fanToggle").forEach((toggle) => {
          const fridgeId = parseInt(toggle.getAttribute("data-fridge"));
          toggle.checked = data.fan_states[fridgeId] || false;
          updateFanAnimation(fridgeId, data.fan_states[fridgeId] || false);
        });
      }
    });
}

initializeFanToggles();

document.querySelectorAll(".fanToggle").forEach((toggle) => {
  toggle.addEventListener("change", function () {
    const fridgeId = this.getAttribute("data-fridge");
    const isChecked = this.checked;
    this.disabled = true;

    fetch(`/fan/${fridgeId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          this.checked = data.fan_state;
          updateFanAnimation(fridgeId, data.fan_state);
        } else {
          this.checked = !isChecked;
          alert("Failed: " + data.error);
        }
      })
      .finally(() => (this.disabled = false));
  });
});

// ===================== EMAIL TEST & SIGNALS =====================
const testEmailBtn = document.getElementById("testEmailBtn");
if (testEmailBtn) {
  testEmailBtn.addEventListener("click", () => {
    testEmailBtn.disabled = true;
    testEmailBtn.textContent = "Sending...";

    fetch("/api/email/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    })
      .then((res) => res.json())
      .then((data) => {
        alert(
          data.success
            ? 'Test email sent! Reply "YES" to activate fan.'
            : "Failed: " + data.error
        );
      })
      .finally(() => {
        testEmailBtn.disabled = false;
        testEmailBtn.textContent = "Send Test Email";
      });
  });
}

function showNotification(message, type = "info") {
  const notification = document.createElement("div");
  notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
  notification.style.cssText =
    "top: 20px; right: 20px; z-index: 9999; max-width: 300px;";
  notification.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
  document.body.appendChild(notification);
  setTimeout(() => {
    notification.classList.add("hide-slide");
    setTimeout(() => notification.remove(), 500);
  }, 5000);
}

function checkEmailSignals() {
  fetch("/api/email/check-signals")
    .then((res) => res.json())
    .then((data) => {
      if (data.success && data.fan_activated) {
        const fridgeId = data.fridge_id;
        const toggle = document.querySelector(
          `.fanToggle[data-fridge="${fridgeId}"]`
        );
        if (toggle) {
          toggle.checked = true;
          updateFanAnimation(fridgeId, true);
        }
        showNotification(
          `Fan activated for Fridge ${fridgeId} via email reply!`,
          "success"
        );
      }
    });
}
setInterval(checkEmailSignals, 10000);
setTimeout(checkEmailSignals, 2000);

document.addEventListener('DOMContentLoaded', () => {

  // ----------------- Modal tracking -----------------
  const fridgeModal = document.getElementById('fridgeModal');

  fridgeModal.addEventListener('show.bs.modal', function (event) {
    const button = event.relatedTarget;
    const fridgeId = button.getAttribute('data-fridge');
    fridgeModal.setAttribute('data-current-fridge', fridgeId);
    console.log('Modal opening for fridge', fridgeId);
  });

  // ----------------- Real-time data refresh -----------------
  async function refreshFridgeData() {
    try {
      const res = await fetch('/api/latest');
      const result = await res.json();

      if (result.success && result.data) {
        for (const fridgeId in result.data) {
          const entry = result.data[fridgeId];

          if (!entry || entry.temperature == null || entry.humidity == null) continue;

          console.log(`Fridge ${fridgeId}:`, entry);

          // ---------- Update fridge cards ----------
          const tempEl = document.querySelector(`#fridgeCard${fridgeId} .temperature`);
          const humEl = document.querySelector(`#fridgeCard${fridgeId} .humidity`);
          if (tempEl) tempEl.textContent = entry.temperature + '°C';
          if (humEl) humEl.textContent = entry.humidity + '%';

          // ---------- Update modal if open ----------
          const isModalOpen = fridgeModal.classList.contains('show');
          const currentFridge = fridgeModal.getAttribute('data-current-fridge');

          if (isModalOpen && currentFridge == fridgeId) {
            document.getElementById('currentTempModal').textContent = entry.temperature + '°C';
            document.getElementById('currentHumidityModal').textContent = entry.humidity + '%';

            if (window.tempGaugeInstance && window.humidityGaugeInstance) {
              window.tempGaugeInstance.data.datasets[0].data = [entry.temperature, 50 - entry.temperature];
              window.humidityGaugeInstance.data.datasets[0].data = [entry.humidity, 100 - entry.humidity];
              window.tempGaugeInstance.update();
              window.humidityGaugeInstance.update();
            }
          }
        }
      }
    } catch (err) {
      console.error('Error refreshing fridge data:', err);
    }
  }

  // Refresh every 3 seconds
  setInterval(refreshFridgeData, 3000);
  refreshFridgeData(); 

});


document.addEventListener("shown.bs.modal", function (e) {
  const dateInput = e.target.querySelector('input[type="date"]');
  if (dateInput) dateInput.focus();
});
