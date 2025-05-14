document.addEventListener("DOMContentLoaded", () => {
  // Contact form submission
  const contactForm = document.getElementById("contactForm")
  const contactSuccessModal = document.getElementById("contactSuccessModal")

  if (contactForm) {
    contactForm.addEventListener("submit", (e) => {
      e.preventDefault()

      // Get form data
      const name = document.getElementById("name").value
      const email = document.getElementById("email").value
      const subject = document.getElementById("subject").value
      const message = document.getElementById("message").value

      // In a real implementation, you would send this data to your backend
      // For this demo, we'll just show a success message

      // Show success modal
      if (contactSuccessModal) {
        contactSuccessModal.classList.remove("hidden")
        setTimeout(() => {
          contactSuccessModal.querySelector(".modal-content").classList.add("active")
        }, 10)
      }

      // Reset form
      contactForm.reset()
    })
  }

  // Initialize 3D effects for form elements
  init3DFormElements()
})

// Initialize 3D effects for form elements
function init3DFormElements() {
  const formInputs = document.querySelectorAll(".form-input")

  formInputs.forEach((input) => {
    input.addEventListener("focus", () => {
      input.parentElement.classList.add("input-focused")
    })

    input.addEventListener("blur", () => {
      input.parentElement.classList.remove("input-focused")
    })
  })

  // Add subtle movement to form on mousemove
  const form = document.querySelector("#contactForm")

  if (form) {
    form.addEventListener("mousemove", (e) => {
      const rect = form.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top

      const centerX = rect.width / 2
      const centerY = rect.height / 2

      const moveX = (x - centerX) / 50
      const moveY = (y - centerY) / 50

      form.style.transform = `translate3d(${moveX}px, ${moveY}px, 0)`
    })

    form.addEventListener("mouseleave", () => {
      form.style.transform = "translate3d(0, 0, 0)"
    })
  }
}
