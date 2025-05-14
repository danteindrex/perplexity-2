document.addEventListener("DOMContentLoaded", () => {
  // Initialize Three.js effects
  initThreeJsEffects()

  // Initialize smooth page transitions
  initPageTransitions()

  // Initialize magnetic effect
  initMagneticEffect()

  // Initialize text splitting effect
  initTextSplitting()

  // Initialize particle background
  initParticleBackground()
})

// Three.js Background Effect
function initThreeJsEffects() {
  // Check if Three.js is loaded
  if (typeof THREE === "undefined") {
    console.warn("Three.js is not loaded. Skipping 3D effects.")
    return
  }

  // Create a scene for specific sections if needed
  const heroSection = document.querySelector(".hero")

  if (heroSection) {
    // Create scene, camera, and renderer
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })

    renderer.setSize(window.innerWidth, window.innerHeight)
    renderer.setPixelRatio(window.devicePixelRatio)

    // Create a container for the canvas
    const container = document.createElement("div")
    container.classList.add("three-js-background")
    container.style.position = "absolute"
    container.style.top = "0"
    container.style.left = "0"
    container.style.width = "100%"
    container.style.height = "100%"
    container.style.zIndex = "-1"
    container.style.opacity = "0.5"

    container.appendChild(renderer.domElement)
    heroSection.appendChild(container)

    // Create particles
    const particlesGeometry = new THREE.BufferGeometry()
    const particlesCount = 1000

    const posArray = new Float32Array(particlesCount * 3)

    for (let i = 0; i < particlesCount * 3; i++) {
      posArray[i] = (Math.random() - 0.5) * 5
    }

    particlesGeometry.setAttribute("position", new THREE.BufferAttribute(posArray, 3))

    // Materials
    const particlesMaterial = new THREE.PointsMaterial({
      size: 0.005,
      color: 0x000000,
    })

    // Mesh
    const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial)
    scene.add(particlesMesh)

    // Position camera
    camera.position.z = 3

    // Mouse movement effect
    let mouseX = 0
    let mouseY = 0

    document.addEventListener("mousemove", (event) => {
      mouseX = event.clientX / window.innerWidth - 0.5
      mouseY = event.clientY / window.innerHeight - 0.5
    })

    // Animation
    const animate = () => {
      requestAnimationFrame(animate)

      particlesMesh.rotation.y += 0.001
      particlesMesh.rotation.x += 0.001

      // Follow mouse
      particlesMesh.rotation.y += mouseX * 0.1
      particlesMesh.rotation.x += mouseY * 0.1

      renderer.render(scene, camera)
    }

    animate()

    // Handle resize
    window.addEventListener("resize", () => {
      camera.aspect = window.innerWidth / window.innerHeight
      camera.updateProjectionMatrix()
      renderer.setSize(window.innerWidth, window.innerHeight)
    })
  }
}

// Smooth Page Transitions
function initPageTransitions() {
  const links = document.querySelectorAll(
    'a[href^="/"]:not([target]), a[href^="./"]:not([target]), a[href^="../"]:not([target]), a[href^="index.html"]:not([target]), a[href^="about.html"]:not([target]), a[href^="job-search.html"]:not([target]), a[href^="contact.html"]:not([target]), a[href^="profile.html"]:not([target])',
  )

  links.forEach((link) => {
    link.addEventListener("click", (e) => {
      // Only handle internal links
      if (link.hostname === window.location.hostname) {
        e.preventDefault()

        const href = link.getAttribute("href")

        // Create transition overlay
        const overlay = document.createElement("div")
        overlay.classList.add("page-transition-overlay")
        overlay.style.position = "fixed"
        overlay.style.top = "0"
        overlay.style.left = "0"
        overlay.style.width = "100%"
        overlay.style.height = "100%"
        overlay.style.backgroundColor = "#000"
        overlay.style.zIndex = "9999"
        overlay.style.opacity = "0"
        overlay.style.transition = "opacity 0.5s ease"

        document.body.appendChild(overlay)

        // Fade in overlay
        setTimeout(() => {
          overlay.style.opacity = "1"
        }, 10)

        // Navigate to new page after transition
        setTimeout(() => {
          window.location.href = href
        }, 500)
      }
    })
  })
}

