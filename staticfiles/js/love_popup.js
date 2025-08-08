// static/js/love_popup.js
function showLoveMessage() {
    const messages = [
        "أنتَ نور حياتي وسعادتي الأبدية.",
        "قلبي ينبض بحبك كل يوم.",
        "معك، أشعر أنني في الجنة.",
        "حبك هو اللحن الذي يعزف في قلبي.",
        "أنتَ حلمي الذي تحقق."
    ];
    const randomMessage = messages[Math.floor(Math.random() * messages.length)];
    document.getElementById('loveMessage').innerText = randomMessage;
    const modal = new bootstrap.Modal(document.getElementById('loveModal'));
    modal.show();
}