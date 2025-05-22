// ========================
// job-search.js (updated)
// ========================
document.addEventListener("DOMContentLoaded", () => {
  // Element references
  const jobSearchForm   = document.getElementById("jobSearchForm");
  const loadingIndicator = document.getElementById("loadingIndicator");
  const jobResults      = document.getElementById("jobResults");
  const jobListings     = document.getElementById("jobListings");
  const noResults       = document.getElementById("noResults");
  const searchAgainBtn  = document.getElementById("searchAgainBtn");
  const loadMoreBtn     = document.getElementById("loadMoreBtn");
  const errorModal      = document.getElementById("errorModal");
  const errorMessage    = document.getElementById("errorMessage");
  const successModal    = document.getElementById("successModal");
  const modalCloseButtons = document.querySelectorAll(".modal-close");
  const resumeFileInput = document.getElementById("resumeFile");

  let allJobs     = [];
  let currentPage = 1;
  const jobsPerPage = 10;
  let resumeText = "";

  // On page load: show the Results container by default,
  // but hide “No Results” and “Loading” and any modals.
  jobResults.classList.remove("hidden");
  noResults.classList.add("hidden");
  loadingIndicator.classList.add("hidden");
  errorModal.classList.add("hidden");
  successModal.classList.add("hidden");
  loadMoreBtn.classList.add("hidden");

  // ───────────────────────────────────────────────────────────────────────────
  // Handle PDF file upload
  // ───────────────────────────────────────────────────────────────────────────
  resumeFileInput?.addEventListener("change", (event) => {
    const file = event.target.files[0];
    if (!file) return;
  
    const reader = new FileReader();
    reader.onload = async function(e) {
      const typedarray = new Uint8Array(e.target.result);
  
      try {
        // Load the PDF
        const pdf = await pdfjsLib.getDocument({data: typedarray}).promise;
        let textContent = "";
  
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const txt = await page.getTextContent();
          textContent += txt.items.map(item => item.str).join(' ') + "\n";
        }
        
        resumeText = textContent;
        console.log("Resume text extracted successfully");
      } catch (err) {
        console.error("Error extracting PDF text:", err);
        showErrorModal("Failed to extract text from PDF. Please upload a valid PDF file.");
      }
    };
    
    reader.readAsArrayBuffer(file);
  });

  // ───────────────────────────────────────────────────────────────────────────
  // Handle form submission: fetch jobs from http://localhost:5000/get_jobs
  // ───────────────────────────────────────────────────────────────────────────
  jobSearchForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const githubUsername = document.getElementById("githubUsername").value.trim();
    const resumeId = document.getElementById("resumeId")?.value.trim() || "";

    if (!githubUsername) {
      showErrorModal("Please enter your GitHub username");
      return;
    }

    if (!resumeId && !resumeText) {
      showErrorModal("Please either enter a Resume ID or upload a resume file");
      return;
    }

    // Show loading; hide any “No Results” text or previous job cards
    loadingIndicator.classList.remove("hidden");
    noResults.classList.add("hidden");
    jobListings.innerHTML = "";
    loadMoreBtn.classList.add("hidden");
    currentPage = 1;

    try {
      // Build request URL with appropriate parameters
      let url = `http://localhost:5000/get_jobs?github_username=${encodeURIComponent(githubUsername)}`;
      
      if (resumeId) {
        url += `&resume_id=${encodeURIComponent(resumeId)}`;
      }
      
      // Create request options object
      const requestOptions = {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      };
      
      // If we have resume text from a file upload, add it to the body
      if (resumeText && !resumeId) {
        requestOptions.method = 'POST';
        requestOptions.body = JSON.stringify({
          github_username: githubUsername,
          resume_text: resumeText
        });
      }

      const response = await fetch(url, requestOptions);

      // If server returns non‐2xx, handle it here
      if (!response.ok) {
        if (response.status === 422) {
          let errorDetail = "The server couldn't process your request due to validation errors.";
          try {
            const errorData = await response.json();
            if (errorData.detail || errorData.message) {
              errorDetail = errorData.detail || errorData.message;
            }
          } catch (_) { /* ignore parse errors */ }

          throw new Error(`Validation Error (422): ${errorDetail}. Please check that your GitHub username and resume ID are correct.`);
        } else {
          throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }
      }

      // Parse JSON as an array of job objects
      allJobs = await response.json();

      // Hide the loading spinner
      loadingIndicator.classList.add("hidden");

      // If there are no jobs, hide #jobResults and show #noResults
      if (!Array.isArray(allJobs) || allJobs.length === 0) {
        jobResults.classList.add("hidden");
        noResults.classList.remove("hidden");
      } else {
        // We have at least one job: show the Results, then populate page #1
        jobResults.classList.remove("hidden");
        displayJobsPage(currentPage);
      }
    } catch (err) {
      // If anything fails here, hide loading and show the error modal
      loadingIndicator.classList.add("hidden");
      showErrorModal(`Failed to fetch jobs: ${err.message}`);
    }
  });

  // ───────────────────────────────────────────────────────────────────────────
  // Display a page of jobs; show or hide Load More
  // ───────────────────────────────────────────────────────────────────────────
  function displayJobsPage(page) {
    const start = (page - 1) * jobsPerPage;
    const end   = start + jobsPerPage;
    const pageJobs = allJobs.slice(start, end);

    pageJobs.forEach((job) => {
      jobListings.appendChild(createJobCard(job));
    });

    init3DJobCards();

    if (end < allJobs.length) {
      loadMoreBtn.classList.remove("hidden");
    } else {
      loadMoreBtn.classList.add("hidden");
    }
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Load more button
  // ───────────────────────────────────────────────────────────────────────────
  loadMoreBtn.addEventListener("click", () => {
    currentPage++;
    displayJobsPage(currentPage);
  });

  // ───────────────────────────────────────────────────────────────────────────
  // Create a job card element (unchanged)
  // ───────────────────────────────────────────────────────────────────────────
  function createJobCard(job) {
    const card = document.createElement("div");
    card.className = "bg-white rounded-xl shadow-lg p-6 mb-6 hover-3d-card";
    card.innerHTML = `
      <div class="flex items-start">
        <div class="flex-shrink-0 mr-4">
          <img src="${job.logo || "/placeholder.svg?height=48&width=48"}" alt="${job.company} Logo" class="w-12 h-12 rounded-full">
        </div>
        <div class="flex-1">
          <h3 class="text-xl font-bold mb-1">${job.title}</h3>
          <p class="text-gray-600 mb-1">${job.company}</p>
          <p class="text-gray-500 mb-3">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline-block mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
            ${job.location}
          </p>
          <div class="flex flex-wrap gap-2 mb-4">
            ${(job.skills || []).map((s) => `<span class="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded">${s}</span>`).join("")}
          </div>
          <p class="text-gray-600 mb-4">${job.description}</p>
          <div class="flex justify-between items-center">
            <div>
              <p class="text-sm text-gray-500">${job.salary || ""}</p>
              <p class="text-sm text-gray-500">${job.type || ""}</p>
            </div>
            <button class="btn-primary apply-btn" data-job-id="${job.id}">Apply Now</button>
          </div>
        </div>
      </div>`;
    return card;
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Apply for job: send POST to /auto_apply (unchanged)
  // ───────────────────────────────────────────────────────────────────────────
  async function applyForJob(jobId) {
    try {
      const applyBtn = document.querySelector(`.apply-btn[data-job-id="${jobId}"]`);
      if (applyBtn) {
        applyBtn.textContent = "Applying...";
        applyBtn.disabled = true;
      }

      const response = await fetch("http://localhost:8000/auto_apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId }),
      });

      if (!response.ok) {
        throw new Error(`Application failed: ${response.status} ${response.statusText}`);
      }

      showSuccessModal();
    } catch (err) {
      showErrorModal(err.message);
    } finally {
      const applyBtn = document.querySelector(`.apply-btn[data-job-id="${jobId}"]`);
      if (applyBtn) {
        applyBtn.textContent = "Apply Now";
        applyBtn.disabled = false;
      }
    }
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Modals
  // ───────────────────────────────────────────────────────────────────────────
  function showSuccessModal() {
    successModal.classList.remove("hidden");
  }

  function showErrorModal(msg) {
    // Hide the Results container when showing an error
    jobResults.classList.add("hidden");
    noResults.classList.add("hidden");

    errorMessage.textContent = msg;
    if (msg.includes("422")) {
      const tipElement = document.createElement("p");
      tipElement.className = "text-sm text-gray-500 mt-2";
      tipElement.innerHTML =
        "Troubleshooting tips:<br>• Ensure your GitHub username is spelled correctly<br>• Check that your resume ID is valid<br>• Try using a different resume ID format (e.g., numeric only)";
      errorMessage.appendChild(tipElement);
    } else if (msg.includes("Failed to fetch")) {
      const tipElement = document.createElement("p");
      tipElement.className = "text-sm text-gray-500 mt-2";
      tipElement.innerHTML =
        "Troubleshooting tips:<br>• Check that the API server is running at http://localhost:5000<br>• Verify your network connection<br>• Try again in a few moments";
      errorMessage.appendChild(tipElement);
    }

    errorModal.classList.remove("hidden");
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Close modals when clicking close button
  // ───────────────────────────────────────────────────────────────────────────
  modalCloseButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const modal = button.closest(".modal-backdrop");
      if (modal) {
        modal.classList.add("hidden");
        // If we just closed the error modal, put #jobResults back
        if (modal.id === "errorModal") {
          jobResults.classList.remove("hidden");
        }
      }
    });
  });

  // ───────────────────────────────────────────────────────────────────────────
  // Search again
  // ───────────────────────────────────────────────────────────────────────────
  searchAgainBtn?.addEventListener("click", () => {
    noResults.classList.add("hidden");
    jobListings.innerHTML = "";
    jobResults.classList.remove("hidden");
    jobSearchForm.reset();
    window.scrollTo({ top: jobSearchForm.offsetTop - 100, behavior: "smooth" });
  });

  // ───────────────────────────────────────────────────────────────────────────
  // Preserve the existing 3D functionality
  // ───────────────────────────────────────────────────────────────────────────
  function init3DJobCards() {
    document.querySelectorAll(".hover-3d-card").forEach((card) => {
      card.querySelector(".apply-btn")?.addEventListener("click", function () {
        applyForJob(this.dataset.jobId);
      });
      // The 3D tilt effect is still handled in effects.js
    });
  }
});
