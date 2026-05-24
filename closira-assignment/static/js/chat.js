/**
 * Closira Chat Interface JavaScript
 * Handles real-time conversation, state updates, and UI interactions
 */

// DOM Elements
const messagesContainer = document.getElementById('messagesContainer');
const messageForm = document.getElementById('messageForm');
const messageInput = document.getElementById('messageInput');
const resetBtn = document.getElementById('resetBtn');
const statsBtn = document.getElementById('statsBtn');
const statusIndicator = document.getElementById('statusIndicator');
const messageCount = document.getElementById('messageCount');
const unansweredCount = document.getElementById('unansweredCount');
const businessType = document.getElementById('businessType');
const teamSize = document.getElementById('teamSize');
const toolsUsed = document.getElementById('toolsUsed');
const leadQuality = document.getElementById('leadQuality');
const escalationSection = document.getElementById('escalationSection');
const qualificationIndicator = document.getElementById('qualificationIndicator');
const statsModal = document.getElementById('statsModal');
const completionModal = document.getElementById('completionModal');

// State
let isLoading = false;
let currentMessageType = 'message';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    messageForm.addEventListener('submit', handleSendMessage);
    resetBtn.addEventListener('click', handleReset);
    statsBtn.addEventListener('click', showStats);
    updateState();
});

/**
 * Send message to backend
 */
async function handleSendMessage(e) {
    e.preventDefault();

    const message = messageInput.value.trim();
    if (!message || isLoading) return;

    // Add customer message to UI
    addMessageToUI(message, 'customer');
    messageInput.value = '';
    messageInput.disabled = true;
    isLoading = true;

    try {
        // Send to backend
        const response = await fetch('/api/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                type: currentMessageType
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            addMessageToUI(`Error: ${data.error}`, 'assistant');
        } else {
            // Add assistant response
            addMessageToUI(data.message, 'assistant');

            // Handle different statuses
            if (data.status === 'qualification') {
                currentMessageType = 'qualification_answer';
                showQualificationIndicator(data.question_number);
                renderQualificationOptions(data.options || []);
            } else if (data.status === 'completed') {
                currentMessageType = 'message';
                hideQualificationIndicator();
                showCompletionModal(data);
                messageInput.disabled = true;
            } else {
                currentMessageType = 'message';
                hideQualificationIndicator();
            }

            // Update UI state
            updateState();
        }
    } catch (error) {
        console.error('Error:', error);
        addMessageToUI('Sorry, I encountered an error. Please try again.', 'assistant');
    } finally {
        if (!document.getElementById('qualificationOptions').contains(document.activeElement)) {
            messageInput.disabled = document.getElementById('qualificationOptions').style.display === 'block';
        }
        isLoading = false;
        messageInput.focus();
    }
}

/**
 * Render multiple-choice qualification options in the chat UI.
 */
function renderQualificationOptions(options) {
    const optionsContainer = document.getElementById('qualificationOptions');
    optionsContainer.innerHTML = '';

    if (!options || options.length === 0) {
        optionsContainer.style.display = 'none';
        messageInput.disabled = false;
        return;
    }

    options.forEach((option) => {
        const button = document.createElement('button');
        button.className = 'btn btn-secondary qualification-option';
        button.type = 'button';
        button.textContent = option;
        button.addEventListener('click', () => submitQualificationAnswer(option));
        optionsContainer.appendChild(button);
    });

    optionsContainer.style.display = 'grid';
    messageInput.disabled = true;
}

function submitQualificationAnswer(answer) {
    addMessageToUI(answer, 'customer');
    sendQualificationAnswer(answer);
}

