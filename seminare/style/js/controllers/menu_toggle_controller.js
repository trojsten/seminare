import {Controller} from "@hotwired/stimulus"
import {useClickOutside} from "stimulus-use";

export default class extends Controller {
    static targets = ["openIcon", "closeIcon", "toggle"]

    connect() {
        useClickOutside(this)
    }

    open(event) {
        event.preventDefault()
        this.toggleTarget.classList.remove("hidden")
        this.closeIconTarget.classList.remove("hidden")
        this.openIconTarget.classList.add("hidden")
    }

    close(event) {
        event.preventDefault()
        this.toggleTarget.classList.add("hidden")
        this.closeIconTarget.classList.add("hidden")
        this.openIconTarget.classList.remove("hidden")
    }
}
