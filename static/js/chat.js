document.addEventListener('DOMContentLoaded', function () {
    // DOM Elements
    const chatMessages = document.getElementById('chatMessages');
    const typingIndicator = document.getElementById('typingIndicator');
    const messageInput = document.getElementById('messageInput');
    const textForm = document.getElementById('textForm');
    const readAloud = document.getElementById('readAloud');
    const languageSelector = document.getElementById('languageSelector');
    const currentLanguage = document.getElementById('currentLanguage');
    const audioPlayer = document.getElementById('audioPlayer');
    const newChatButton = document.getElementById('newChatButton');
    const chatInterface = document.getElementById('chatInterface');

    // Tab elements
    const tabText = document.getElementById('tabText');
    const tabVoice = document.getElementById('tabVoice');
    const tabImage = document.getElementById('tabImage');

    // Input sections
    const inputText = document.getElementById('inputText');
    const inputVoice = document.getElementById('inputVoice');
    const inputImage = document.getElementById('inputImage');
    const inputSoil = document.getElementById('inputSoil');

    // Form elements
    const imageForm = document.getElementById('imageForm');
    const recordButton = document.getElementById('recordButton');
    const micIcon = document.getElementById('micIcon');
    const recordStatus = document.getElementById('recordStatus');

    // Character elements
    const character = document.querySelector('.farmer-assistant');
    const characterContainer = document.getElementById('farmerCharacterContainer');

    // JS Confetti for celebrations
    const jsConfetti = new JSConfetti();

    // Farmer Character instance
    let farmerCharacter = null;



    // Animation for the character
    function animateCharacter() {
        gsap.to(character, {
            y: 10,
            duration: 2,
            repeat: -1,
            yoyo: true,
            ease: "power1.inOut"
        });
    }

    // Call animation if character exists
    if (character) {
        animateCharacter();
    }

    // Get current chat ID from URL
    function getCurrentChatId() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('chat_id');
    }

    // Create new chat
    async function createNewChat() {
        try {
            // Show loading indicator
            const oldButtonText = newChatButton.innerHTML;
            newChatButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating...';
            newChatButton.disabled = true;

            const response = await fetch('/api/create_chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache'
                },
                body: JSON.stringify({
                    language: languageSelector.value
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to create new chat');
            }

            const data = await response.json();

            if (!data.chat_id) {
                throw new Error('No chat ID returned from server');
            }

            // Redirect to the new chat
            window.location.href = `/chat?chat_id=${data.chat_id}&language=${languageSelector.value}`;
        } catch (error) {
            console.error('Error creating new chat:', error);

            // Reset button
            newChatButton.innerHTML = oldButtonText;
            newChatButton.disabled = false;

            // Show error and retry option
            const language = languageSelector.value;
            const errorMessage = language === 'english'
                ? "Failed to create new chat. Please try again."
                : "नया चैट बनाने में विफल। कृपया पुनः प्रयास करें।";

            alert(errorMessage);
        }
    }

    // Load chat history
    async function loadChatHistory() {
        try {
            const response = await fetch('/api/get_chat_history');
            if (!response.ok) {
                throw new Error('Failed to load chat history');
            }
            const data = await response.json();
            updateChatHistoryList(data.chats);
        } catch (error) {
            console.error('Error:', error);
        }
    }

    // Update chat history list in UI
    function updateChatHistoryList(chats) {
        const chatHistoryList = document.getElementById('chatHistoryList');
        chatHistoryList.innerHTML = '';

        const currentChatId = getCurrentChatId(); // Get current chat ID

        chats.forEach((chat, index) => {
            const chatItem = document.createElement('div');
            chatItem.className = `chat-history-item ${chat.id === currentChatId ? 'active' : ''}`;
            chatItem.dataset.chatId = chat.id;

            const lastMessage = chat.messages.length > 0 ? chat.messages[chat.messages.length - 1] : null;
            const preview = lastMessage ? lastMessage.text.substring(0, 50) + (lastMessage.text.length > 50 ? '...' : '') : 'New chat';

            chatItem.innerHTML = `
                <div class="flex justify-between items-start">
                    <div class="cursor-pointer" onclick="window.location.href='/chat?chat_id=${chat.id}&language=${chat.language}'">
                        <div class="font-medium text-gray-900">Chat #${index + 1}</div>
                        <div class="time">${new Date(chat.created_at).toLocaleString()}</div>
                    </div>
                    <div class="flex items-start">
                        <div class="text-sm text-gray-500 mr-2">${chat.language}</div>
                        <button class="delete-chat-btn text-red-500 hover:text-red-700" data-chat-id="${chat.id}">
                            <i class="fa-solid fa-trash-alt"></i>
                        </button>
                    </div>
                </div>
                <div class="preview mt-1">${preview}</div>
            `;

            chatHistoryList.appendChild(chatItem);
        });

        // Add event listeners to delete buttons
        document.querySelectorAll('.delete-chat-btn').forEach(btn => {
            btn.addEventListener('click', function (e) {
                e.stopPropagation(); // Prevent triggering the chat item click
                const chatId = this.getAttribute('data-chat-id');
                deleteChat(chatId);
            });
        });
    }

    // Function to delete a chat
    async function deleteChat(chatId) {
        if (!confirm('Are you sure you want to delete this chat?')) {
            return;
        }

        try {
            const response = await fetch(`/api/delete_chat/${chatId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to delete chat');
            }

            // If we're currently viewing the deleted chat, go to a new chat
            if (getCurrentChatId() === chatId) {
                createNewChat();
            } else {
                // Otherwise just reload the chat history
                loadChatHistory();
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to delete chat. Please try again.');
        }
    }

    // Tab switching
    function switchTab(tab) {
        // Remove active class from all tabs
        [tabText, tabVoice, tabImage].forEach(t => {
            t.classList.remove('active');
            t.classList.add('text-gray-500');
        });

        // Hide all input sections
        [inputText, inputVoice, inputImage, inputSoil].forEach(section => {
            section.classList.add('hidden');
        });

        // Add active class to selected tab
        tab.classList.add('active');
        tab.classList.remove('text-gray-500');

        // Show corresponding input section
        if (tab === tabText) {
            inputText.classList.remove('hidden');
            chatInterface.classList.remove('voice-active');
        }
        else if (tab === tabVoice) {
            inputVoice.classList.remove('hidden');
            chatInterface.classList.add('voice-active');
        }
        else if (tab === tabImage) {
            inputImage.classList.remove('hidden');
            chatInterface.classList.remove('voice-active');
        }
    }

    // Initialize Farmer Character for voice interaction
    function initFarmerCharacter() {
        if (!farmerCharacter && characterContainer) {
            farmerCharacter = new FarmerCharacter('farmerCharacterContainer');
            farmerCharacter.setState(farmerCharacter.states.IDLE);
        }
    }

    // Clean up Farmer Character
    function cleanupFarmerCharacter() {
        if (farmerCharacter) {
            farmerCharacter.dispose();
            farmerCharacter = null;
        }
    }

    // Tab event listeners
    tabText.addEventListener('click', () => switchTab(tabText));
    tabVoice.addEventListener('click', () => switchTab(tabVoice));
    tabImage.addEventListener('click', () => switchTab(tabImage));

    // Auto scroll to bottom of chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Show typing indicator
    function showTypingIndicator() {
        typingIndicator.classList.remove('hidden');
        scrollToBottom();
    }

    // Hide typing indicator
    function hideTypingIndicator() {
        typingIndicator.classList.add('hidden');
    }

    // Message formatting function
    function formatMessage(message) {
        if (!message) return '';

        // If it's already HTML content (has tags), skip formatting
        if (/<img|<br>|<p|<strong|<em|<code/.test(message)) {
            return message;
        }

        // 1. Escape existing HTML tags to prevent injection
        message = message
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // 2. Convert markdown to HTML
        // Bold (**text** or ∗∗text∗∗)
        message = message
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/∗∗(.+?)∗∗/g, '<strong>$1</strong>');

        // Italic (*text* or ∗text∗) — should run after bold
        message = message
            .replace(/\*([^*]+?)\*/g, '<em>$1</em>')
            .replace(/∗([^∗]+?)∗/g, '<em>$1</em>');

        // Inline code (`text`)
        message = message.replace(/`(.+?)`/g, '<code>$1</code>');

        // Line breaks
        message = message.replace(/\n/g, '<br>');

        // Bullet points
        message = message.replace(/^•\s?(.+)/gm, '<br>• $1');

        // Numbered lists
        message = message.replace(/^\d+\.\s?(.+)/gm, '<br>$&');

        return message;
    }

    // Add message to chat
    function addMessage(message, isUser = false, imageUrl = null) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${isUser ? 'justify-end' : ''} mb-4`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = `message-bubble ${isUser ? 'user-message' : 'bot-message'} p-3`;

        // Add image if provided
        if (imageUrl) {
            const imgElement = document.createElement('img');
            imgElement.src = imageUrl;
            imgElement.className = 'rounded-md mb-2';
            imgElement.style.maxWidth = '100%';
            imgElement.style.maxHeight = '200px';
            bubbleDiv.appendChild(imgElement);
        }

        if (isUser) {
            // Check if the message contains HTML
            if (message.includes('<img') || message.includes('<br>')) {
                const formattedDiv = document.createElement('div');
                formattedDiv.className = 'formatted-message';
                formattedDiv.innerHTML = message;
                bubbleDiv.appendChild(formattedDiv);
            } else {
                const textP = document.createElement('p');
                textP.textContent = message;
                bubbleDiv.appendChild(textP);
            }
        } else {
            const formattedDiv = document.createElement('div');
            formattedDiv.className = 'formatted-message';
            formattedDiv.innerHTML = formatMessage(message);
            bubbleDiv.appendChild(formattedDiv);
        }

        // Add timestamp
        const timeP = document.createElement('p');
        timeP.className = `text-xs text-gray-500 ${isUser ? 'text-right' : ''} mt-1`;
        const now = new Date();
        timeP.textContent = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
        bubbleDiv.appendChild(timeP);

        messageDiv.appendChild(bubbleDiv);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Update message handling to include chat_id
    async function handleUserMessage(message) {
        try {
            const chatId = getCurrentChatId();
            if (!chatId) {
                throw new Error('No active chat session');
            }

            addMessage(message, true);

            // Show typing indicator while waiting for response
            showTypingIndicator();

            const response = await fetch('/api/process_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                },
                body: JSON.stringify({
                    message,
                    chat_id: chatId,
                    language: languageSelector.value
                })
            });

            // Hide typing indicator
            hideTypingIndicator();

            const data = await response.json();

            if (!response.ok) {
                console.error('Server error:', data.error);
                throw new Error(data.error || 'Server error');
            }

            if (data.error) {
                console.error('API error:', data.error);
                throw new Error(data.error);
            }

            addMessage(data.response);

            // Only play audio if it was successfully generated
            if (data.audio_url) {
                const audio = new Audio(data.audio_url);
                audio.onerror = () => {
                    console.log('Audio playback failed, continuing without audio');
                };
                await audio.play();
            }

            // Reload chat history to update preview
            loadChatHistory();

        } catch (error) {
            console.error('Error:', error);
            hideTypingIndicator();

            // Get appropriate error message based on language
            const errorMessage = languageSelector.value === 'english'
                ? "I'm sorry, I encountered an error: " + error.message
                : "मुझे खेद है, मुझे एक त्रुटि मिली: " + error.message;

            addMessage(errorMessage);

            // If error is related to chat session, try creating a new one
            if (error.message.includes('session') || error.message.includes('chat_id')) {
                setTimeout(() => {
                    if (confirm('There seems to be an issue with your chat session. Would you like to start a new chat?')) {
                        createNewChat();
                    }
                }, 500);
            }
        }
    }

    // Add text form submission event listener
    textForm.addEventListener('submit', function (e) {
        e.preventDefault(); // Prevent the form from submitting normally

        const message = messageInput.value.trim();
        if (message) {
            handleUserMessage(message);
            messageInput.value = ''; // Clear the input field
        }
    });

    // Update event listeners
    newChatButton.addEventListener('click', createNewChat);

    // Load chat history on page load
    loadChatHistory();

    // Language selector change
    languageSelector.addEventListener('change', function () {
        const currentChatId = getCurrentChatId();
        if (currentChatId) {
            window.location.href = `/chat?chat_id=${currentChatId}&language=${this.value}`;
        } else {
            window.location.href = `/chat?language=${this.value}`;
        }
    });

    // Play audio
    function playAudio(url) {
        console.log("Playing audio", url)
        if (!url) return;

        audioPlayer.src = url;
        audioPlayer.play();
    }


    // Voice recording logic
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

    // If readAloud is changed, play the audio
    // readAloud.addEventListener('change', function() {

    //     playAudio("static/storage/tts_1745416644.mp3")
    // });

    // Start recording
    function startRecording() {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);

                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    sendAudioToServer(audioBlob);
                };

                audioChunks = [];
                mediaRecorder.start();
                isRecording = true;

                // Update UI
                recordButton.classList.add('bg-red-600', 'hover:bg-red-700');
                recordButton.classList.remove('bg-farmer-green-600', 'hover:bg-farmer-green-700');
                micIcon.classList.remove('fa-microphone');
                micIcon.classList.add('fa-stop');
                recordStatus.textContent = "Recording... Click to stop";

                // Add ripple effect
                const ripple = document.createElement('div');
                ripple.className = 'voice-ripple';
                recordButton.appendChild(ripple);

                // Update farmer character to listening state
                if (farmerCharacter) {
                    farmerCharacter.setState(farmerCharacter.states.LISTENING);
                }
            })
            .catch(error => {
                console.error('Error accessing microphone:', error);
                recordStatus.textContent = "Error accessing microphone";
            });
    }

    // Stop recording
    function stopRecording() {
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();
            isRecording = false;

            // Update UI
            recordButton.classList.remove('bg-red-600', 'hover:bg-red-700');
            recordButton.classList.add('bg-farmer-green-600', 'hover:bg-farmer-green-700');
            micIcon.classList.add('fa-microphone');
            micIcon.classList.remove('fa-stop');
            recordStatus.textContent = "Processing audio...";

            // Remove ripple effect
            const ripple = recordButton.querySelector('.voice-ripple');
            if (ripple) ripple.remove();

            // Stop all tracks
            mediaRecorder.stream.getTracks().forEach(track => track.stop());

            // Set character back to idle while processing
            if (farmerCharacter) {
                farmerCharacter.setState(farmerCharacter.states.IDLE);
            }
        }
    }

    // Record button click
    recordButton.addEventListener('click', function () {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    });

    // Send audio to server
    function sendAudioToServer(audioBlob) {
        const formData = new FormData();
        formData.append('audio', audioBlob);
        formData.append('language', languageSelector.value);
        formData.append('chat_id', getCurrentChatId());

        // Show typing indicator
        showTypingIndicator();

        fetch('/api/process_voice', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                console.log("API response", data)
                hideTypingIndicator();

                // Add transcribed text as user message
                if (data.transcribed_text) {
                    addMessage(data.transcribed_text, true);
                }

                // Add bot response
                if (data.response) {
                    addMessage(data.response);
                }

                // Play audio response
                if (data.audio_url) {
                    console.log(data.audio_url)
                    playAudio(data.audio_url);
                }

                recordStatus.textContent = "Press to start recording";

                // Reload chat history
                loadChatHistory();
            })
            .catch(error => {
                console.error('Error:', error);
                hideTypingIndicator();
                recordStatus.textContent = "Error processing audio";
                addMessage("Sorry, there was an error processing your voice. Please try again.");

                // Set character back to idle on error
                if (farmerCharacter) {
                    farmerCharacter.setState(farmerCharacter.states.IDLE);
                }
            });
    }

    // Image form submission
    imageForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const imageFile = document.getElementById('imageInput').files[0];
        if (!imageFile) {
            alert('Please select an image file');
            return;
        }

        // Create a local URL for the selected image
        const imageUrl = URL.createObjectURL(imageFile);

        // Add user message with image
        addMessage("Plant image uploaded for diagnosis", true, imageUrl);

        // Show typing indicator
        showTypingIndicator();

        const formData = new FormData();
        formData.append('image', imageFile);
        formData.append('language', languageSelector.value);
        formData.append('need_audio', readAloud.checked);
        formData.append('chat_id', getCurrentChatId());

        fetch('/api/process_image', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                console.log("API response", data)
                hideTypingIndicator();

                if (data.result) {
                    const resultText = `Plant type: ${data.result.plant_type}\nDisease: ${data.result.disease}\nConfidence: ${(data.result.confidence * 100).toFixed(1)}%\nRecommendation: ${data.result.recommendation}`;

                    // Add text response without the image (image is already in user message)
                    addMessage(resultText);

                    // Show confetti for healthy plants
                    if (data.result.disease.toLowerCase().includes('healthy') || data.result.disease.toLowerCase().includes('स्वस्थ')) {
                        jsConfetti.addConfetti({
                            confettiColors: ['#22c55e', '#eab308', '#4ade80', '#facc15'],
                            confettiRadius: 5,
                            confettiNumber: 100
                        });
                    }

                    // Play audio if available
                    if (data.audio_url) {
                        playAudio(data.audio_url);
                    }
                } else if (data.error) {
                    addMessage(`Error: ${data.error}`);
                }

                // Reset form
                imageForm.reset();

                // Reload chat history
                loadChatHistory();
            })
            .catch(error => {
                console.error('Error:', error);
                hideTypingIndicator();
                addMessage("Sorry, there was an error analyzing your image. Please try again.");
                imageForm.reset();
            });
    });

    // Cleanup when navigating away
    window.addEventListener('beforeunload', function () {
        cleanupFarmerCharacter();
    });

    // Scroll to bottom of chat on page load
    scrollToBottom();
});