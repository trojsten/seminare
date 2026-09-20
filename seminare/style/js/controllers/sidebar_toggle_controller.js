import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["sidebar", "button"]

  connect() {
    const key = `sidebar:${this.sidebarTarget.id}`
    const hidden = localStorage.getItem(key) === "hidden"

    this.sidebarTarget.classList.toggle("hidden", hidden)
    this.buttonTarget.classList.toggle("rotate-180", hidden)
  }

  toggle() {
    const hidden = this.sidebarTarget.classList.toggle("hidden")
    this.buttonTarget.classList.toggle("rotate-180", hidden)

    localStorage.setItem(
      `sidebar:${this.sidebarTarget.id}`,
      hidden ? "hidden" : "visible"
    )
  }
}
