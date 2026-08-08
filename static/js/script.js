/**
 * FAQBot - Interactive SaaS Chatbot Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const chatMessages = document.getElementById('chatMessages');
  const chatForm = document.getElementById('chatForm');
  const userInput = document.getElementById('userInput');
  const sendBtn = document.getElementById('sendBtn');
  const micBtn = document.getElementById('micBtn');
  const themeToggle = document.getElementById('themeToggle');
  const adminToggle = document.getElementById('adminToggle');
  const adminModal = document.getElementById('adminModal');
  const closeModal = document.getElementById('closeModal');
  const adminForm = document.getElementById('adminForm');
  const faqListContainer = document.getElementById('faqListContainer');
  const categoryFilter = document.getElementById('categoryFilter');
  const formFaqId = document.getElementById('formFaqId');
  const faqQuestionInput = document.getElementById('faqQuestionInput');
  const faqAnswerInput = document.getElementById('faqAnswerInput');
  const faqCategoryInput = document.getElementById('faqCategoryInput');
  const formSubmitBtn = document.getElementById('formSubmitBtn');

  let isSpeechRecognizing = false;
  let recognition = null;
  let currentTheme = localStorage.getItem('theme') || 'light';

  // Initialize Theme
  setTheme(currentTheme);

  // Initialize Speech Recognition if supported
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      userInput.value = transcript;
      toggleMic(false);
      userInput.focus();
    };

    recognition.onerror = () => {
      toggleMic(false);
    };

    recognition.onend = () => {
      toggleMic(false);
    };
  } else {
    if (micBtn) micBtn.style.display = 'none';
  }

  // ================= EVENT LISTENERS =================

  // Theme Toggle Listener
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      currentTheme = currentTheme === 'light' ? 'dark' : 'light';
      setTheme(currentTheme);
    });
  }

  // Submit Form Listener
  if (chatForm) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      handleSendMessage();
    });
  }

  // Mic Button Listener
  if (micBtn) {
    micBtn.addEventListener('click', () => {
      if (!recognition) return;
      if (isSpeechRecognizing) {
        recognition.stop();
        toggleMic(false);
      } else {
        recognition.start();
        toggleMic(true);
      }
    });
  }

  // Admin Modal Listeners
  if (adminToggle) {
    adminToggle.addEventListener('click', () => {
      openAdminModal();
    });
  }

  if (closeModal) {
    closeModal.addEventListener('click', () => {
      closeAdminModal();
    });
  }

  if (adminForm) {
    adminForm.addEventListener('submit', (e) => {
      e.preventDefault();
      handleSaveFaq();
    });
  }

  if (categoryFilter) {
    categoryFilter.addEventListener('change', () => {
      loadAdminFaqs(categoryFilter.value);
    });
  }

  // Delegate suggestion chip click events globally
  document.addEventListener('click', (e) => {
    const chip = e.target.closest('.suggestion-chip');
    if (chip) {
      const questionText = chip.getAttribute('data-question') || chip.innerText.trim();
      if (questionText) {
        userInput.value = questionText;
        handleSendMessage();
      }
    }
  });

  // ================= CORE FUNCTIONS =================

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    if (themeToggle) {
      themeToggle.innerHTML = theme === 'dark' 
        ? '<i class="fas fa-sun"></i>' 
        : '<i class="fas fa-moon"></i>';
    }
  }

  function toggleMic(listening) {
    isSpeechRecognizing = listening;
    if (micBtn) {
      if (listening) {
        micBtn.classList.add('listening');
        micBtn.title = "Listening...";
      } else {
        micBtn.classList.remove('listening');
        micBtn.title = "Voice Input";
      }
    }
  }

  function handleSendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    // Add user message to UI
    appendMessage(text, 'user');
    userInput.value = '';
    sendBtn.disabled = true;

    // Show Typing Indicator
    const typingId = showTypingIndicator();

    // Call Backend API
    fetch('/ask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ question: text })
    })
    .then(response => response.json())
    .then(data => {
      removeTypingIndicator(typingId);
      sendBtn.disabled = false;

      if (data.status === 'success') {
        appendMessage(data.answer, 'bot', {
          similarity: data.similarity,
          faqId: data.faq ? data.faq.id : null,
          question: text
        });

        // Render suggested questions
        if (data.suggestions && data.suggestions.length > 0) {
          renderSuggestions(data.suggestions);
        }
      } else {
        appendMessage(data.message || 'Something went wrong. Please try again.', 'bot');
      }
    })
    .catch(error => {
      console.error('Error asking FAQBot:', error);
      removeTypingIndicator(typingId);
      sendBtn.disabled = false;
      appendMessage('Unable to connect to FAQBot server. Please check your network connection.', 'bot');
    });
  }

  function appendMessage(text, sender, meta = {}) {
    const wrapper = document.createElement('div');
    wrapper.className = `message-wrapper ${sender}`;

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    if (sender === 'user') {
      wrapper.innerHTML = `
        <div class="message-bubble">${escapeHtml(text)}</div>
        <div class="message-meta">${timeStr}</div>
      `;
    } else {
      let metaHtml = `${timeStr}`;
      if (meta.similarity && meta.similarity > 0) {
        metaHtml += `<span class="similarity-badge">Match ${(meta.similarity * 100).toFixed(0)}%</span>`;
      }

      wrapper.innerHTML = `
        <div class="message-bubble">${escapeHtml(text)}</div>
        <div class="message-meta">${metaHtml}</div>
        <div class="bot-actions">
          <button class="action-chip tts-btn" title="Listen Answer" data-text="${escapeHtml(text)}">
            <i class="fas fa-volume-up"></i>
          </button>
          <button class="action-chip copy-btn" title="Copy Text" data-text="${escapeHtml(text)}">
            <i class="far fa-copy"></i>
          </button>
          <button class="action-chip feedback-btn" data-helpful="true" data-question="${escapeHtml(meta.question || '')}" data-faq="${meta.faqId || ''}" title="Helpful">
            <i class="far fa-thumbs-up"></i>
          </button>
          <button class="action-chip feedback-btn" data-helpful="false" data-question="${escapeHtml(meta.question || '')}" data-faq="${meta.faqId || ''}" title="Not Helpful">
            <i class="far fa-thumbs-down"></i>
          </button>
        </div>
      `;
    }

    chatMessages.appendChild(wrapper);
    scrollToBottom();

    // Attach button handlers for TTS, Copy, Feedback
    if (sender === 'bot') {
      const copyBtn = wrapper.querySelector('.copy-btn');
      if (copyBtn) {
        copyBtn.addEventListener('click', () => {
          navigator.clipboard.writeText(text).then(() => {
            copyBtn.innerHTML = '<i class="fas fa-check"></i>';
            setTimeout(() => {
              copyBtn.innerHTML = '<i class="far fa-copy"></i>';
            }, 2000);
          });
        });
      }

      const ttsBtn = wrapper.querySelector('.tts-btn');
      if (ttsBtn) {
        ttsBtn.addEventListener('click', () => {
          speakText(text);
        });
      }

      const feedbackBtns = wrapper.querySelectorAll('.feedback-btn');
      feedbackBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const isHelpful = btn.getAttribute('data-helpful') === 'true';
          const q = btn.getAttribute('data-question');
          const fid = btn.getAttribute('data-faq');

          sendFeedback(q, isHelpful, fid);

          feedbackBtns.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
        });
      });
    }
  }

  function showTypingIndicator() {
    const id = 'typing-' + Date.now();
    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper bot';
    wrapper.id = id;

    wrapper.innerHTML = `
      <div class="typing-indicator">
        <span style="font-size: 0.8rem; color: var(--text-muted); margin-right: 4px;">FAQBot typing</span>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    `;

    chatMessages.appendChild(wrapper);
    scrollToBottom();
    return id;
  }

  function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function renderSuggestions(suggestions) {
    if (!suggestions || suggestions.length === 0) return;

    const container = document.createElement('div');
    container.className = 'suggestions-container';

    suggestions.slice(0, 4).forEach(s => {
      const chip = document.createElement('button');
      chip.className = 'suggestion-chip';
      chip.setAttribute('data-question', s);
      chip.innerHTML = `<i class="far fa-question-circle"></i> ${escapeHtml(s)}`;
      container.appendChild(chip);
    });

    chatMessages.appendChild(container);
    scrollToBottom();
  }

  function sendFeedback(question, helpful, faqId) {
    fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: question,
        helpful: helpful,
        faq_id: faqId ? parseInt(faqId) : null
      })
    }).catch(err => console.error('Feedback error:', err));
  }

  function speakText(text) {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;")
              .replace(/</g, "&lt;")
              .replace(/>/g, "&gt;")
              .replace(/"/g, "&quot;")
              .replace(/'/g, "&#039;");
  }

  // ================= ADMIN MODAL LOGIC =================

  function openAdminModal() {
    adminModal.classList.add('active');
    loadAdminCategories();
    loadAdminFaqs();
  }

  function closeAdminModal() {
    adminModal.classList.remove('active');
    resetAdminForm();
  }

  function loadAdminCategories() {
    fetch('/api/categories')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success' && categoryFilter) {
          categoryFilter.innerHTML = '<option value="ALL">All Categories</option>';
          data.categories.forEach(cat => {
            categoryFilter.innerHTML += `<option value="${cat}">${cat}</option>`;
          });
        }
      });
  }

  function loadAdminFaqs(filterCat = 'ALL') {
    fetch('/api/faqs')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success' && faqListContainer) {
          faqListContainer.innerHTML = '';
          let faqs = data.faqs;
          if (filterCat !== 'ALL') {
            faqs = faqs.filter(f => f.category === filterCat);
          }

          if (faqs.length === 0) {
            faqListContainer.innerHTML = '<p style="text-align: center; color: var(--text-muted); padding: 1rem;">No FAQs found.</p>';
            return;
          }

          faqs.forEach(faq => {
            const card = document.createElement('div');
            card.className = 'faq-item-card';
            card.innerHTML = `
              <div class="faq-item-content">
                <span class="category-tag">${escapeHtml(faq.category)}</span>
                <h4>${escapeHtml(faq.question)}</h4>
                <p>${escapeHtml(faq.answer)}</p>
              </div>
              <div class="faq-actions">
                <button class="icon-btn edit-faq-btn" data-id="${faq.id}" title="Edit FAQ">
                  <i class="fas fa-edit"></i>
                </button>
                <button class="icon-btn delete-faq-btn" data-id="${faq.id}" title="Delete FAQ" style="color: var(--accent-red);">
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            `;

            card.querySelector('.edit-faq-btn').addEventListener('click', () => {
              editFaqForm(faq);
            });

            card.querySelector('.delete-faq-btn').addEventListener('click', () => {
              if (confirm(`Delete FAQ: "${faq.question}"?`)) {
                deleteFaqItem(faq.id);
              }
            });

            faqListContainer.appendChild(card);
          });
        }
      });
  }

  function handleSaveFaq() {
    const id = formFaqId.value;
    const question = faqQuestionInput.value.trim();
    const answer = faqAnswerInput.value.trim();
    const category = faqCategoryInput.value.trim() || 'General';

    if (!question || !answer) {
      alert('Please fill in both Question and Answer.');
      return;
    }

    const payload = { question, answer, category };
    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/faqs/${id}` : '/api/faqs';

    fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success') {
        resetAdminForm();
        loadAdminFaqs(categoryFilter ? categoryFilter.value : 'ALL');
        loadAdminCategories();
      } else {
        alert(data.message || 'Failed to save FAQ.');
      }
    });
  }

  function editFaqForm(faq) {
    formFaqId.value = faq.id;
    faqQuestionInput.value = faq.question;
    faqAnswerInput.value = faq.answer;
    faqCategoryInput.value = faq.category;
    formSubmitBtn.innerText = 'Update FAQ';
  }

  function resetAdminForm() {
    formFaqId.value = '';
    adminForm.reset();
    formSubmitBtn.innerText = 'Add FAQ';
  }

  function deleteFaqItem(id) {
    fetch(`/api/faqs/${id}`, { method: 'DELETE' })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          loadAdminFaqs(categoryFilter ? categoryFilter.value : 'ALL');
        } else {
          alert('Failed to delete FAQ.');
        }
      });
  }
});
