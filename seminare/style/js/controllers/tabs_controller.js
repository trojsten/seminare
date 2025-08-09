import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["content", "button"]
  static values = { active: String }

  connect() {
    this.showTab(this.activeValue || this.buttonTargets[0].dataset.tab)
  }

  switch(event) {
    const tab = event.currentTarget.dataset.tab
    this.showTab(tab)
  }

  showTab(tab) {
    // Hide all content, show selected
    this.contentTargets.forEach(el => el.classList.add('hidden'))
    this.contentTargets.find(el => el.dataset.tab === tab)?.classList.remove('hidden')

    // Update button states
    this.buttonTargets.forEach(btn => btn.classList.remove('active'))
    this.buttonTargets.find(btn => btn.dataset.tab === tab)?.classList.add('active')

    this.activeValue = tab
  }
}
