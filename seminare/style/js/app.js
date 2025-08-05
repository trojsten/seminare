import { Application } from "@hotwired/stimulus"
import htmx from 'htmx.org'
import 'iconify-icon'
import { definitions } from 'stimulus:./controllers'
import tippy from "tippy.js"

window.htmx = htmx
htmx.on("htmx:load", () => {
    tippy('[data-tippy-content]')
    for (const el of document.getElementsByClassName("scroll-to-me")) {
        el.scrollIntoView({ behavior: "smooth", block: "center" })
    }
})

const app = Application.start()
app.load(definitions)
