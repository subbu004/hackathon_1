function toggleChat() {
    const bot = document.getElementById("chatbot");
    bot.style.display = bot.style.display === "flex" ? "none" : "flex";
}

function send() {
    const questionInput = document.getElementById("question");
    const question = questionInput.value;
    if (!question) return;

    // Show user message
    const chatBox = document.getElementById("answer");
    const userMessage = document.createElement("div");
    userMessage.className = "user-message";
    userMessage.textContent = question;
    chatBox.appendChild(userMessage);

    questionInput.value = "";

    // Send POST request
    fetch("/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({question: question})
    })
    .then(res => res.json())
    .then(data => {
        const botMessage = document.createElement("div");
        botMessage.className = "bot-message";
        botMessage.textContent = data.answer;
        chatBox.appendChild(botMessage);
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(err => console.error(err));
}
