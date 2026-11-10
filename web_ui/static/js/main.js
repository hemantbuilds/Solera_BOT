document.addEventListener('DOMContentLoaded', function() {
    const socket = io();

    const chatMessages = document.getElementById('chat-messages');
    const thinkingDiv = document.getElementById('thinking');

    socket.on('transcribed', function(data) {
        appendMessage(data.message, 'user');
        thinkingDiv.style.display = 'block';
    });

    socket.on('final_response', function(data) {
        thinkingDiv.style.display = 'none';
        appendMessage(data.message, 'bot');
    });

    socket.on('finished', function(data) {
        thinkingDiv.style.display = 'none';
    });

    function appendMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
