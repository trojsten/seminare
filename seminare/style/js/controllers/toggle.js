import {Controller} from "@hotwired/stimulus"

export default class extends Controller {
    static targets = ["toggle"]
    static classes = ["toggle"]

    click() {
        this.toggleTarget.classList.toggle(this.toggleClass)
    }
}
