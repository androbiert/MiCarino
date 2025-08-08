self.addEventListener('push', function(event) {
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: '/static/images/notification-icon.png', // Add an icon in your static folder
        badge: '/static/images/badge.png', // Optional badge
        data: {
            url: data.url // URL to open when notification is clicked
        }
    };
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});