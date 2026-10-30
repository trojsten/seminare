import {Controller} from "@hotwired/stimulus"

function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4)
    const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/")
    const raw = atob(base64)
    const output = new Uint8Array(raw.length)
    for (let i = 0; i < raw.length; i++) {
        output[i] = raw.charCodeAt(i)
    }
    return output
}

export default class extends Controller {
    static targets = ["button", "label", "icon"]
    static values = {
        vapidUrl: String,
        subscribeUrl: String,
        unsubscribeUrl: String,
    }

    connect() {
        this.onSubscriptionChanged = (event) => {
            this.subscription = event.detail
            this.failed = false
            this.render()
        }
        window.addEventListener("push-subscription-changed", this.onSubscriptionChanged)
        this.start()
    }

    disconnect() {
        window.removeEventListener("push-subscription-changed", this.onSubscriptionChanged)
    }

    async start() {
        if (!this.supported) return

        this.buttonTarget.hidden = false
        this.buttonTarget.disabled = true
        try {
            this.registration = await navigator.serviceWorker.register("/sw.js")
            await navigator.serviceWorker.ready
            this.subscription = await this.registration.pushManager.getSubscription()
            if (this.subscription && Notification.permission === "granted") {
                await this.save(this.subscription)
            }
        } catch (_error) {
            this.failed = true
        }
        this.render()
    }

    get supported() {
        return window.isSecureContext
            && "serviceWorker" in navigator
            && "PushManager" in window
            && "Notification" in window
    }

    csrf() {
        const input = this.element.querySelector("[name=csrfmiddlewaretoken]")
        return input ? input.value : ""
    }

    render() {
        const button = this.buttonTarget
        button.disabled = false

        if (this.failed) {
            this.labelTarget.textContent = "Push sa nepodarilo zapnúť"
            this.iconTarget.setAttribute("icon", "mdi:bell-off")
            return
        }

        if (Notification.permission === "denied") {
            this.labelTarget.textContent = "Push je zablokovaný"
            this.iconTarget.setAttribute("icon", "mdi:bell-off")
            button.disabled = true
            return
        }

        if (this.subscription) {
            this.labelTarget.textContent = "Vypnúť push upozornenia"
            this.iconTarget.setAttribute("icon", "mdi:bell-check")
            return
        }

        this.labelTarget.textContent = "Povoliť push upozornenia"
        this.iconTarget.setAttribute("icon", "mdi:bell-plus")
    }

    async toggle(event) {
        event.preventDefault()
        if (this.busy || this.buttonTarget.disabled) return

        this.busy = true
        try {
            if (this.subscription) {
                await this.turnOff()
            } else {
                await this.turnOn()
            }
            this.failed = false
            window.dispatchEvent(new CustomEvent("push-subscription-changed", {
                detail: this.subscription,
            }))
        } catch (_error) {
            this.failed = true
        } finally {
            this.busy = false
            this.render()
        }
    }

    async turnOn() {
        const permission = await Notification.requestPermission()
        if (permission !== "granted") return

        if (!this.registration) {
            this.registration = await navigator.serviceWorker.register("/sw.js")
        }
        await navigator.serviceWorker.ready

        const response = await fetch(this.vapidUrlValue, {credentials: "same-origin"})
        if (!response.ok) throw new Error("missing vapid key")
        const {publicKey} = await response.json()

        this.subscription = await this.registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(publicKey),
        })
        await this.save(this.subscription)
    }

    async turnOff() {
        const endpoint = this.subscription.endpoint
        await this.subscription.unsubscribe()
        this.subscription = null
        await fetch(this.unsubscribeUrlValue, {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": this.csrf(),
            },
            body: JSON.stringify({endpoint}),
        })
    }

    async save(subscription) {
        const response = await fetch(this.subscribeUrlValue, {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": this.csrf(),
            },
            body: JSON.stringify(subscription),
        })
        if (!response.ok) throw new Error("subscribe failed")
    }
}
