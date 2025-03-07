document.addEventListener("DOMContentLoaded", () => {
  fetchProfileStats();
});

async function fetchProfileStats() {
  try {
    const currentTime = new Date().toLocaleString();
    console.log(`[${currentTime}] Fetching profile statistics...`);

    const response = await fetch("/api/profile/stats");
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    renderProfileStats(data);
  } catch (error) {
    const currentTime = new Date().toLocaleString();
    console.error(`[${currentTime}] Error fetching profile stats:`, error);

    document.querySelectorAll(".loading").forEach((el) => {
      el.textContent = "Failed to load data";
      el.classList.add("error");
    });
  }
}

function renderProfileStats(data) {
  // Render summary stats
  document.querySelector("#total-applications .stat-value").textContent =
    data.total_applications;
  document.querySelector("#application-rate .stat-value").textContent =
    data.application_rate;

  // Render company stats
  renderCompanyStats(data.companies);

  // Render daily application stats
  renderDailyStats(data.daily_applications);

  // Render recent applications
  renderRecentApplications(data.recent_applications);
}

function renderCompanyStats(companies) {
  // Clear loading message
  document.querySelector("#company-chart").innerHTML = "";
  document.querySelector("#company-list").innerHTML = "";

  if (companies.length === 0) {
    document.querySelector("#company-chart").innerHTML =
      "<p>No application data available</p>";
    return;
  }

  // Create company list
  const companyList = document.querySelector("#company-list");
  companies.forEach((company) => {
    const item = document.createElement("div");
    item.className = "stat-item";
    item.innerHTML = `
            <span class="company-name">${company.name}</span>
            <span class="company-count">${company.count}</span>
        `;
    companyList.appendChild(item);
  });

  // Create company chart (top 10)
  const topCompanies = companies.slice(0, 10);
  const canvas = document.createElement("canvas");
  document.querySelector("#company-chart").appendChild(canvas);

  new Chart(canvas, {
    type: "bar",
    data: {
      labels: topCompanies.map((c) => c.name),
      datasets: [
        {
          label: "Applications",
          data: topCompanies.map((c) => c.count),
          backgroundColor: "rgba(54, 162, 235, 0.7)",
          borderColor: "rgba(54, 162, 235, 1)",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1,
          },
        },
      },
    },
  });
}

function renderDailyStats(dailyData) {
  // Clear loading message
  document.querySelector("#daily-chart").innerHTML = "";
  document.querySelector("#daily-list").innerHTML = "";

  if (dailyData.length === 0) {
    document.querySelector("#daily-chart").innerHTML =
      "<p>No application data available</p>";
    return;
  }

  // Create daily list
  const dailyList = document.querySelector("#daily-list");
  dailyData.forEach((day) => {
    const item = document.createElement("div");
    item.className = "stat-item";

    // Format date to be more readable
    const formattedDate = new Date(day.date).toLocaleDateString();

    item.innerHTML = `
            <span class="day-date">${formattedDate}</span>
            <span class="day-count">${day.count}</span>
        `;
    dailyList.appendChild(item);
  });

  // Create daily chart (last 14 days)
  const recentDays = dailyData.slice(0, 14).reverse();
  const canvas = document.createElement("canvas");
  document.querySelector("#daily-chart").appendChild(canvas);

  new Chart(canvas, {
    type: "line",
    data: {
      labels: recentDays.map((d) => new Date(d.date).toLocaleDateString()),
      datasets: [
        {
          label: "Applications",
          data: recentDays.map((d) => d.count),
          backgroundColor: "rgba(75, 192, 192, 0.2)",
          borderColor: "rgba(75, 192, 192, 1)",
          borderWidth: 2,
          tension: 0.1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1,
          },
        },
      },
    },
  });
}

function renderRecentApplications(applications) {
  const container = document.querySelector("#recent-applications");
  container.innerHTML = "";

  if (applications.length === 0) {
    container.innerHTML = "<p>No recent applications</p>";
    return;
  }

  applications.forEach((job) => {
    const item = document.createElement("div");
    item.className = "application-item";

    // Format date to be more readable
    const formattedDate = job.time_applied
      ? new Date(job.time_applied).toLocaleString()
      : "Unknown";

    item.innerHTML = `
            <div class="application-header">
                <h3 class="job-title">${job.title}</h3>
                <span class="application-date">${formattedDate}</span>
            </div>
            <div class="company-name">${job.company}</div>
        `;
    container.appendChild(item);
  });
}
