function parseMessage(message) {
    return message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');

    // Fetch chat history
    fetch('/history')
        .then(response => response.json())
        .then(data => {
            data.forEach(item => {
                const messageElement = document.createElement('div');
                messageElement.classList.add('chat-message');
                messageElement.innerHTML = parseMessage(item.message);
                chatBox.appendChild(messageElement);
            });
            chatBox.scrollTop = chatBox.scrollHeight;
        });
});

document.getElementById('chat-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const chatBox = document.getElementById('chat-box');
    const chatInput = document.getElementById('chat-input');
    const imageInput = document.getElementById('image-input');
    const message = chatInput.value.trim();
    const file = imageInput.files[0];

    if (message !== '' || file) {
        const userMessageElement = document.createElement('div');
        userMessageElement.classList.add('chat-message');
        userMessageElement.innerHTML = parseMessage(message);
        chatBox.appendChild(userMessageElement);

        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const imageElement = document.createElement('img');
                imageElement.src = e.target.result;
                imageElement.classList.add('chat-image');
                chatBox.appendChild(imageElement);
            };
            reader.readAsDataURL(file);
        }

        const thinkingMessageElement = document.createElement('div');
        thinkingMessageElement.classList.add('chat-message');
        thinkingMessageElement.innerHTML = 'Thinking<span class="thinking-animation"><span class="dot"></span><span class="dot"></span><span class="dot"></span></span>';
        chatBox.appendChild(thinkingMessageElement);
        chatBox.scrollTop = chatBox.scrollHeight;

        const formData = new FormData();
        formData.append('message', message);
        if (file) {
            formData.append('image', file);
        }

        fetch(file ? '/upload' : '/chat', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            chatBox.removeChild(thinkingMessageElement);

            if (data.image_url) {
                const imageElement = document.createElement('img');
                imageElement.src = data.image_url;
                imageElement.classList.add('chat-image');
                chatBox.appendChild(imageElement);
            }

            const botMessageElement = document.createElement('div');
            botMessageElement.classList.add('chat-message');
            botMessageElement.innerHTML = parseMessage(data.response);
            chatBox.appendChild(botMessageElement);
            chatBox.scrollTop = chatBox.scrollHeight;
        });

        chatInput.value = '';
        imageInput.value = '';
    }
});

document.getElementById('attachment-button').addEventListener('click', function() {
    const dropdown = document.getElementById('attachment-dropdown');
    dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
});

document.getElementById('upload-button').addEventListener('click', function() {
    document.getElementById('image-input').click();
});

document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('attachment-dropdown');
    if (!event.target.closest('.attachment-container')) {
        dropdown.style.display = 'none';
    }
});