async function sendQualificationAnswer(answer) {
    if (isLoading) return;
    isLoading = true;
    messageInput.disabled = true;

    try {
        const response = await fetch('/api/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: answer,
                type: 'qualification_answer'
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.error) {
            addMessageToUI(`Error: ${data.error}`, 'assistant');
        } else {
            addMessageToUI(data.message, 'assistant');
            if (data.status === 'qualification') {
                currentMessageType = 'qualification_answer';
                showQualificationIndicator(data.question_number);
                renderQualificationOptions(data.options || []);
            } else if (data.status === 'completed') {
                currentMessageType = 'message';
                hideQualificationIndicator();
                showCompletionModal(data);
            } else {
                currentMessageType = 'message';
                hideQualificationIndicator();
            }
            updateState();
        }
    } catch (error) {
        console.error('Error:', error);
        addMessageToUI('Sorry, I encountered an error. Please try again.', 'assistant');
    } finally {
        isLoading = false;
        messageInput.disabled = document.getElementById('qualificationOptions').style.display === 'grid';
        messageInput.focus();
    }
}

/**
 * Add message to chat UI
 */
function addMessageToUI(text, role) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;

    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Remove welcome message if exists
    const welcomeMessage = messagesContainer.querySelector('.welcome-message');
    if (welcomeMessage && messagesContainer.children.length > 1) {
        welcomeMessage.remove();
    }
}

/**
 * Update conversation state from backend
 */
async function updateState() {
    try {
        const response = await fetch('/api/state');
        const data = await response.json();

        // Update counters
        messageCount.textContent = data.message_count;
        unansweredCount.textContent = data.unanswered_count;

        // Update lead data
        businessType.textContent = data.lead_data.business_type || '-';
        teamSize.textContent = data.lead_data.team_size || '-';
        toolsUsed.textContent = data.lead_data.current_tools || '-';

        // Update lead quality badge
        if (data.lead_data.lead_quality) {
            leadQuality.textContent = data.lead_data.lead_quality;
            leadQuality.className = `badge ${data.lead_data.lead_quality.toLowerCase()}`;
        }

        // Update escalation status
        if (data.escalated) {
            statusIndicator.textContent = 'Escalated';
            statusIndicator.classList.add('escalated');
            escalationSection.style.display = 'block';

            // Fetch escalation details
            const escalationResponse = await fetch('/api/escalation-info');
            const escalationData = await escalationResponse.json();

            if (escalationData.escalated) {
                document.getElementById('escalationReason').textContent = escalationData.reason_description;
                document.getElementById('escalationConfidence').textContent = (escalationData.confidence * 100).toFixed(0) + '%';
                document.getElementById('assignedQueue').textContent = escalationData.assigned_queue;
            }
        } else {
            statusIndicator.textContent = 'Active';
            statusIndicator.classList.remove('escalated');
            escalationSection.style.display = 'none';
        }
    } catch (error) {
        console.error('Error updating state:', error);
    }
}

/**
 * Show qualification indicator
 */
function showQualificationIndicator(questionNum) {
    document.getElementById('questionNum').textContent = questionNum;
    qualificationIndicator.style.display = 'block';
}

/**
 * Hide qualification indicator
 */
function hideQualificationIndicator() {
    qualificationIndicator.style.display = 'none';
    const optionsContainer = document.getElementById('qualificationOptions');
    optionsContainer.innerHTML = '';
    optionsContainer.style.display = 'none';
    messageInput.disabled = false;
}

/**
 * Show completion modal with summary
 */
