document.addEventListener("DOMContentLoaded", () => {
  // Initialize 3D effects for profile elements

  const profileDataDiv = document.getElementById("profileData");
  const githubUsername = localStorage.getItem('githubUsername');
  if (githubUsername) {
    fetchGitHubData(githubUsername);
  } else {
    profileDataDiv.innerHTML = "<p>Please complete a job search first to load your profile data.</p>";
  }
  async function fetchGitHubData(username) {
    profileDataDiv.innerHTML = "<p>Loading profile data...</p>";
    try {
      const response = await fetch(`https://api.github.com/users/${username}`);
      if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status}`);
      }
      const data = await response.json();
      displayProfileData(data);
    } catch (error) {
      console.error("Error fetching GitHub data:", error);
      profileDataDiv.innerHTML = `<p>Error loading profile data: ${error.message}</p>`;
    }
  }
  function displayProfileData(data) {
  init3DProfileElements()

  // Initialize parallax effects
  initProfileParallax()

  // Initialize hover effects for application cards
  initApplicationCards()
  if (data) {
    profileDataDiv.innerHTML = `
              <div class="bg-white rounded-xl shadow-lg p-8">
                  <h2 class="text-3xl font-bold mb-6 hover-3d">Your GitHub Profile</h2>
                  <div class="flex items-center space-x-6 mb-6">
                      <img src="${data.avatar_url}" alt="GitHub Avatar" class="w-24 h-24 rounded-full">
                      <div>
                          <h3 class="text-2xl font-bold">${data.name || data.login}</h3>
                          <p class="text-gray-600">${data.bio || "No bio available."}</p>
                          <a href="${data.html_url}" target="_blank" class="text-blue-500 hover:underline">View on GitHub</a>
                      </div>
                  </div>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                          <p><span class="font-semibold">Username:</span> ${data.login}</p>
                          <p><span class="font-semibold">Location:</span> ${data.location || "Not specified"}</p>
                          <p><span class="font-semibold">Email:</span> ${data.email || "Not available"}</p>
                      </div>
                      <div>
                          <p><span class="font-semibold">Followers:</span> ${data.followers}</p>
                          <p><span class="font-semibold">Following:</span> ${data.following}</p>
                          <p><span class="font-semibold">Public Repos:</span> ${data.public_repos}</p>
                      </div>
                  </div>
              </div>
          `;
  } else {
    profileDataDiv.innerHTML = "<p>No profile data available.</p>";
  }
}
})



















// Initialize 3D effects for profile elements
function init3DProfileElements() {
  const profileImage = document.querySelector(".profile-image")
  const skillTags = document.querySelectorAll(".bg-gray-100.rounded-full")

  // Profile image hover effect
  if (profileImage) {
    profileImage.addEventListener("mousemove", (e) => {
      const rect = profileImage.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top

      const centerX = rect.width / 2
      const centerY = rect.height / 2;

      const moveX = (x - centerX) / 10
      const moveY = (y - centerY) / 10

      profileImage.style.transform = `translate3d(${moveX}px, ${moveY}px, 0) scale(1.05)`
    })

    profileImage.addEventListener("mouseleave", () => {
      profileImage.style.transform = "translate3d(0, 0, 0) scale(1)"
    })
  }

  // Skill tags hover effect
  skillTags.forEach((tag) => {
    tag.addEventListener("mouseenter", () => {
      tag.style.transform = "translateY(-5px)"
    })

    tag.addEventListener("mouseleave", () => {
      tag.style.transform = "translateY(0)"
    })
  })
}

// Initialize parallax effects for profile page
function initProfileParallax() {
  const parallaxItems = document.querySelectorAll(".parallax-item")

  window.addEventListener("mousemove", (e) => {
    const x = e.clientX / window.innerWidth
    const y = e.clientY / window.innerHeight

    parallaxItems.forEach((item) => {
      const depth = Number.parseFloat(item.getAttribute("data-depth")) || 0.1
      const moveX = (x - 0.5) * 50 * depth
      const moveY = (y - 0.5) * 50 * depth

      item.style.transform = `translate3d(${moveX}px, ${moveY}px, 0)`
    })
  })
}

// Initialize hover effects for application cards
function initApplicationCards() {
  const applicationCards = document.querySelectorAll(".hover-3d-card")

  applicationCards.forEach((card) => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top

      const centerX = rect.width / 2
      const centerY = rect.height / 2

      const rotateX = (y - centerY) / 20
      const rotateY = (centerX - x) / 20

      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(5px)`
    })

    card.addEventListener("mouseleave", () => {
      card.style.transform = "perspective(1000px) rotateX(0) rotateY(0) translateZ(0)"
    })
  })
}
