document.addEventListener("DOMContentLoaded", () => {
  // Initialize 3D effects for profile elements
  init3DProfileElements()

  // Initialize parallax effects
  initProfileParallax()

  // Initialize hover effects for application cards
  initApplicationCards()
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
      const centerY = rect.height / 2

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