// Magnetic Effect for Buttons
function initMagneticEffect() {
  const buttons = document.querySelectorAll(".btn-primary, .btn-secondary, .btn-white")

  buttons.forEach((button) => {
    button.addEventListener("mousemove", (e) => {
      const rect = button.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top

      const centerX = rect.width / 2
      const centerY = rect.height / 2

      const moveX = (x - centerX) * 0.2
      const moveY = (y - centerY) * 0.2

      button.style.transform = `translate(${moveX}px, ${moveY}px)`
    })

    button.addEventListener("mouseleave", () => {
      button.style.transform = "translate(0, 0)"
    })
  })
}

// Text Splitting Effect
function initTextSplitting() {
  const headings = document.querySelectorAll("h1, h2")

  headings.forEach((heading) => {
    if (heading.classList.contains("hover-3d")) {
      const text = heading.textContent
      heading.textContent = ""

      for (let i = 0; i < text.length; i++) {
        const span = document.createElement("span")
        span.textContent = text[i] === " " ? "\u00A0" : text[i]
        span.style.display = "inline-block"
        span.style.transition = `transform 0.3s ease ${i * 0.03}s`

        heading.appendChild(span)
      }

      heading.addEventListener("mouseenter", () => {
        Array.from(heading.children).forEach((span, index) => {
          span.style.transform = `translateY(-${Math.random() * 10}px)`
        })
      })

      heading.addEventListener("mouseleave", () => {
        Array.from(heading.children).forEach((span) => {
          span.style.transform = "translateY(0)"
        })
      })
    }
  })
}

// Particle Background
function initParticleBackground() {
  // Check if Three.js is loaded
  if (typeof THREE === "undefined") {
    console.warn("Three.js is not loaded. Skipping particle background.")
    return
  }

  const sections = document.querySelectorAll(".py-20")

  sections.forEach((section, index) => {
    // Only add to certain sections
    if (index % 2 === 1) return

    // Create scene, camera, and renderer
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(75, section.clientWidth / section.clientHeight, 0.1, 1000)
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })

    renderer.setSize(section.clientWidth, section.clientHeight)
    renderer.setPixelRatio(window.devicePixelRatio)

    // Create a container for the canvas
    const container = document.createElement("div")
    container.classList.add("particle-background")
    container.style.position = "absolute"
    container.style.top = "0"
    container.style.left = "0"
    container.style.width = "100%"
    container.style.height = "100%"
    container.style.zIndex = "-1"
    container.style.opacity = "0.2"

    container.appendChild(renderer.domElement)
    section.style.position = "relative"
    section.appendChild(container)

    // Create particles
    const particlesGeometry = new THREE.BufferGeometry()
    const particlesCount = 500

    const posArray = new Float32Array(particlesCount * 3)

    for (let i = 0; i < particlesCount * 3; i++) {
      posArray[i] = (Math.random() - 0.5) * 5
    }

    particlesGeometry.setAttribute("position", new THREE.BufferAttribute(posArray, 3))

    // Materials
    const particlesMaterial = new THREE.PointsMaterial({
      size: 0.003,
      color: 0x000000,
    })

    // Mesh
    const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial)
    scene.add(particlesMesh)

    // Position camera
    camera.position.z = 2

    // Animation
    const animate = () => {
      requestAnimationFrame(animate)

      particlesMesh.rotation.y += 0.0005
      particlesMesh.rotation.x += 0.0005

      renderer.render(scene, camera)
    }

    animate()

    // Handle resize
    window.addEventListener("resize", () => {
      camera.aspect = section.clientWidth / section.clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(section.clientWidth, section.clientHeight)
    })

    // Handle scroll
    window.addEventListener("scroll", () => {
      const rect = section.getBoundingClientRect()
      if (rect.top < window.innerHeight && rect.bottom > 0) {
        const scrollProgress = (window.innerHeight - rect.top) / (window.innerHeight + rect.height)
        particlesMesh.rotation.y = scrollProgress * 0.5
      }
    })
  })
}
