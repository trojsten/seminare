import 'iconify-icon'
import htmx from 'htmx.org'
import tippy from "tippy.js"
import { Application } from "@hotwired/stimulus"

window.htmx = htmx
htmx.on("htmx:load", () => {
    tippy('[data-tippy-content]')
})

const app = Application.start()

import Toggle from "./controllers/toggle";
app.register("toggle", Toggle)
