document.addEventListener("DOMContentLoaded", () => {
  // Initialize loading screen
  initLoadingScreen()

  // Initialize custom cursor
  initCustomCursor()

  // Initialize 3D hover effects
  init3DHoverEffects()

  // Initialize parallax effects
  initParallaxEffects()

  // Initialize reveal animations
  initRevealAnimations()

  // Mobile menu toggle
  initMobileMenu()

  // Modal functionality
  initModals()
})

// Loading Screen
function initLoadingScreen() {
  const loadingScreen = document.querySelector(".loading-screen")
  const loadingPercentage = document.querySelector(".loading-percentage")

  if (!loadingScreen || !loadingPercentage) return

  let progress = 0
  const totalAssets = 100 // Simulate 100 assets to load

  // Simulate loading progress
  const interval = setInterval(() => {
    progress += Math.floor(Math.random() * 5) + 1

    if (progress >= 100) {
      progress = 100
      clearInterval(interval)

      // Hide loading screen after a short delay
      setTimeout(() => {
        loadingScreen.style.opacity = "0"
        setTimeout(() => {
          loadingScreen.style.visibility = "hidden"
        }, 500)
      }, 500)
    }

    loadingPercentage.textContent = progress
  }, 100)
}

// Custom Cursor
function initCustomCursor() {
  const cursor = document.querySelector(".cursor")
  const cursorFollower = document.querySelector(".cursor-follower")

  if (!cursor || !cursorFollower) return

  document.addEventListener("mousemove", (e) => {
    cursor.style.left = e.clientX + "px"
    cursor.style.top = e.clientY + "px"

    // Add a slight delay to the follower for a smoother effect
    setTimeout(() => {
      cursorFollower.style.left = e.clientX + "px"
      cursorFollower.style.top = e.clientY + "px"
    }, 50)
  })

  // Cursor grow effect on interactive elements
  const interactiveElements = document.querySelectorAll("a, button, input, textarea, .hover-3d, .hover-3d-card")

  interactiveElements.forEach((el) => {
    el.addEventListener("mouseenter", () => {
      cursor.classList.add("cursor-grow")
      cursorFollower.classList.add("cursor-follower-grow")
    })

    el.addEventListener("mouseleave", () => {
      cursor.classList.remove("cursor-grow")
      cursorFollower.classList.remove("cursor-follower-grow")
    })
  })
}

// 3D Hover Effects
function init3DHoverEffects() {
  const cards = document.querySelectorAll(".hover-3d-card")

  cards.forEach((card) => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top

      const centerX = rect.width / 2
      const centerY = rect.height / 2

      const rotateX = (y - centerY) / 10
      const rotateY = (centerX - x) / 10

      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`
    })

    card.addEventListener("mouseleave", () => {
      card.style.transform = "perspective(1000px) rotateX(0) rotateY(0)"
    })
  })
}

// Parallax Effects
function initParallaxEffects() {
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

// Reveal Animations
function initRevealAnimations() {
  const revealElements = document.querySelectorAll(".reveal-text, .reveal-element, .reveal-image")

  const revealOnScroll = () => {
    revealElements.forEach((el) => {
      const elementTop = el.getBoundingClientRect().top
      const elementVisible = 150

      if (elementTop < window.innerHeight - elementVisible) {
        el.classList.add("active")
      }
    })
  }

  // Initial check
  revealOnScroll()

  // Check on scroll
  window.addEventListener("scroll", revealOnScroll)
}

// Mobile Menu
function initMobileMenu() {
  const menuToggle = document.querySelector(".menu-toggle")
  const mobileMenu = document.querySelector(".mobile-menu")

  if (!menuToggle || !mobileMenu) return

  menuToggle.addEventListener("click", () => {
    mobileMenu.classList.toggle("hidden")

    if (!mobileMenu.classList.contains("hidden")) {
      setTimeout(() => {
        mobileMenu.classList.add("active")
      }, 10)
    } else {
      mobileMenu.classList.remove("active")
    }
  })
}

// Modal Functionality
function initModals() {
  const modalTriggers = document.querySelectorAll("[data-modal]")
  const modalCloseButtons = document.querySelectorAll(".modal-close")

  modalTriggers.forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const modalId = trigger.getAttribute("data-modal")
      const modal = document.getElementById(modalId)

      if (modal) {
        modal.classList.remove("hidden")
        setTimeout(() => {
          modal.querySelector(".modal-content").classList.add("active")
        }, 10)
      }
    })
  })

  modalCloseButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const modal = button.closest("[id]")

      if (modal) {
        modal.querySelector(".modal-content").classList.remove("active")
        setTimeout(() => {
          modal.classList.add("hidden")
        }, 300)
      }
    })
  })

  // Close modal when clicking outside
  document.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-backdrop")) {
      const modal = e.target.closest("[id]")

      if (modal) {
        modal.querySelector(".modal-content").classList.remove("active")
        setTimeout(() => {
          modal.classList.add("hidden")
        }, 300)
      }
    }
  })
}
