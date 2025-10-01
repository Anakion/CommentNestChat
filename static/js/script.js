// ----------------------------------------
// DOM элементы
const statusEl = document.getElementById("status");
const commentsEl = document.getElementById("comments");
const userInput = document.getElementById("userName");
const emailInput = document.getElementById("userEmail");
const textInput = document.getElementById("commentText");
const sendBtn = document.getElementById("sendButton");
const parentIdInput = document.getElementById("parentId");
const cancelReplyBtn = document.getElementById("cancelReply");
const newCommentForm = document.getElementById("newCommentForm");

const protocol = location.protocol === "https:" ? "wss" : "ws";
let ws;
let heartbeatInterval;
let currentReplyId = null;

// ----------------------------------------
// Рендер комментариев с возможностью раскрытия
function renderComments(comments) {
  commentsEl.innerHTML = "";

  if (comments.length === 0) {
    commentsEl.innerHTML = `
      <div class="no-comments">
        <h3>💬 Пока нет комментариев</h3>
        <p>Будьте первым, кто оставит комментарий!</p>
      </div>
    `;
    return;
  }

  comments.forEach(comment => {
    if (!comment.parent_id) {
      renderComment(comment, commentsEl);
    }
  });
}

function renderComment(comment, container, level = 0) {
  const commentEl = document.createElement('div');
  commentEl.className = 'comment';
  commentEl.setAttribute('data-id', comment.id);
  commentEl.setAttribute('data-level', level);

  const hasReplies = comment.replies && comment.replies.length > 0;
  const replyCount = hasReplies ? comment.replies.length : 0;

  commentEl.innerHTML = `
    <div class="comment-header">
      <div class="user-info">
        <span class="user-name">${escapeHtml(comment.user_name)}</span>
        <span class="user-email">${escapeHtml(comment.email)}</span>
      </div>
      <div class="comment-date">${formatDate(comment.created_at)}</div>
    </div>
    <div class="comment-text">${escapeHtml(comment.text)}</div>
    <div class="comment-actions">
      <button class="reply-btn" data-id="${comment.id}">
        <span>💬 Ответить</span>
      </button>
      ${hasReplies ? `
        <button class="expand-btn" data-id="${comment.id}">
          <span class="icon">+</span>
          <span class="text">Ответы (${replyCount})</span>
        </button>
      ` : ''}
    </div>
    ${hasReplies ? `
      <div class="replies" id="replies-${comment.id}" style="display: none;"></div>
    ` : ''}
  `;

  container.appendChild(commentEl);

  // Обработчики для кнопок
  const replyBtn = commentEl.querySelector('.reply-btn');
  const expandBtn = commentEl.querySelector('.expand-btn');

  replyBtn.addEventListener('click', () => startReply(comment.id, comment.user_name, comment.text));

  if (expandBtn) {
    expandBtn.addEventListener('click', () => toggleReplies(comment.id, comment.replies, level + 1));
  }
}

function toggleReplies(commentId, replies, level) {
  const repliesContainer = document.getElementById(`replies-${commentId}`);
  const expandBtn = document.querySelector(`.expand-btn[data-id="${commentId}"]`);

  if (repliesContainer.style.display === 'none') {
    // Показываем ответы
    repliesContainer.innerHTML = '';
    replies.forEach(reply => {
      renderComment(reply, repliesContainer, level);
    });
    repliesContainer.style.display = 'block';
    expandBtn.classList.add('expanded');
    expandBtn.querySelector('.text').textContent = `Скрыть ответы (${replies.length})`;
    expandBtn.querySelector('.icon').textContent = '−';
  } else {
    // Скрываем ответы
    repliesContainer.style.display = 'none';
    expandBtn.classList.remove('expanded');
    expandBtn.querySelector('.text').textContent = `Ответы (${replies.length})`;
    expandBtn.querySelector('.icon').textContent = '+';
  }
}

