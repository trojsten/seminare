import {Controller} from "@hotwired/stimulus"
import {useIntersection} from "stimulus-use";

export default class extends Controller {
    static targets = ["cta", "submitForm"]

    connect() {
        useIntersection(this, {
            element: this.submitFormTarget,
        })
    }

    appear() {
        this.ctaTarget.classList.add("hidden")
    }

    disappear() {
        this.ctaTarget.classList.remove("hidden")
    }

    scroll() {
        this.submitFormTarget.scrollIntoView({behavior: "smooth"})
    }
}
