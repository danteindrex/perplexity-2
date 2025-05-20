document.addEventListener("DOMContentLoaded", () => {
  // Element references
  const jobSearchForm = document.getElementById("jobSearchForm")
  const loadingIndicator = document.getElementById("loadingIndicator")
  const jobResults = document.getElementById("jobResults")
  const jobListings = document.getElementById("jobListings")
  const noResults = document.getElementById("noResults")
  const searchAgainBtn = document.getElementById("searchAgainBtn")
  const loadMoreBtn = document.getElementById("loadMoreBtn")
  const errorModal = document.getElementById("errorModal")
  const errorMessage = document.getElementById("errorMessage")
  const successModal = document.getElementById("successModal")
  const modalCloseButtons = document.querySelectorAll(".modal-close")

  let allJobs = []
  let currentPage = 1
  const jobsPerPage = 10

  // Handle form submission: fetch jobs from http://localhost:5000/get_jobs
  jobSearchForm.addEventListener("submit", async (e) => {
    e.preventDefault()

    const githubUsername = document.getElementById("githubUsername").value.trim()
    const resumeId = document.getElementById("resumeId").value.trim()

    if (!githubUsername || !resumeId) {
      showErrorModal("Please enter both GitHub username and Resume ID")
      return
    }

    // Show loading, hide previous results/messages
    loadingIndicator.classList.remove("hidden")
    jobResults.classList.add("hidden")
    noResults.classList.add("hidden")
    jobListings.innerHTML = ""
    loadMoreBtn.classList.add("hidden")
    currentPage = 1

    try {
      const response = await fetch(
        `http://localhost:5000/get_jobs?github_username=${encodeURIComponent(githubUsername)}&resume_id=${encodeURIComponent(resumeId)}`,
      )

      if (!response.ok) {
        // Handle specific error codes
        if (response.status === 422) {
          let errorDetail = "The server couldn't process your request due to validation errors."

          // Try to get more detailed error information if available
          try {
            const errorData = await response.json()
            if (errorData.detail || errorData.message) {
              errorDetail = errorData.detail || errorData.message
            }
          } catch (e) {
            // If we can't parse the error response, use the default message
          }

          throw new Error(
            `Validation Error (422): ${errorDetail}. Please check that your GitHub username and resume ID are correct.`,
          )
        } else {
          throw new Error(`Server error: ${response.status} ${response.statusText}`)
        }
      }

      allJobs = response

      // Hide loading indicator
      loadingIndicator.classList.add("hidden")

      if (allJobs.length === 0) {
        noResults.classList.remove("hidden")
      } else {
        displayJobsPage(currentPage)
        jobResults.classList.remove("hidden")
      }
    } catch (err) {
      loadingIndicator.classList.add("hidden")
      showErrorModal(`Failed to fetch jobs: ${err.message}`)
    }
  })

  // Display a page of jobs; show or hide Load More
  function displayJobsPage(page) {
    const start = (page - 1) * jobsPerPage
    const end = start + jobsPerPage
    const pageJobs = allJobs.slice(start, end)

    pageJobs.forEach((job) => {
      jobListings.appendChild(createJobCard(job))
    })

    init3DJobCards()

    if (end < allJobs.length) {
      loadMoreBtn.classList.remove("hidden")
    } else {
      loadMoreBtn.classList.add("hidden")
    }
  }

  // Load more button
  loadMoreBtn.addEventListener("click", () => {
    currentPage++
    displayJobsPage(currentPage)
  })

  // Create a job card element
  function createJobCard(job) {
    const card = document.createElement("div")
    card.className = "bg-white rounded-xl shadow-lg p-6 mb-6 hover-3d-card"
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
      </div>`
    return card
  }

  // Apply for job: send POST to /auto_apply
  async function applyForJob(jobId) {
    try {
      // Show loading state on the button
      const applyBtn = document.querySelector(`.apply-btn[data-job-id="${jobId}"]`)
      if (applyBtn) {
        applyBtn.textContent = "Applying..."
        applyBtn.disabled = true
      }

      const response = await fetch("http://localhost:8000/auto_apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId }),
      })

      if (!response.ok) {
        throw new Error(`Application failed: ${response.status} ${response.statusText}`)
      }

      showSuccessModal()
    } catch (err) {
      showErrorModal(err.message)
    } finally {
      // Reset button state
      const applyBtn = document.querySelector(`.apply-btn[data-job-id="${jobId}"]`)
      if (applyBtn) {
        applyBtn.textContent = "Apply Now"
        applyBtn.disabled = false
      }
    }
  }

  // Modals
  function showSuccessModal() {
    successModal.classList.remove("hidden")
  }

  function showErrorModal(msg) {
    errorMessage.textContent = msg

    // Add troubleshooting tips for common errors
    if (msg.includes("422")) {
      const tipElement = document.createElement("p")
      tipElement.className = "text-sm text-gray-500 mt-2"
      tipElement.innerHTML =
        "Troubleshooting tips:<br>• Ensure your GitHub username is spelled correctly<br>• Check that your resume ID is valid<br>• Try using a different resume ID format (e.g., numeric only)"
      errorMessage.appendChild(tipElement)
    } else if (msg.includes("Failed to fetch")) {
      const tipElement = document.createElement("p")
      tipElement.className = "text-sm text-gray-500 mt-2"
      tipElement.innerHTML =
        "Troubleshooting tips:<br>• Check that the API server is running at http://localhost:5000<br>• Verify your network connection<br>• Try again in a few moments"
      errorMessage.appendChild(tipElement)
    }

    errorModal.classList.remove("hidden")
  }

  // Close modals when clicking close button
  modalCloseButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const modal = button.closest(".modal-backdrop")
      if (modal) {
        modal.classList.add("hidden")
      }
    })
  })

  // Search again
  searchAgainBtn?.addEventListener("click", () => {
    noResults.classList.add("hidden")
    jobSearchForm.reset()
    window.scrollTo({ top: jobSearchForm.offsetTop - 100, behavior: "smooth" })
  })

  // Preserve the existing 3D functionality
  function init3DJobCards() {
    document.querySelectorAll(".hover-3d-card").forEach((card) => {
      // Apply button
      card.querySelector(".apply-btn")?.addEventListener("click", function () {
        applyForJob(this.dataset.jobId)
      })

      // 3D tilt effect is already handled in the original effects.js
    })
  }
})