function startReply(parentId, userName, text) {
  currentReplyId = parentId;
  parentIdInput.value = parentId;

  // Показываем индикатор ответа
  let replyIndicator = document.querySelector('.replying-to');
  if (!replyIndicator) {
    replyIndicator = document.createElement('div');
    replyIndicator.className = 'replying-to';
    newCommentForm.parentNode.insertBefore(replyIndicator, newCommentForm);
  }

  replyIndicator.innerHTML = `
    <strong>💬 Ответ ${userName}:</strong>
    <span class="text">"${truncateText(text, 50)}"</span>
    <button onclick="cancelReply()" style="margin-left: 10px; background: none; border: none; color: #702459; cursor: pointer;">✕</button>
  `;

  cancelReplyBtn.style.display = 'inline-block';
  textInput.placeholder = `Ваш ответ ${userName}...`;
  textInput.focus();

  // Плавная прокрутка к форме
  newCommentForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function cancelReply() {
  currentReplyId = null;
  parentIdInput.value = '';

  const replyIndicator = document.querySelector('.replying-to');
  if (replyIndicator) {
    replyIndicator.remove();
  }

  cancelReplyBtn.style.display = 'none';
  textInput.placeholder = 'Ваш комментарий...';
  textInput.value = '';
}

// ----------------------------------------
// Вставка нового комментария по WebSocket
function addCommentToTree(comment) {
  if (comment.parent_id) {
    // Это ответ - находим родительский комментарий
    const parentComment = document.querySelector(`.comment[data-id="${comment.parent_id}"]`);
    if (parentComment) {
      let repliesContainer = parentComment.querySelector('.replies');
      const level = parseInt(parentComment.getAttribute('data-level')) + 1;

      if (!repliesContainer) {
        // Создаем контейнер для ответов
        repliesContainer = document.createElement('div');
        repliesContainer.className = 'replies';
        repliesContainer.id = `replies-${comment.parent_id}`;
        repliesContainer.style.display = 'block'; // Показываем сразу для нового ответа
        parentComment.appendChild(repliesContainer);

        // Создаем кнопку раскрытия
        const actions = parentComment.querySelector('.comment-actions');
        const newExpandBtn = document.createElement('button');
        newExpandBtn.className = 'expand-btn expanded';
        newExpandBtn.setAttribute('data-id', comment.parent_id);
        newExpandBtn.innerHTML = '<span class="icon">−</span><span class="text">Ответы (1)</span>';
        newExpandBtn.addEventListener('click', () => toggleReplies(comment.parent_id, [comment], level));
        actions.appendChild(newExpandBtn);
      } else {
        // Обновляем счетчик ответов
        const expandBtn = parentComment.querySelector('.expand-btn');
        if (expandBtn) {
          const match = expandBtn.querySelector('.text').textContent.match(/\d+/);
          const currentCount = match ? parseInt(match[0]) : 0;
          expandBtn.querySelector('.text').textContent = `Ответы (${currentCount + 1})`;
        }

        // Если ответы раскрыты - добавляем новый комментарий
        if (repliesContainer.style.display !== 'none') {
          renderComment(comment, repliesContainer, level);
        }
      }

      // Если контейнер пустой (только что создан), добавляем комментарий
      if (repliesContainer.children.length === 0) {
        renderComment(comment, repliesContainer, level);
      }
    }
  } else {
    // Это корневой комментарий
    renderComment(comment, commentsEl);

    // Убираем сообщение "нет комментариев"
    const noComments = commentsEl.querySelector('.no-comments');
    if (noComments) {
      noComments.remove();
    }
  }

  // Анимация появления
  const newCommentEl = document.querySelector(`.comment[data-id="${comment.id}"]`);
  if (newCommentEl) {
    newCommentEl.style.animation = 'fadeIn 0.5s ease';
  }
}

// ----------------------------------------
// WebSocket
function connectWS() {
  if (ws) ws.close();
  if (heartbeatInterval) clearInterval(heartbeatInterval);

  ws = new WebSocket(`${protocol}://${location.host}/ws/comments`);

  ws.onopen = () => {
    console.log("WS connected");
    statusEl.textContent = "🟢 Подключено";
    statusEl.className = "status connected";

    heartbeatInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, 2000);
  };

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);

    if (msg.type === "all_comments") {
      renderComments(msg.data);
    } else if (msg.type === "new_comment") {
      addCommentToTree(msg.data);
    }
  };

  ws.onerror = (err) => {
    console.error("WebSocket error:", err);
    statusEl.textContent = "🔴 Ошибка подключения";
    statusEl.className = "status disconnected";
    if (heartbeatInterval) clearInterval(heartbeatInterval);
  };

  ws.onclose = () => {
    console.log("WS closed, reconnecting...");
    statusEl.textContent = "🔴 Отключено";
    statusEl.className = "status disconnected";
    if (heartbeatInterval) clearInterval(heartbeatInterval);
    setTimeout(connectWS, 3000);
  };
}

