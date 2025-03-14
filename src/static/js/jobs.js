document.addEventListener("DOMContentLoaded", function () {
  // console.log(window.location.href.split("?")[1]);
  const queryParams = window.location.href.split("?")[1];
  if (queryParams) {
    const daysAgo = queryParams.split("=")[1];
    if (daysAgo) {
      document.getElementById("days-ago-input").value = daysAgo;
    }
  }

  // Current job being processed
  let currentJobId = null;
  let currentExternalId = null;

  // Add event listeners for downrate buttons
  document.querySelectorAll(".downrate-job-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const jobId = this.getAttribute("data-job-id");
      downrateJob(jobId);
    });
  });

  // Add event listeners for delete buttons
  document.querySelectorAll(".delete-job-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const jobId = this.getAttribute("data-job-id");
      deleteJob(jobId);
    });
  });

  // Add event listeners for mark applied buttons
  document.querySelectorAll(".mark-applied-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const jobId = this.getAttribute("data-job-id");
      markAsApplied(jobId);
    });
  });

  // Expose the viewOnLinkedIn function globally
  window.viewOnLinkedIn = function (jobId, externalId) {
    // First open LinkedIn in a new tab
    window.open(`https://www.linkedin.com/jobs/view/${externalId}`, "_blank");
  };

  // Function to mark a job as applied
  window.markAsApplied = function (jobId) {
    // Get the job element
    const jobElement = document.getElementById(`job-${jobId}`);

    // Add the applied class to the job element
    if (jobElement) {
      jobElement.classList.add("applied");
    }

    // Send the request to mark the job as applied
    fetch(`/mark_applied/${jobId}`, {
      method: "POST",
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          console.log(
            `${new Date().toLocaleString()} - Job ${jobId} marked as applied`,
          );
        } else {
          console.error(
            `${new Date().toLocaleString()} - Error marking job ${jobId} as applied:`,
            data.error,
          );
        }
      })
      .catch((error) => {
        console.error(
          `${new Date().toLocaleString()} - Error marking job ${jobId} as applied:`,
          error,
        );
      });
  };

  // Function to downrate a job
  window.downrateJob = function (jobId) {
    // Get the job element
    const jobElement = document.getElementById(`job-${jobId}`);

    // Add the downrated class to the job element
    if (jobElement) {
      jobElement.classList.add("downrated");
    }

    // Send the request to mark the job as downrated
    fetch(`/downrate_job/${jobId}`, {
      method: "POST",
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          console.log(
            `${new Date().toLocaleString()} - Job ${jobId} marked as downrated`,
          );
        } else {
          console.error(
            `${new Date().toLocaleString()} - Error marking job ${jobId} as downrated:`,
            data.error,
          );
        }
      })
      .catch((error) => {
        console.error(
          `${new Date().toLocaleString()} - Error marking job ${jobId} as downrated:`,
          error,
        );
      });
  };

  // Function to delete a job
  window.deleteJob = function (jobId) {
    // Get the job element
    const jobElement = document.getElementById(`job-${jobId}`);

    // Add the downrated class to the job element
    if (jobElement) {
      jobElement.classList.add("deleted");
    }

    // Send the request to mark the job as downrated
    fetch(`/delete_job/${jobId}`, {
      method: "POST",
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          console.log(`${new Date().toLocaleString()} - Job ${jobId} deleted`);
        } else {
          console.error(
            `${new Date().toLocaleString()} - Error deleting job ${jobId}:`,
            data.error,
          );
        }
      })
      .catch((error) => {
        console.error(
          `${new Date().toLocaleString()} - Error deleting job ${jobId}:`,
          error,
        );
      });
  };
});