function showCompletionModal(data) {
    const summary = data.summary || {};
    const content = document.getElementById('completionContent');

    let html = '<div class="alert alert-success">✓ Conversation Completed</div>';

    // Customer Intent
    if (summary.customer_intent) {
        html += `
            <div class="summary-section">
                <h3>Customer Intent</h3>
                <p>${summary.customer_intent}</p>
            </div>
        `;
    }

    // Key Details
    if (summary.key_details && summary.key_details.length > 0) {
        html += `
            <div class="summary-section">
                <h3>Key Details</h3>
                <ul>
                    ${summary.key_details.map(detail => `<li>${detail}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // SOP Gaps
    if (summary.sop_gaps && summary.sop_gaps.length > 0) {
        html += `
            <div class="summary-section">
                <h3>Information Gaps</h3>
                <ul>
                    ${summary.sop_gaps.map(gap => `<li>${gap}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // Recommended Action
    if (summary.recommended_next_action) {
        html += `
            <div class="summary-section">
                <h3>Recommended Action</h3>
                <p>${summary.recommended_next_action}</p>
            </div>
        `;
    }

    // Assigned To
    if (summary.assigned_to) {
        html += `
            <div class="summary-section">
                <h3>Assigned To</h3>
                <p><strong>${summary.assigned_to}</strong></p>
            </div>
        `;
    }

    content.innerHTML = html;
    completionModal.style.display = 'flex';
}

/**
 * Close completion modal
 */
function closeCompletionModal() {
    completionModal.style.display = 'none';
}

/**
 * Start new conversation
 */
async function newConversation() {
    closeCompletionModal();
    
    try {
        await fetch('/api/reset', { method: 'POST' });
    } catch (error) {
        console.error('Error resetting:', error);
    }

    // Reset UI
    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <h2>Welcome to Closira Support</h2>
            <p>Hi! I'm here to help. Ask me about our services, pricing, or anything else.</p>
        </div>
    `;
    messageInput.value = '';
    messageInput.disabled = false;
    currentMessageType = 'message';
    isLoading = false;
    hideQualificationIndicator();
    updateState();
    messageInput.focus();
}

/**
 * Reset conversation
 */
async function handleReset() {
    if (confirm('Start a new conversation? Current conversation will be lost.')) {
        await newConversation();
    }
}

/**
 * Show stats modal
 */
async function showStats() {
    try {
        const stateResponse = await fetch('/api/state');
        const stateData = await stateResponse.json();

        const conversationResponse = await fetch('/api/conversation');
        const conversationData = await conversationResponse.json();

        const content = document.getElementById('statsContent');
        
        let html = '<div class="stats-grid">';
        html += `
            <div class="stat-card">
                <h4>Total Messages</h4>
                <div class="value">${stateData.message_count}</div>
            </div>
            <div class="stat-card">
                <h4>Unanswered Questions</h4>
                <div class="value">${stateData.unanswered_count}</div>
            </div>
        `;

        if (stateData.lead_data.business_type) {
            html += `
                <div class="stat-card">
                    <h4>Business Type</h4>
                    <div class="value" style="font-size: 1rem;">${stateData.lead_data.business_type}</div>
                </div>
            `;
        }

        if (stateData.lead_data.team_size) {
            html += `
                <div class="stat-card">
                    <h4>Team Size</h4>
                    <div class="value">${stateData.lead_data.team_size}</div>
                </div>
            `;
        }

        if (stateData.lead_data.lead_quality) {
            html += `
                <div class="stat-card">
                    <h4>Lead Quality</h4>
                    <div class="value" style="font-size: 1rem;">${stateData.lead_data.lead_quality}</div>
                </div>
            `;
        }

        html += '</div>';

        // Conversation flow
        if (conversationData.messages.length > 0) {
            html += '<div class="summary-section"><h3>Conversation Flow</h3>';
            html += conversationData.messages.map((msg, i) => {
                const role = msg.role.charAt(0).toUpperCase() + msg.role.slice(1);
                return `<p><strong>${role}:</strong> ${msg.content.substring(0, 100)}${msg.content.length > 100 ? '...' : ''}</p>`;
            }).join('');
            html += '</div>';
        }

        content.innerHTML = html;
        statsModal.style.display = 'flex';
    } catch (error) {
        console.error('Error showing stats:', error);
    }
}

/**
 * Close modal
 */
function closeModal() {
    statsModal.style.display = 'none';
}

/**
 * Close modal when clicking outside
 */
window.addEventListener('click', (e) => {
    if (e.target === statsModal) {
        closeModal();
    }
    if (e.target === completionModal) {
        closeCompletionModal();
    }
});

/**
 * Focus input on page load
 */
window.addEventListener('load', () => {
    messageInput.focus();
});