// ----------------------------------------
// REST загрузка текущих комментариев
async function loadInitialComments() {
  try {
    commentsEl.classList.add('loading');
    const res = await fetch("/comments/");
    if (!res.ok) throw new Error(`HTTP error: ${res.status}`);
    const data = await res.json();
    renderComments(data);
  } catch (e) {
    console.error("Failed to load comments:", e);
    commentsEl.innerHTML = `
      <div class="no-comments" style="background: #fed7d7; border-color: #feb2b2;">
        <h3>❌ Ошибка загрузки</h3>
        <p>Не удалось загрузить комментарии. Проверьте подключение к интернету.</p>
      </div>
    `;
  } finally {
    commentsEl.classList.remove('loading');
  }
}

// ----------------------------------------
// Отправка нового комментария
sendBtn.addEventListener("click", async (e) => {
  e.preventDefault();

  const payload = {
    user_name: userInput.value.trim(),
    email: emailInput.value.trim(),
    text: textInput.value.trim(),
    captcha: "12345",
    parent_id: currentReplyId || null
  };

  // Валидация
  if (!payload.user_name) {
    showError(userInput, "Введите имя");
    return;
  }
  if (!payload.email || !isValidEmail(payload.email)) {
    showError(emailInput, "Введите корректный email");
    return;
  }
  if (!payload.text) {
    showError(textInput, "Введите текст комментария");
    return;
  }

  try {
    // Блокируем кнопку отправки
    sendBtn.disabled = true;
    sendBtn.textContent = 'Отправка...';
    sendBtn.style.opacity = '0.7';

    const res = await fetch("/comments/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || "Ошибка сервера");
    }

    // Успешная отправка
    textInput.value = "";
    clearErrors();

    if (!currentReplyId) {
      userInput.value = "";
      emailInput.value = "";
    }

    // Показываем временное сообщение об успехе
    showSuccessMessage();

  } catch (e) {
    console.error("Failed to send comment:", e);
    alert(`Ошибка при отправке: ${e.message}`);
  } finally {
    // Разблокируем кнопку
    sendBtn.disabled = false;
    sendBtn.textContent = '💬 Отправить';
    sendBtn.style.opacity = '1';
  }
});

// ----------------------------------------
// Вспомогательные функции
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function truncateText(text, maxLength) {
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function showError(inputElement, message) {
  clearErrors();
  const errorEl = document.createElement('span');
  errorEl.className = 'field-error';
  errorEl.textContent = message;
  inputElement.parentNode.appendChild(errorEl);
  inputElement.style.borderColor = '#e53e3e';
  inputElement.focus();
}

function clearErrors() {
  document.querySelectorAll('.field-error').forEach(el => el.remove());
  document.querySelectorAll('input, textarea').forEach(el => {
    el.style.borderColor = '#e2e8f0';
  });
}

function showSuccessMessage() {
  const successEl = document.createElement('div');
  successEl.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: #48bb78;
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 1000;
    animation: slideIn 0.3s ease;
  `;
  successEl.textContent = '✅ Комментарий отправлен!';
  document.body.appendChild(successEl);

  setTimeout(() => {
    successEl.remove();
  }, 3000);
}

// Делаем функции глобальными
window.cancelReply = cancelReply;

// ----------------------------------------
// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
  await loadInitialComments();
  connectWS();
});