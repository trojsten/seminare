import 'iconify-icon'
import htmx from 'htmx.org'
import tippy from "tippy.js"
import { Application } from "@hotwired/stimulus"
import { definitions } from 'stimulus:./controllers'

window.htmx = htmx
htmx.on("htmx:load", () => {
    tippy('[data-tippy-content]')
})

const app = Application.start()
app.load(definitions)
