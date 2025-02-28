document.addEventListener("DOMContentLoaded", () => {
  // Get DOM elements
  const startScrapeBtn = document.getElementById("start-scrape-btn");
  const stopScrapeBtn = document.getElementById("stop-scrape-btn");
  const stopAnalysisBtn = document.getElementById("stop-analysis-btn");
  const timePeriodSelect = document.getElementById("time-period");
  const locationSelect = document.getElementById("location");
  const keywordsInput = document.getElementById("keywords");
  const statusContainer = document.getElementById("status-container");
  const isRunningStatus = document.getElementById("is-running-status");
  const scrapeCompleteStatus = document.getElementById(
    "scrape-complete-status",
  );
  const analysisCompleteStatus = document.getElementById(
    "analysis-complete-status",
  );
  const jobsScrapedCount = document.getElementById("jobs-scraped-count");
  const jobsAnalyzedCount = document.getElementById("jobs-analyzed-count");
  const jobsScrapedProgress = document.getElementById("jobs-scraped-progress");
  const jobsAnalyzedProgress = document.getElementById(
    "jobs-analyzed-progress",
  );
  const jobsScrapedBar = document.getElementById("jobs-scraped-bar");
  const jobsAnalyzedBar = document.getElementById("jobs-analyzed-bar");
  const errorContainer = document.getElementById("error-container");
  const errorMessage = document.getElementById("error-message");

  // Create suggestions container
  const suggestionsContainer = document.createElement("div");
  suggestionsContainer.id = "keywords-suggestions";
  suggestionsContainer.className = "suggestions-container hidden";
  keywordsInput.parentNode.appendChild(suggestionsContainer);

  // Status polling interval (in milliseconds)
  const POLLING_INTERVAL = 2000;
  let pollingTimer = null;

  // Store previous values to detect changes
  let prevScrapedCount = 0;
  let prevAnalyzedCount = 0;

  // Store total expected counts
  let totalJobsToScrape = 0;
  let totalJobsToAnalyze = 0;

  // Track current phase
  let isScrapingPhase = false;
  let isAnalysisPhase = false;

  // Load previously used keywords from localStorage
  function loadPreviousKeywords() {
    const currentTime = new Date().toLocaleString();
    try {
      const savedKeywords = localStorage.getItem("previousKeywords");
      if (savedKeywords) {
        return JSON.parse(savedKeywords);
      }
    } catch (error) {
      console.error(
        `${currentTime} - Error loading previous keywords: ${error.message}`,
      );
    }
    return [];
  }

  // Save keyword to localStorage
  function saveKeyword(keyword) {
    const currentTime = new Date().toLocaleString();
    try {
      if (!keyword.trim()) return;

      let previousKeywords = loadPreviousKeywords();

      // Remove the keyword if it already exists (to avoid duplicates)
      previousKeywords = previousKeywords.filter(
        (k) => k.toLowerCase() !== keyword.toLowerCase(),
      );

      // Add the new keyword at the beginning
      previousKeywords.unshift(keyword);

      // Keep only the last 10 keywords
      if (previousKeywords.length > 10) {
        previousKeywords = previousKeywords.slice(0, 10);
      }

      localStorage.setItem(
        "previousKeywords",
        JSON.stringify(previousKeywords),
      );
      console.log(`${currentTime} - Saved keyword to localStorage: ${keyword}`);
    } catch (error) {
      console.error(`${currentTime} - Error saving keyword: ${error.message}`);
    }
  }

  // Display keyword suggestions
  function showSuggestions() {
    const currentTime = new Date().toLocaleString();
    try {
      const previousKeywords = loadPreviousKeywords();

      if (previousKeywords.length === 0) {
        suggestionsContainer.classList.add("hidden");
        return;
      }

      suggestionsContainer.innerHTML = "";

      previousKeywords.forEach((keyword) => {
        const suggestion = document.createElement("div");
        suggestion.className = "suggestion-item";
        suggestion.textContent = keyword;
        suggestion.addEventListener("click", () => {
          keywordsInput.value = keyword;
          suggestionsContainer.classList.add("hidden");
        });
        suggestionsContainer.appendChild(suggestion);
      });

      suggestionsContainer.classList.remove("hidden");
    } catch (error) {
      console.error(
        `${currentTime} - Error showing suggestions: ${error.message}`,
      );
      suggestionsContainer.classList.add("hidden");
    }
  }

  // Hide suggestions when clicking outside
  document.addEventListener("click", (event) => {
    if (
      event.target !== keywordsInput &&
      event.target !== suggestionsContainer
    ) {
      suggestionsContainer.classList.add("hidden");
    }
  });

  // Show suggestions when the keywords input is focused
  keywordsInput.addEventListener("focus", showSuggestions);

  // Filter suggestions based on input
  keywordsInput.addEventListener("input", () => {
    const currentTime = new Date().toLocaleString();
    try {
      const inputValue = keywordsInput.value.toLowerCase();
      const previousKeywords = loadPreviousKeywords();

      if (previousKeywords.length === 0) {
        suggestionsContainer.classList.add("hidden");
        return;
      }

      suggestionsContainer.innerHTML = "";

      const filteredKeywords = previousKeywords.filter((keyword) =>
        keyword.toLowerCase().includes(inputValue),
      );

      if (filteredKeywords.length === 0) {
        suggestionsContainer.classList.add("hidden");
        return;
      }

      filteredKeywords.forEach((keyword) => {
        const suggestion = document.createElement("div");
        suggestion.className = "suggestion-item";
        suggestion.textContent = keyword;
        suggestion.addEventListener("click", () => {
          keywordsInput.value = keyword;
          suggestionsContainer.classList.add("hidden");
        });
        suggestionsContainer.appendChild(suggestion);
      });

      suggestionsContainer.classList.remove("hidden");
    } catch (error) {
      console.error(
        `${currentTime} - Error filtering suggestions: ${error.message}`,
      );
    }
  });

  // Event listener for the start scrape button
  startScrapeBtn.addEventListener("click", async () => {
    const currentTime = new Date().toLocaleString();
    console.log(`${currentTime} - Starting scrape process...`);

    // Get form values
    const timePeriod = timePeriodSelect.value;
    const location = locationSelect.value;
    const keywords = keywordsInput.value.trim();

    // Validate input
    if (!keywords) {
      const currentTime = new Date().toLocaleString();
      console.warn(`${currentTime} - Keywords field is empty`);
      alert("Please enter at least one keyword");
      return;
    }

    // Save the keywords to localStorage
    saveKeyword(keywords);

    // Reset previous counts and progress
    prevScrapedCount = 0;
    prevAnalyzedCount = 0;
    totalJobsToScrape = 0;
    totalJobsToAnalyze = 0;
    isScrapingPhase = true;
    isAnalysisPhase = false;

    // Reset counter displays
    jobsScrapedCount.textContent = "0";
    jobsAnalyzedCount.textContent = "0";
    jobsScrapedProgress.textContent = "0/0";
    jobsAnalyzedProgress.textContent = "0/0";
    jobsScrapedBar.style.width = "0%";
    jobsAnalyzedBar.style.width = "0%";

    // Disable button during scraping
    startScrapeBtn.disabled = true;
    startScrapeBtn.textContent = "Scraping...";

    // Show stop scrape button, hide stop analysis button
    stopScrapeBtn.classList.remove("hidden");
    stopAnalysisBtn.classList.add("hidden");

    try {
      // Send request to start scraping
      const response = await fetch("/api/start_scrape", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          time_period: timePeriod,
          location: location,
          keywords: keywords,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      // Show status container
      statusContainer.classList.remove("hidden");

      // Start polling for status updates
      startStatusPolling();
    } catch (error) {
      const currentTime = new Date().toLocaleString();
      console.error(`${currentTime} - Error starting scrape: ${error.message}`);

      // Show error
      errorContainer.classList.remove("hidden");
      errorMessage.textContent = error.message;

      // Reset button
      startScrapeBtn.disabled = false;
      startScrapeBtn.textContent = "Start Scraping";
      stopScrapeBtn.classList.add("hidden");
    }
  });

  // Event listener for the stop scrape button
  stopScrapeBtn.addEventListener("click", async () => {
    const currentTime = new Date().toLocaleString();
    console.log(`${currentTime} - User clicked stop scraping button`);

    try {
      // Send request to stop scraping
      const response = await fetch("/api/stop_scrape", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      // Disable the stop button to prevent multiple clicks
      stopScrapeBtn.disabled = true;
      stopScrapeBtn.textContent = "Stopping...";
    } catch (error) {
      const currentTime = new Date().toLocaleString();
      console.error(`${currentTime} - Error stopping scrape: ${error.message}`);
    }
  });

  // Event listener for the stop analysis button
  stopAnalysisBtn.addEventListener("click", async () => {
    const currentTime = new Date().toLocaleString();
    console.log(`${currentTime} - User clicked stop analysis button`);

    try {
      // Send request to stop analysis
      const response = await fetch("/api/stop_analysis", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      // Disable the stop button to prevent multiple clicks
      stopAnalysisBtn.disabled = true;
      stopAnalysisBtn.textContent = "Stopping...";
    } catch (error) {
      const currentTime = new Date().toLocaleString();
      console.error(
        `${currentTime} - Error stopping analysis: ${error.message}`,
      );
    }
  });

  // Function to start polling for status updates
  function startStatusPolling() {
    // Clear any existing polling
    if (pollingTimer) {
      clearInterval(pollingTimer);
    }

    // Update status immediately
    updateStatus();

    // Set up polling interval
    pollingTimer = setInterval(updateStatus, POLLING_INTERVAL);
  }

  // Function to animate counter when value changes
  function animateCounter(element, newValue) {
    // Add animation class
    element.classList.add("counter-updated");

    // Update the text
    element.textContent = newValue;

    // Remove animation class after animation completes
    setTimeout(() => {
      element.classList.remove("counter-updated");
    }, 500);
  }

  // Function to update progress bar
  function updateProgressBar(current, total, progressElement, barElement) {
    if (total > 0) {
      const percentage = Math.min(Math.round((current / total) * 100), 100);
      progressElement.textContent = `${current}/${total}`;
      barElement.style.width = `${percentage}%`;
    } else {
      progressElement.textContent = `${current}/0`;
      barElement.style.width = "0%";
    }
  }

  // Function to update status display
  async function updateStatus() {
    try {
      const response = await fetch("/api/scrape_status");

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const status = await response.json();

      // Update status indicators
      isRunningStatus.textContent = status.is_running ? "Yes" : "No";
      isRunningStatus.className = status.is_running
        ? "status-running"
        : "status-no";

      scrapeCompleteStatus.textContent = status.scrape_complete ? "Yes" : "No";
      scrapeCompleteStatus.className = status.scrape_complete
        ? "status-yes"
        : "status-no";

      analysisCompleteStatus.textContent = status.analysis_complete
        ? "Yes"
        : "No";
      analysisCompleteStatus.className = status.analysis_complete
        ? "status-yes"
        : "status-no";

      // Update job counts with animation if they've changed
      const currentScrapedCount = status.jobs_scraped || 0;
      const currentAnalyzedCount = status.jobs_analyzed || 0;

      // Update total jobs to scrape if available
      if (status.total_jobs_to_scrape && status.total_jobs_to_scrape > 0) {
        totalJobsToScrape = status.total_jobs_to_scrape;
      }

      // Update total jobs to analyze if available
      if (status.total_jobs_to_analyze && status.total_jobs_to_analyze > 0) {
        totalJobsToAnalyze = status.total_jobs_to_analyze;
      }

      // Update progress bars
      updateProgressBar(
        currentScrapedCount,
        totalJobsToScrape,
        jobsScrapedProgress,
        jobsScrapedBar,
      );
      updateProgressBar(
        currentAnalyzedCount,
        totalJobsToAnalyze,
        jobsAnalyzedProgress,
        jobsAnalyzedBar,
      );

      if (currentScrapedCount !== prevScrapedCount) {
        animateCounter(jobsScrapedCount, currentScrapedCount);
        prevScrapedCount = currentScrapedCount;
      }

      if (currentAnalyzedCount !== prevAnalyzedCount) {
        animateCounter(jobsAnalyzedCount, currentAnalyzedCount);
        prevAnalyzedCount = currentAnalyzedCount;
      }

      // Check if we've transitioned from scraping to analysis phase
      if (isScrapingPhase && status.scrape_complete) {
        isScrapingPhase = false;
        isAnalysisPhase = true;

        // Hide stop scrape button, show stop analysis button
        stopScrapeBtn.classList.add("hidden");
        stopAnalysisBtn.classList.remove("hidden");

        const currentTime = new Date().toLocaleString();
        console.log(
          `${currentTime} - Scraping phase complete, starting analysis phase`,
        );
      }

      // Handle error if present
      if (status.error) {
        const currentTime = new Date().toLocaleString();
        console.error(`${currentTime} - Scraping error: ${status.error}`);
        errorContainer.classList.remove("hidden");
        errorMessage.textContent = status.error;
      } else {
        errorContainer.classList.add("hidden");
      }

      // If scraping is no longer running, stop polling and reset button
      if (!status.is_running) {
        clearInterval(pollingTimer);
        startScrapeBtn.disabled = false;
        startScrapeBtn.textContent = "Start Scraping";
        stopScrapeBtn.classList.add("hidden");
        stopAnalysisBtn.classList.add("hidden");
        isScrapingPhase = false;
        isAnalysisPhase = false;

        const currentTime = new Date().toLocaleString();
        if (status.analysis_complete) {
          console.log(
            `${currentTime} - Scraping and analysis completed successfully. Found ${status.jobs_scraped} jobs, analyzed ${status.jobs_analyzed} jobs.`,
          );
        } else if (status.error) {
          console.error(`${currentTime} - Scraping process failed`);
        }
      }
    } catch (error) {
      const currentTime = new Date().toLocaleString();
      console.error(`${currentTime} - Error fetching status: ${error.message}`);

      // Stop polling on error
      clearInterval(pollingTimer);

      // Reset button
      startScrapeBtn.disabled = false;
      startScrapeBtn.textContent = "Start Scraping";
      stopScrapeBtn.classList.add("hidden");
      stopAnalysisBtn.classList.add("hidden");

      // Show error
      errorContainer.classList.remove("hidden");
      errorMessage.textContent = `Failed to get status updates: ${error.message}`;
    }
  }
});
