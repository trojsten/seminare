self.addEventListener("push", (event) => {
    let payload = {title: "Upozornenie", body: "", url: "/"}
    if (event.data) {
        try {
            payload = {...payload, ...event.data.json()}
        } catch (_error) {
            payload.body = event.data.text()
        }
    }

    event.waitUntil(
        self.registration.showNotification(payload.title, {
            body: payload.body,
            data: {url: payload.url || "/"},
        })
    )
})

self.addEventListener("notificationclick", (event) => {
    event.notification.close()
    const url = (event.notification.data && event.notification.data.url) || "/"

    event.waitUntil(
        self.clients.matchAll({type: "window", includeUncontrolled: true}).then((windowClients) => {
            for (const client of windowClients) {
                if (client.url === url && "focus" in client) {
                    return client.focus()
                }
            }
            if (self.clients.openWindow) {
                return self.clients.openWindow(url)
            }
        })
    )
})
