document.addEventListener("DOMContentLoaded", function () {
  // Modal elements
  const modal = document.getElementById("resume-editor-modal");
  const closeModalBtn = document.querySelector(".close");
  const jobsContainer = document.getElementById("resume-jobs-container");
  const suggestionsContainer = document.getElementById("suggestions-container");
  const generateBtn = document.getElementById("generate-btn");
  const statusMessage = document.getElementById("status-message");

  // Current job being edited
  let currentJobId = null;
  let currentJobExternalId = null;
  let currentJobSuggestions = [];

  // Add event listeners to all "Edit Resume" buttons
  document.querySelectorAll(".edit-resume-btn").forEach((el) => {
    el.addEventListener("click", function () {
      const jobId = this.getAttribute("data-job-id");
      const externalId = this.getAttribute("data-external-id");
      const jobElement = document.getElementById(`job-${jobId}`);
      const suggestions =
        jobElement.querySelector(".job-suggestions p").textContent;

      openResumeEditor(jobId, externalId, suggestions);
    });
  });

  // Function to open the resume editor for a specific job
  function openResumeEditor(jobId, externalId, suggestions) {
    currentJobId = jobId;
    currentJobExternalId = externalId;

    // Parse suggestions by splitting on \item
    // This regex looks for \item and captures everything until the next \item or end of string
    const itemRegex = /\\item\s+(.*?)(?=\\item|$)/gs;
    let match;
    currentJobSuggestions = [];

    // If suggestions start with \item, process with regex
    if (suggestions.trim().includes("\\item")) {
      while ((match = itemRegex.exec(suggestions)) !== null) {
        if (match[1] && match[1].trim().length > 0) {
          currentJobSuggestions.push({
            display: match[1].trim(), // Display text without \item
            value: `\\item ${match[1].trim()}`, // Ensure it has \item for LaTeX
          });
        }
      }
    } else {
      // Fallback to period splitting if no \item is found
      currentJobSuggestions = suggestions
        .split(/\s*\.\s*/)
        .filter((s) => s.trim().length > 0)
        .map((s) => {
          const trimmed = s.trim();
          return {
            display: trimmed,
            value: `\\item ${trimmed}`,
          };
        });
    }

    modal.style.display = "block";

    // Show loading message
    jobsContainer.innerHTML =
      '<div class="loading">Loading resume data...</div>';
    suggestionsContainer.innerHTML =
      '<h2>Suggestions</h2><div class="loading">Loading suggestions...</div>';

    // Fetch resume data
    fetch("/get_resume_data")
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // Clear loading message
          jobsContainer.innerHTML = "";

          // Calculate optimal layout based on number of jobs
          const jobs = data.jobs;
          const jobCount = Object.keys(jobs).length;

          // Add a class to the job container based on job count for CSS styling
          if (jobCount <= 3) {
            jobsContainer.className =
              "job-sections-container job-section-count-" + jobCount;
          } else if (jobCount <= 6) {
            jobsContainer.className =
              "job-sections-container job-section-count-" + jobCount;
          } else {
            jobsContainer.className =
              "job-sections-container job-section-count-many";
          }

          // Populate job sections
          jobs.forEach((job) => {
            Object.entries(job).forEach(([jobTitle, items]) => {
              const jobSection = document.createElement("div");
              jobSection.className = "job-section";
              jobSection.setAttribute("data-job-title", jobTitle);

              const jobTitleDiv = document.createElement("div");
              jobTitleDiv.className = "job-title";
              jobTitleDiv.textContent = jobTitle;
              jobSection.appendChild(jobTitleDiv);

              const itemList = document.createElement("ul");
              itemList.className = "item-list";
              itemList.setAttribute("data-job-title", jobTitle);

              // Make the list a drop target
              itemList.addEventListener("dragover", handleDragOver);
              itemList.addEventListener("drop", handleDrop);
              itemList.addEventListener("dragenter", function () {
                this.classList.add("drag-over");
              });
              itemList.addEventListener("dragleave", function () {
                this.classList.remove("drag-over");
              });

              items.forEach((item, index) => {
                const listItem = createItemElement(jobTitle, item, index);
                itemList.appendChild(listItem);
              });

              jobSection.appendChild(itemList);
              jobsContainer.appendChild(jobSection);
            });
          });

          // Populate suggestions
          populateSuggestions();
        } else {
          jobsContainer.innerHTML = `<div class="error">Error loading resume data: ${data.error}</div>`;
          console.error(`${new Date().toLocaleString()} - Error:`, data.error);
        }
      })
      .catch((error) => {
        jobsContainer.innerHTML = `<div class="error">Error loading resume data: ${error.message}</div>`;
        console.error(`${new Date().toLocaleString()} - Error:`, error);
      });
  }

  // Function to populate suggestions
  function populateSuggestions() {
    suggestionsContainer.innerHTML = "<h1>Suggestions</h1>";

    if (currentJobSuggestions.length === 0) {
      suggestionsContainer.innerHTML +=
        "<p>No suggestions available for this job.</p>";
      return;
    }

    const suggestionsList = document.createElement("div");
    suggestionsList.className = "suggestions-list";

    currentJobSuggestions.forEach((suggestion, index) => {
      if (!suggestion.display || suggestion.display.trim().length === 0) return;

      const suggestionItem = document.createElement("div");
      suggestionItem.className = "suggestion-item";
      suggestionItem.textContent = suggestion.display; // Display text without \item
      suggestionItem.setAttribute("draggable", "true");
      suggestionItem.setAttribute("data-suggestion-index", index);
      // Store the full value with \item as a data attribute
      suggestionItem.setAttribute("data-full-value", suggestion.value);

      // Add drag event listeners
      suggestionItem.addEventListener("dragstart", handleDragStart);
      suggestionItem.addEventListener("dragend", handleDragEnd);

      suggestionsList.appendChild(suggestionItem);
    });

    suggestionsContainer.appendChild(suggestionsList);
  }

  // Function to create an item element
  function createItemElement(jobTitle, item, index) {
    const listItem = document.createElement("li");
    listItem.className = "item";
    listItem.setAttribute("draggable", "true");

    // Remove \item prefix for display but keep it in the value
    const displayText = item.replace(/^\\item\s+/, "");
    const fullValue = item.startsWith("\\item") ? item : `\\item ${item}`;

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.name = "selected_items[]";
    checkbox.value = `${jobTitle}:${fullValue}`; // Include \item in the value
    checkbox.id = `item-${index}-${jobTitle.replace(/\s+/g, "-")}`;
    checkbox.checked = true;

    const label = document.createElement("label");
    label.className = "item-text";
    label.htmlFor = checkbox.id;
    label.textContent = displayText; // Display without \item

    // Add edit button
    const editButton = document.createElement("button");
    editButton.className = "edit-item-btn";
    editButton.innerHTML = "✏️";
    editButton.title = "Edit this bullet point";
    editButton.addEventListener("click", function (e) {
      e.stopPropagation(); // Prevent triggering other events
      // Use the current label text instead of the original displayText
      startEditing(listItem, label, label.textContent, jobTitle);
    });

    listItem.appendChild(checkbox);
    listItem.appendChild(label);
    listItem.appendChild(editButton);

    // Add drag event listeners for reordering
    listItem.addEventListener("dragstart", handleItemDragStart);
    listItem.addEventListener("dragend", handleItemDragEnd);

    // Store the job title as a data attribute for cross-job dragging
    listItem.setAttribute("data-job-title", jobTitle);
    listItem.setAttribute("data-full-value", fullValue);

    return listItem;
  }

  // Function to start editing a bullet point
  function startEditing(listItem, label, text, jobTitle) {
    // Add editing class to the list item for styling
    listItem.classList.add("editing");

    // Create a textarea for editing
    const textarea = document.createElement("textarea");
    textarea.className = "item-edit-textarea";
    textarea.value = text;

    // Replace the label with the textarea
    label.style.display = "none";
    listItem.insertBefore(textarea, listItem.querySelector(".edit-item-btn"));

    // Add save and cancel buttons
    const saveButton = document.createElement("button");
    saveButton.className = "save-item-btn";
    saveButton.innerHTML = "✓";
    saveButton.title = "Save changes";

    const cancelButton = document.createElement("button");
    cancelButton.className = "cancel-item-btn";
    cancelButton.innerHTML = "✗";
    cancelButton.title = "Cancel editing";

    // Add buttons to the list item
    listItem.appendChild(saveButton);
    listItem.appendChild(cancelButton);

    // Hide the edit button while editing
    listItem.querySelector(".edit-item-btn").style.display = "none";

    // Auto-resize the textarea to fit content
    autoResizeTextarea(textarea);

    // Focus the textarea
    textarea.focus();

    // Add event listeners for save and cancel
    saveButton.addEventListener("click", function () {
      saveEditing(listItem, label, textarea, jobTitle);
    });

    cancelButton.addEventListener("click", function () {
      cancelEditing(listItem, label, textarea);
    });

    // Also save on Enter key (Shift+Enter for new line)
    textarea.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        saveEditing(listItem, label, textarea, jobTitle);
      }
    });

    // Auto-resize on input
    textarea.addEventListener("input", function () {
      autoResizeTextarea(this);
    });

    // Disable dragging while editing
    listItem.setAttribute("draggable", "false");
  }

  // Function to automatically resize textarea to fit content
  function autoResizeTextarea(textarea) {
    // Reset height to get the correct scrollHeight
    textarea.style.height = "auto";

    // Set height to scrollHeight to fit all content
    textarea.style.height = textarea.scrollHeight + "px";

    // Ensure minimum height
    if (parseInt(textarea.style.height) < 60) {
      textarea.style.height = "60px";
    }
  }

  // Function to save edited text
  function saveEditing(listItem, label, textarea, jobTitle) {
    const newText = textarea.value.trim();
    if (newText) {
      // Update the label text
      label.textContent = newText;

      // Update the checkbox value with the new text
      const checkbox = listItem.querySelector('input[type="checkbox"]');
      const fullValue = `\\item ${newText}`;
      checkbox.value = `${jobTitle}:${fullValue}`;

      // Update the data-full-value attribute
      listItem.setAttribute("data-full-value", fullValue);
    }

    // Clean up the editing UI
    finishEditing(listItem, label, textarea);
  }

  // Function to cancel editing
  function cancelEditing(listItem, label, textarea) {
    finishEditing(listItem, label, textarea);
  }

  // Function to clean up after editing
  function finishEditing(listItem, label, textarea) {
    // Remove editing class
    listItem.classList.remove("editing");

    // Show the label again
    label.style.display = "";

    // Remove the textarea and buttons
    if (textarea) textarea.remove();
    const saveBtn = listItem.querySelector(".save-item-btn");
    const cancelBtn = listItem.querySelector(".cancel-item-btn");
    if (saveBtn) saveBtn.remove();
    if (cancelBtn) cancelBtn.remove();

    // Show the edit button again
    const editBtn = listItem.querySelector(".edit-item-btn");
    if (editBtn) editBtn.style.display = "";

    // Re-enable dragging
    listItem.setAttribute("draggable", "true");
  }

  // Drag and drop handlers
  function handleDragStart(e) {
    this.classList.add("dragging");
    e.dataTransfer.effectAllowed = "copy";
    // Transfer both display text and full value with \item
    const data = {
      display: this.textContent,
      value: this.getAttribute("data-full-value"),
    };
    e.dataTransfer.setData("text/plain", JSON.stringify(data));

    // Also transfer the suggestion index for removal after drop
    const suggestionIndex = this.getAttribute("data-suggestion-index");
    if (suggestionIndex) {
      e.dataTransfer.setData("suggestion-index", suggestionIndex);
    }

    // Store reference to the dragged item for reordering
    window.draggedItem = this;
  }

  // Handlers for reordering items within job sections
  function handleItemDragStart(e) {
    this.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("application/x-item", "reorder"); // Just a marker to identify this as a reorder operation

    // Store the job title for cross-job dragging
    e.dataTransfer.setData(
      "source-job-title",
      this.getAttribute("data-job-title"),
    );
    e.dataTransfer.setData(
      "item-full-value",
      this.getAttribute("data-full-value"),
    );

    // Store reference to the dragged item for reordering
    window.draggedItem = this;
  }

  function handleItemDragEnd() {
    this.classList.remove("dragging");
    window.draggedItem = null;
  }

  function handleDragEnd() {
    this.classList.remove("dragging");
  }

  function handleDragOver(e) {
    e.preventDefault();

    // Check if this is a reorder operation or a suggestion drop
    const isReorderOperation =
      e.dataTransfer.types.includes("application/x-item");
    e.dataTransfer.dropEffect = isReorderOperation ? "move" : "copy";

    if (window.draggedItem) {
      const list = this;

      // Find the item we're dragging over
      const afterElement = getDragAfterElement(list, e.clientY);

      if (afterElement == null) {
        list.appendChild(window.draggedItem);
      } else {
        list.insertBefore(window.draggedItem, afterElement);
      }
    }

    return false;
  }

  // Helper function to determine where to place the dragged item
  function getDragAfterElement(container, y) {
    const draggableElements = [
      ...container.querySelectorAll(".item:not(.dragging)"),
    ];

    return draggableElements.reduce(
      (closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;

        if (offset < 0 && offset > closest.offset) {
          return { offset: offset, element: child };
        } else {
          return closest;
        }
      },
      { offset: Number.NEGATIVE_INFINITY },
    ).element;
  }

  function handleDrop(e) {
    e.preventDefault();
    this.classList.remove("drag-over");

    // Get the target job title
    const targetJobTitle = this.getAttribute("data-job-title");

    // Check if this is a reorder operation
    const isReorderOperation =
      e.dataTransfer.types.includes("application/x-item");

    if (isReorderOperation) {
      // Get the source job title
      const sourceJobTitle = e.dataTransfer.getData("source-job-title");

      // If dragging between different job sections
      if (sourceJobTitle && sourceJobTitle !== targetJobTitle) {
        console.log(
          `${new Date().toLocaleString()} - Moving item from ${sourceJobTitle} to ${targetJobTitle}`,
        );

        // Create a new item in the target job section
        const itemFullValue = e.dataTransfer.getData("item-full-value");
        const newIndex = this.children.length;

        // Create a new item with the target job title
        const newItem = createItemElement(
          targetJobTitle,
          itemFullValue,
          `new-${newIndex}`,
        );

        // Find the position to insert the new item
        const afterElement = getDragAfterElement(this, e.clientY);
        if (afterElement == null) {
          this.appendChild(newItem);
        } else {
          this.insertBefore(newItem, afterElement);
        }

        // Remove the original item from its source list
        if (window.draggedItem) {
          window.draggedItem.remove();
          window.draggedItem = null;
        }
      } else {
        // Regular reordering within the same job section is handled in dragOver
        console.log(
          `${new Date().toLocaleString()} - Item reordered within ${targetJobTitle}`,
        );
      }
      return false;
    }

    try {
      // This is a suggestion drop operation
      // Parse the transferred data to get both display text and full value
      const data = JSON.parse(e.dataTransfer.getData("text/plain"));

      // Create a new item from the suggestion, using the full value with \item
      const newIndex = this.children.length;
      const newItem = createItemElement(
        targetJobTitle,
        data.value,
        `new-${newIndex}`,
      );

      // Find the position to insert the new item
      const afterElement = getDragAfterElement(this, e.clientY);
      if (afterElement == null) {
        this.appendChild(newItem);
      } else {
        this.insertBefore(newItem, afterElement);
      }

      // Remove the suggestion from the suggestions list
      const suggestionIndex = e.dataTransfer.getData("suggestion-index");
      if (suggestionIndex) {
        // Find the suggestion element by its index and remove it
        const suggestionElement = document.querySelector(
          `.suggestion-item[data-suggestion-index="${suggestionIndex}"]`,
        );
        if (suggestionElement) {
          suggestionElement.remove();

          // Also remove it from the currentJobSuggestions array
          if (currentJobSuggestions[suggestionIndex]) {
            currentJobSuggestions.splice(suggestionIndex, 1);
          }
        }
      }
    } catch (error) {
      console.error(
        `${new Date().toLocaleString()} - Error in drop handler:`,
        error,
      );
    }

    return false;
  }

  // Close modal
  closeModalBtn.addEventListener("click", function () {
    modal.style.display = "none";
    currentJobId = null;
    currentJobExternalId = null;
    currentJobSuggestions = [];
  });

  // Close modal when clicking outside
  window.addEventListener("click", function (event) {
    if (event.target === modal) {
      modal.style.display = "none";
      currentJobId = null;
      currentJobExternalId = null;
      currentJobSuggestions = [];
    }
  });

  // Generate PDF
  generateBtn.addEventListener("click", function () {
    // Show loading message
    statusMessage.textContent = "Generating PDF...";
    statusMessage.className = "";
    statusMessage.style.display = "block";

    // Create an object to store job sections and their items in order
    const jobSections = {};

    // Process each job section to maintain the order after dragging
    document.querySelectorAll(".item-list").forEach((itemList) => {
      const jobTitle = itemList.getAttribute("data-job-title");
      if (!jobTitle) return;

      // Initialize array for this job if not exists
      if (!jobSections[jobTitle]) {
        jobSections[jobTitle] = [];
      }

      // Get all checked items in this job section in their current order
      itemList.querySelectorAll(".item").forEach((item) => {
        const checkbox = item.querySelector('input[type="checkbox"]');
        if (checkbox && checkbox.checked) {
          // Extract the item text with \item prefix
          const label = item.querySelector(".item-text");
          const itemText = label ? label.textContent.trim() : "";

          if (itemText) {
            // Format as jobTitle:\item itemText
            const formattedItem = `${jobTitle}:\\item ${itemText}`;
            jobSections[jobTitle].push(formattedItem);
          }
        }
      });
    });

    // Create form data from the organized job sections
    const formData = new FormData();

    // Add the job_id (external_id) to the form data
    if (currentJobExternalId) {
      formData.append("job_id", currentJobExternalId);
    }

    // Add all items in order by job section
    Object.keys(jobSections).forEach((jobTitle) => {
      jobSections[jobTitle].forEach((item) => {
        formData.append("selected_items[]", item);
      });
    });

    // Log the items being sent
    console.log(
      `${new Date().toLocaleString()} - Sending items to generate resume:`,
      Array.from(formData.getAll("selected_items[]")),
    );

    // Also log the job sections object for debugging
    console.log(
      `${new Date().toLocaleString()} - Job sections structure:`,
      jobSections,
    );

    // Send request to generate PDF
    fetch("/generate_resume", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          statusMessage.textContent = "PDF generated successfully!";
          statusMessage.className = "success";
          console.log(
            `${new Date().toLocaleString()} - PDF generated successfully`,
          );

          // Show the PDF in a popup dialog instead of opening in a new tab
          if (data.pdf_path) {
            console.log(
              `${new Date().toLocaleString()} - Showing PDF in dialog: ${
                data.pdf_path
              }`,
            );

            // Create or get the PDF viewer modal
            let pdfViewerModal = document.getElementById("pdf-viewer-modal");
            if (!pdfViewerModal) {
              pdfViewerModal = document.createElement("div");
              pdfViewerModal.id = "pdf-viewer-modal";
              pdfViewerModal.className = "modal pdf-viewer-modal";

              // Create modal content
              const modalContent = document.createElement("div");
              modalContent.className = "modal-content pdf-viewer-content";

              // Add iframe for PDF
              const pdfFrame = document.createElement("iframe");
              pdfFrame.id = "pdf-frame";
              pdfFrame.className = "pdf-frame";

              // Add elements to the DOM
              modalContent.appendChild(pdfFrame);
              pdfViewerModal.appendChild(modalContent);
              document.body.appendChild(pdfViewerModal);

              // Close modal when clicking outside
              window.addEventListener("click", function (event) {
                if (event.target === pdfViewerModal) {
                  pdfViewerModal.style.display = "none";
                }
              });
            }

            // Set the PDF source and show the modal
            const pdfFrame = document.getElementById("pdf-frame");

            // Add a timestamp to prevent caching
            const timestamp = new Date().getTime();
            const pdfUrl = `${data.pdf_path}?t=${timestamp}#toolbar=0&view=FitV`;

            // Force iframe refresh by removing and recreating it
            const existingFrame = document.getElementById("pdf-frame");
            if (existingFrame) {
              const parent = existingFrame.parentNode;

              // Create a new iframe element
              const newFrame = document.createElement("iframe");
              newFrame.id = "pdf-frame";
              newFrame.className = "pdf-frame";
              newFrame.src = pdfUrl;

              // Replace the old iframe with the new one
              parent.replaceChild(newFrame, existingFrame);

              console.log(
                `${new Date().toLocaleString()} - PDF iframe refreshed with new URL: ${pdfUrl}`,
              );
            } else {
              pdfFrame.src = pdfUrl;
            }

            pdfViewerModal.style.display = "block";
          } else {
            console.warn(
              `${new Date().toLocaleString()} - PDF path not provided in response`,
            );
          }
        } else {
          statusMessage.textContent =
            "Error generating PDF: " + (data.error || "Unknown error");
          statusMessage.className = "error";
          console.error(`${new Date().toLocaleString()} - Error:`, data.error);
        }
      })
      .catch((error) => {
        statusMessage.textContent = "Error generating PDF: " + error.message;
        statusMessage.className = "error";
        console.error(`${new Date().toLocaleString()} - Error:`, error);
      });
  });
});
