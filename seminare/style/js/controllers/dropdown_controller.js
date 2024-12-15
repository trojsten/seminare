import {Controller} from "@hotwired/stimulus"
import {useClickOutside} from "stimulus-use";

export default class extends Controller {
    static targets = ["dropdown", "button"]

    connect() {
        useClickOutside(this)
    }

    toggle() {
        this.dropdownTarget.classList.toggle("hidden")
        this.buttonTarget.setAttribute("aria-expanded", !this.dropdownTarget.classList.contains("hidden"))
    }

    hide() {
        this.dropdownTarget.classList.add("hidden")
        this.buttonTarget.setAttribute("aria-expanded", false)
    }
}
