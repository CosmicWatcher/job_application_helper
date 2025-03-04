document.addEventListener("DOMContentLoaded", function () {
  // Get the application dialog element
  const applicationDialog = document.getElementById("application-dialog");
  const yesButton = document.getElementById("applied-yes-btn");

  // Current job being processed
  let currentJobId = null;
  let currentExternalId = null;

  // Initialize event listeners for the dialog buttons
  if (yesButton) {
    yesButton.addEventListener("click", function () {
      // Mark the job as applied
      markAsApplied(currentJobId);
      // Close the dialog
      applicationDialog.style.display = "none";
    });
  }

  // Add event listeners for reject buttons
  document.querySelectorAll(".reject-job-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const jobId = this.getAttribute("data-job-id");
      rejectJob(jobId);
    });
  });

  // Add event listeners for mark applied buttons
  document.querySelectorAll(".mark-applied-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const jobId = this.getAttribute("data-job-id");
      markAsApplied(jobId);
    });
  });

  // close the did you apply dialog
  window.addEventListener("click", function (event) {
    if (event.target === applicationDialog) {
      applicationDialog.style.display = "none";
    }
  });

  // Expose the viewOnLinkedIn function globally
  window.viewOnLinkedIn = function (jobId, externalId) {
    // Store the current job info
    currentJobId = jobId;
    currentExternalId = externalId;

    // First open LinkedIn in a new tab
    const linkedInWindow = window.open(
      `https://www.linkedin.com/jobs/view/${externalId}`,
      "_blank",
    );

    // Then show the application dialog after a short delay
    // This ensures the browser doesn't block the popup and the tab opens first
    setTimeout(function () {
      applicationDialog.style.display = "block";
      // Focus back on our window so the user sees the dialog
      window.focus();
    }, 500);

    // Prevent the default link behavior
    return false;
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

  // Function to reject a job
  window.rejectJob = function (jobId) {
    // Get the job element
    const jobElement = document.getElementById(`job-${jobId}`);

    // Add the rejected class to the job element
    if (jobElement) {
      jobElement.classList.add("rejected");
    }

    // Send the request to mark the job as rejected
    fetch(`/reject_job/${jobId}`, {
      method: "POST",
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          console.log(
            `${new Date().toLocaleString()} - Job ${jobId} marked as rejected`,
          );
        } else {
          console.error(
            `${new Date().toLocaleString()} - Error marking job ${jobId} as rejected:`,
            data.error,
          );
        }
      })
      .catch((error) => {
        console.error(
          `${new Date().toLocaleString()} - Error marking job ${jobId} as rejected:`,
          error,
        );
      });
  };
});
