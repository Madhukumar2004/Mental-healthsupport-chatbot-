/**
 * MindCare – Mental Health Support Companion
 * Frontend JavaScript Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------
    // 1. Session & State Management
    // -------------------------------------------------------------
    const STORAGE_KEY_SESSION = "mindcare_session_id";
    const STORAGE_KEY_THEME = "mindcare_theme";

    let sessionId = localStorage.getItem(STORAGE_KEY_SESSION);
    if (!sessionId) {
        sessionId = "mc_" + Date.now() + "_" + Math.random().toString(36).substring(2, 9);
        localStorage.setItem(STORAGE_KEY_SESSION, sessionId);
    }

    // DOM Elements
    const chatViewport = document.getElementById("chatViewport");
    const welcomeCard = document.getElementById("welcomeCard");
    const messagesList = document.getElementById("messagesList");
    const typingIndicator = document.getElementById("typingIndicator");
    const chatInput = document.getElementById("chatInput");
    const btnSend = document.getElementById("btnSend");
    const btnClearChat = document.getElementById("btnClearChat");
    const btnThemeToggle = document.getElementById("btnThemeToggle");
    const themeIcon = document.getElementById("themeIcon");

    // Status elements in header
    const statusText = document.querySelector(".status-text");
    const statusDot = document.querySelector(".status-dot");

    // Modals
    const breathingModal = document.getElementById("breathingModal");
    const btnOpenBreathing = document.getElementById("btnOpenBreathing");
    const btnCloseBreathing = document.getElementById("btnCloseBreathing");

    const crisisModal = document.getElementById("crisisModal");
    const btnOpenCrisis = document.getElementById("btnOpenCrisis");
    const btnCloseCrisis = document.getElementById("btnCloseCrisis");

    // Breathing Pacer Elements
    const pacerCircle = document.getElementById("pacerCircle");
    const pacerPhase = document.getElementById("pacerPhase");
    const pacerTimer = document.getElementById("pacerTimer");
    const btnTogglePacer = document.getElementById("btnTogglePacer");
    const modeButtons = document.querySelectorAll(".mode-btn");

    // Mood Elements
    const moodPills = document.querySelectorAll(".mood-pill");
    const moodFeedback = document.getElementById("moodFeedback");

    // -------------------------------------------------------------
    // 2. Theme Initialization
    // -------------------------------------------------------------
    const savedTheme = localStorage.getItem(STORAGE_KEY_THEME) || "dark";
    if (savedTheme === "light") {
        document.body.classList.remove("theme-dark");
        document.body.classList.add("theme-light");
        themeIcon.textContent = "🌙";
    } else {
        document.body.classList.add("theme-dark");
        document.body.classList.remove("theme-light");
        themeIcon.textContent = "☀️";
    }

    btnThemeToggle.addEventListener("click", () => {
        const isDark = document.body.classList.contains("theme-dark");
        if (isDark) {
            document.body.classList.remove("theme-dark");
            document.body.classList.add("theme-light");
            themeIcon.textContent = "🌙";
            localStorage.setItem(STORAGE_KEY_THEME, "light");
        } else {
            document.body.classList.remove("theme-light");
            document.body.classList.add("theme-dark");
            themeIcon.textContent = "☀️";
            localStorage.setItem(STORAGE_KEY_THEME, "dark");
        }
    });

    // -------------------------------------------------------------
    // 3. Mood Indicator Updater
    // -------------------------------------------------------------
    function updateMoodIndicator(mood) {
        if (!mood) return;

        const moodLower = String(mood).toLowerCase();
        const moodIcons = {
            happy: "😊",
            peaceful: "😌",
            anxious: "😰",
            stressed: "🌀",
            overwhelmed: "🌀",
            sad: "🌧️",
            down: "🌧️",
            angry: "😤",
            neutral: "🌿",
            crisis: "🆘",
        };
        const icon = moodIcons[moodLower] || "✨";
        const moodCapitalized = mood.charAt(0).toUpperCase() + mood.slice(1);

        // Update moodFeedback element
        if (moodFeedback) {
            moodFeedback.innerHTML = `<span>Current Mood: <strong>${icon} ${moodCapitalized}</strong></span>`;
            moodFeedback.style.display = "block";
        }

        // Highlight matching mood pill if present
        if (moodPills && moodPills.length > 0) {
            moodPills.forEach(pill => {
                const pillMood = (pill.getAttribute("data-mood") || "").toLowerCase();
                if (
                    pillMood === moodLower ||
                    (moodLower === "happy" && pillMood === "peaceful") ||
                    (moodLower === "happy" && pillMood === "grateful") ||
                    (moodLower === "sad" && pillMood === "down") ||
                    (moodLower === "stressed" && pillMood === "overwhelmed")
                ) {
                    pill.classList.add("active");
                } else {
                    pill.classList.remove("active");
                }
            });
        }

        // Update header status indicator
        if (statusText) {
            if (moodLower === "crisis") {
                statusText.textContent = "Crisis Support • Emergency Helplines (112)";
            } else {
                statusText.textContent = `Mood: ${icon} ${moodCapitalized} • Safe Space`;
            }
        }
        if (statusDot) {
            if (moodLower === "crisis") {
                statusDot.style.backgroundColor = "var(--crisis-red)";
                statusDot.style.boxShadow = "0 0 12px var(--crisis-red)";
            } else {
                statusDot.style.backgroundColor = "";
                statusDot.style.boxShadow = "";
            }
        }
    }

    // -------------------------------------------------------------
    // 4. Chat History Loading on Webpage Open
    // When the webpage opens:
    // 1. Call /history.
    // 2. Retrieve saved conversations.
    // 3. Display them in the chat window in chronological order.
    // 4. Restore the latest detected mood.
    // If there is no history, show the default MindCare welcome message.
    // -------------------------------------------------------------
    async function loadChatHistory() {
        try {
            // 1. Call /history
            const res = await fetch("/history");
            if (!res.ok) {
                if (welcomeCard) welcomeCard.style.display = "block";
                return;
            }

            // 2. Retrieve saved conversations
            const data = await res.json();
            const history = Array.isArray(data) ? data : (data.history || []);

            if (history && history.length > 0) {
                // Hide welcome card when history exists
                if (welcomeCard) welcomeCard.style.display = "none";
                messagesList.innerHTML = "";

                // 3. Display them in chronological order
                history.sort((a, b) => (a.id || 0) - (b.id || 0));

                let latestMood = null;

                history.forEach(item => {
                    const userMsg = item.user_message || (item.sender === "user" ? item.message : null);
                    const botMsg = item.bot_response || (item.sender === "bot" ? item.message : null);
                    const isCrisis = item.mood === "crisis" || Boolean(item.is_crisis);
                    const timestamp = item.created_at || item.timestamp;

                    if (userMsg) {
                        renderMessageBubble("user", userMsg, false, timestamp);
                    }
                    if (botMsg) {
                        renderMessageBubble("bot", botMsg, isCrisis, timestamp);
                    }
                    if (item.mood) {
                        latestMood = item.mood;
                    }
                });

                // 4. Restore the latest detected mood
                if (latestMood) {
                    updateMoodIndicator(latestMood);
                }

                // Scroll to the latest message
                scrollToBottom();
            } else {
                // If there is no history, show the default MindCare welcome message
                if (welcomeCard) welcomeCard.style.display = "block";
                messagesList.innerHTML = "";
            }
        } catch (err) {
            console.warn("Could not load previous chat history:", err);
            if (welcomeCard) welcomeCard.style.display = "block";
        }
    }

    // Load chat history immediately on webpage open
    loadChatHistory();

    // -------------------------------------------------------------
    // 5. Message Rendering & Helpers
    // -------------------------------------------------------------
    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function formatMessageContent(rawText) {
        let safe = escapeHtml(rawText || "");

        // Bold **text**
        safe = safe.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

        // Italic *text*
        safe = safe.replace(/\*(.*?)\*/g, "<em>$1</em>");

        // Bullet points with optional whitespace/indentation (- or •)
        safe = safe.replace(/^\s*[-•]\s+(.*$)/gim, "&bull; $1");

        // Convert URLs to clickable links
        safe = safe.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

        // Preserve linebreaks
        safe = safe.replace(/\n/g, "<br>");
        return safe;
    }

    function formatTimestamp(timestampStr) {
        if (!timestampStr) {
            const now = new Date();
            return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
        try {
            let normalized = String(timestampStr);
            if (normalized.includes(" ") && !normalized.includes("T")) {
                normalized = normalized.replace(" ", "T") + "Z";
            }
            const date = new Date(normalized);
            return isNaN(date.getTime()) ? timestampStr : date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch {
            return "";
        }
    }

    function renderMessageBubble(sender, messageText, isCrisis = false, timestamp = null, suggestions = []) {
        const row = document.createElement("div");
        row.className = `message-row ${sender}`;

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = sender === "user" ? "👤" : "🌿";

        const bubbleWrapper = document.createElement("div");
        bubbleWrapper.className = "message-bubble-wrapper";

        const bubble = document.createElement("div");
        bubble.className = "message-bubble";
        if (isCrisis && sender === "bot") {
            bubble.classList.add("crisis-message-box");
        }

        let innerHTML = "";
        if (isCrisis && sender === "bot") {
            innerHTML += `<div class="crisis-badge">🆘 Immediate Crisis Resources</div>`;
        }
        innerHTML += formatMessageContent(messageText);
        bubble.innerHTML = innerHTML;

        const meta = document.createElement("div");
        meta.className = "message-meta";
        meta.textContent = formatTimestamp(timestamp);

        bubbleWrapper.appendChild(bubble);

        // Suggestions pills for bot
        if (sender === "bot" && suggestions && suggestions.length > 0) {
            const suggestionsContainer = document.createElement("div");
            suggestionsContainer.className = "bot-suggestions";
            suggestions.forEach(pillText => {
                const pill = document.createElement("button");
                pill.type = "button";
                pill.className = "suggestion-chip";
                pill.textContent = pillText;
                pill.addEventListener("click", () => handleSuggestionClick(pillText));
                suggestionsContainer.appendChild(pill);
            });
            bubbleWrapper.appendChild(suggestionsContainer);
        }

        bubbleWrapper.appendChild(meta);

        row.appendChild(avatar);
        row.appendChild(bubbleWrapper);

        messagesList.appendChild(row);
        scrollToBottom();
    }

    function handleSuggestionClick(text) {
        const lower = (text || "").toLowerCase();
        if (lower.includes("breath") || lower.includes("breathe")) {
            openBreathingModal();
        } else if (lower.includes("helpline") || lower.includes("emergency") || lower.includes("crisis")) {
            openCrisisModal();
        } else {
            sendMessage(text);
        }
    }

    function scrollToBottom() {
        requestAnimationFrame(() => {
            chatViewport.scrollTop = chatViewport.scrollHeight;
        });
    }

    function showTyping(show) {
        if (typingIndicator) {
            typingIndicator.style.display = show ? "flex" : "none";
            if (show) scrollToBottom();
        }
    }

    // -------------------------------------------------------------
    // 6. Sending Chat Messages
    // When the user clicks Send:
    // 1. Read the message.
    // 2. Display the user's message immediately.
    // 3. Send it to /chat using fetch().
    // 4. Display the chatbot response.
    // 5. Update the mood indicator.
    // 6. Automatically scroll to the latest message.
    // -------------------------------------------------------------
    let isSending = false;

    async function sendMessage(textToSend) {
        if (isSending) return;

        // 1. Read the message
        const text = (textToSend !== undefined ? textToSend : chatInput.value).trim();
        if (!text) return;

        isSending = true;

        // 2. Display the user's message immediately
        if (welcomeCard && welcomeCard.style.display !== "none") {
            welcomeCard.style.display = "none";
        }
        renderMessageBubble("user", text);

        // Clear input and adjust height
        if (textToSend === undefined) {
            chatInput.value = "";
            chatInput.style.height = "auto";
        }

        // Show typing indicator
        showTyping(true);
        btnSend.disabled = true;

        // 6. Automatically scroll to latest message
        scrollToBottom();

        try {
            // 3. Send it to /chat using fetch()
            const res = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: text,
                    session_id: sessionId
                })
            });

            const data = await res.json();

            if (res.ok && (data.response || data.bot_response)) {
                const botResponse = data.response || data.bot_response;
                const mood = data.mood || "neutral";

                // 4. Display the chatbot response
                renderMessageBubble(
                    "bot",
                    botResponse,
                    Boolean(data.is_crisis),
                    new Date().toISOString(),
                    data.suggested_actions || []
                );

                // 5. Update the mood indicator
                updateMoodIndicator(mood);

                // 6. Automatically scroll to latest message
                scrollToBottom();

                // If crisis detected, open emergency helpline modal automatically
                if (data.is_crisis) {
                    setTimeout(() => {
                        openCrisisModal();
                    }, 700);
                }
            } else {
                const errorMsg = data.error || "I had a brief connection issue. Please feel free to resend your message.";
                renderMessageBubble("bot", errorMsg);
                scrollToBottom();
            }
        } catch (err) {
            console.error("Chat error:", err);
            renderMessageBubble(
                "bot",
                "I'm having trouble connecting right now. Please ensure the server is running."
            );
            scrollToBottom();
        } finally {
            showTyping(false);
            btnSend.disabled = false;
            isSending = false;
        }
    }

    // Event listeners for sending
    btnSend.addEventListener("click", () => sendMessage());

    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-grow textarea
    chatInput.addEventListener("input", () => {
        chatInput.style.height = "auto";
        chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + "px";
    });

    // Starter prompts click handler
    document.querySelectorAll(".quick-prompt-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const prompt = btn.getAttribute("data-prompt");
            if (prompt) sendMessage(prompt);
        });
    });

    // -------------------------------------------------------------
    // 7. Clear Conversation Button -> DELETE /clear
    // -------------------------------------------------------------
    btnClearChat.addEventListener("click", async () => {
        if (confirm("Would you like to clear your current conversation and start fresh?")) {
            try {
                const res = await fetch("/clear", {
                    method: "DELETE",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ session_id: sessionId })
                });

                if (res.ok) {
                    messagesList.innerHTML = "";
                    if (welcomeCard) welcomeCard.style.display = "block";

                    // Reset mood feedback and pills
                    if (moodFeedback) moodFeedback.style.display = "none";
                    moodPills.forEach(p => p.classList.remove("active"));
                    if (statusText) statusText.textContent = "Compassionate Support • Always Here";
                    if (statusDot) {
                        statusDot.style.backgroundColor = "";
                        statusDot.style.boxShadow = "";
                    }
                }
            } catch (err) {
                console.error("Clear chat error:", err);
            }
        }
    });

    // -------------------------------------------------------------
    // 8. Mood Check-in Pills Click Handler
    // -------------------------------------------------------------
    moodPills.forEach(pill => {
        pill.addEventListener("click", async () => {
            const mood = pill.getAttribute("data-mood");
            moodPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");

            try {
                await fetch("/api/mood", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ session_id: sessionId, mood: mood })
                });

                updateMoodIndicator(mood);

                if (mood === "Anxious" || mood === "Overwhelmed") {
                    sendMessage(`I am currently feeling ${mood.toLowerCase()}. Can we take a moment to pause or breathe?`);
                }
            } catch (err) {
                console.error("Mood check-in error:", err);
            }
        });
    });

    // -------------------------------------------------------------
    // 9. Modals (Breathing & Crisis)
    // -------------------------------------------------------------
    function openBreathingModal() {
        breathingModal.style.display = "flex";
    }
    function closeBreathingModal() {
        breathingModal.style.display = "none";
        stopPacer();
    }
    btnOpenBreathing.addEventListener("click", openBreathingModal);
    btnCloseBreathing.addEventListener("click", closeBreathingModal);

    function openCrisisModal() {
        crisisModal.style.display = "flex";
    }
    function closeCrisisModal() {
        crisisModal.style.display = "none";
    }
    btnOpenCrisis.addEventListener("click", openCrisisModal);
    btnCloseCrisis.addEventListener("click", closeCrisisModal);

    // Close on backdrop click
    [breathingModal, crisisModal].forEach(modal => {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                if (modal === breathingModal) closeBreathingModal();
                if (modal === crisisModal) closeCrisisModal();
            }
        });
    });

    // Close on Escape key press
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            if (breathingModal && breathingModal.style.display !== "none") closeBreathingModal();
            if (crisisModal && crisisModal.style.display !== "none") closeCrisisModal();
        }
    });

    // -------------------------------------------------------------
    // 10. Guided Breathing Pacer Logic
    // -------------------------------------------------------------
    let pacerInterval = null;
    let isPacerRunning = false;
    let currentMode = "box"; // "box" or "478"

    const PACER_CONFIG = {
        box: [
            { phase: "Inhale Slowly", duration: 4, action: "inhale" },
            { phase: "Hold Gently", duration: 4, action: "hold" },
            { phase: "Exhale Completely", duration: 4, action: "exhale" },
            { phase: "Rest Calmly", duration: 4, action: "rest" }
        ],
        "478": [
            { phase: "Inhale through Nose", duration: 4, action: "inhale" },
            { phase: "Hold your Breath", duration: 7, action: "hold" },
            { phase: "Exhale whoosh through Mouth", duration: 8, action: "exhale" }
        ]
    };

    let stepIndex = 0;
    let secondsLeft = 4;

    function startPacer() {
        isPacerRunning = true;
        btnTogglePacer.textContent = "Pause Session";
        btnTogglePacer.style.background = "#E53E3E";

        stepIndex = 0;
        executePacerStep();

        pacerInterval = setInterval(() => {
            secondsLeft--;
            pacerTimer.textContent = secondsLeft;

            if (secondsLeft <= 0) {
                stepIndex = (stepIndex + 1) % PACER_CONFIG[currentMode].length;
                executePacerStep();
            }
        }, 1000);
    }

    function executePacerStep() {
        const currentStep = PACER_CONFIG[currentMode][stepIndex];
        secondsLeft = currentStep.duration;
        pacerPhase.textContent = currentStep.phase;
        pacerTimer.textContent = secondsLeft;

        pacerCircle.className = "pacer-circle " + currentStep.action;
    }

    function stopPacer() {
        isPacerRunning = false;
        clearInterval(pacerInterval);
        pacerInterval = null;
        btnTogglePacer.textContent = "Start Session";
        btnTogglePacer.style.background = "";
        pacerPhase.textContent = "Get Ready";
        pacerTimer.textContent = PACER_CONFIG[currentMode][0].duration;
        pacerCircle.className = "pacer-circle";
    }

    btnTogglePacer.addEventListener("click", () => {
        if (isPacerRunning) {
            stopPacer();
        } else {
            startPacer();
        }
    });

    modeButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            modeButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentMode = btn.getAttribute("data-mode");
            stopPacer();
        });
    });
});
