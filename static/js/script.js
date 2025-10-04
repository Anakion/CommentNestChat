// ----------------------------------------
// DOM элементы
const statusEl = document.getElementById("status");
const commentsEl = document.getElementById("comments");
const userInput = document.getElementById("userName");
const emailInput = document.getElementById("userEmail");
const homePageInput = document.getElementById("homePage");
const textInput = document.getElementById("commentText");
const sendBtn = document.getElementById("sendButton");
const imageUpload = document.getElementById("imageUpload");
const textFileUpload = document.getElementById("textFileUpload");
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
        ${comment.home_page ? `<a href="${comment.home_page}" target="_blank" class="user-website">🌐 Website</a>` : ''}
      </div>
      <div class="comment-date">${formatDate(comment.created_at)}</div>
    </div>
    <div class="comment-text">${safeHtml(comment.text)}</div>

    ${comment.file_path ? `
      <div class="comment-files">
        ${comment.file_type === 'image' ? `
          <div class="file-preview image-preview">
            <img src="/${comment.file_path}" alt="Attached image"
                 data-width="${comment.image_w || 320}"
                 data-height="${comment.image_h || 240}"
                 class="preview-image">
            <div class="file-info">🖼️ Изображение ${comment.image_w || 320}×${comment.image_h || 240}</div>
          </div>
        ` : ''}
        ${comment.file_type === 'text' ? `
          <div class="file-preview text-preview">
            <a href="/${comment.file_path}" target="_blank" class="text-file-link">
              📄 ${comment.file_path.split('/').pop()}
            </a>
            <div class="file-info">📝 Текстовый файл</div>
          </div>
        ` : ''}
      </div>
    ` : ''}

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
    console.log("WebSocket message:", msg);

    if (msg.type === "all_comments") {
      renderComments(msg.data);
    } else if (msg.type === "new_comment") {
      addCommentToTree(msg.data);
    }
  };

  ws.onerror = (err) => {
    console.log("WS error (ignore, reconnecting...)");
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

  // Сначала валидация полей из DOM элементов
  const userName = userInput.value.trim();
  const email = emailInput.value.trim();
  const homePage = homePageInput.value.trim();
  const text = textInput.value.trim();
  const captcha = document.getElementById('captcha').value.trim();
  const parentId = currentReplyId || "";

  // ВАЛИДАЦИЯ ВСЕХ ПОЛЕЙ
  let hasErrors = false;
  clearErrors();

  // Валидация имени
  if (!userName) {
    showError(userInput, "Введите имя");
    hasErrors = true;
  } else if (!validateUserName(userName)) {
    showError(userInput, "Только английские буквы и цифры (1-60 символов)");
    hasErrors = true;
  }

  // Валидация email
  if (!email) {
    showError(emailInput, "Введите email");
    hasErrors = true;
  } else if (!isValidEmail(email)) {
    showError(emailInput, "Введите корректный email");
    hasErrors = true;
  }

  // Валидация homepage (необязательное поле)
  if (homePage && !validateUrl(homePage)) {
    showError(homePageInput, "Введите корректный URL (например https://example.com)");
    hasErrors = true;
  }

  // Валидация текста комментария
  if (!text) {
    showError(textInput, "Введите текст комментария");
    hasErrors = true;
  }

  // Валидация капчи
  if (!captcha) {
    const captchaInput = document.getElementById('captcha');
    showError(captchaInput, "Введите код с картинки");
    hasErrors = true;
  }

  // Валидация файлов
  if (!validateFiles()) {
    hasErrors = true;
  }

  // Если есть ошибки - прерываем отправку
  if (hasErrors) {
    return;
  }

  // Создаем FormData для отправки файлов
  const formData = new FormData();

  // Добавляем текстовые поля
  formData.append("user_name", userName);
  formData.append("email", email);
  formData.append("home_page", homePage || "");
  formData.append("text", text);
  formData.append("captcha", captcha);
  formData.append("parent_id", parentId);

  // Добавляем файлы если есть
  if (imageUpload.files[0]) {
    formData.append("image", imageUpload.files[0]);
  }

  if (textFileUpload.files[0]) {
    formData.append("text_file", textFileUpload.files[0]);
  }

  console.log("Sending form data with files:", {
    user_name: userName,
    email: email,
    hasImage: !!imageUpload.files[0],
    hasTextFile: !!textFileUpload.files[0]
  });

  try {
    // Блокируем кнопку отправки
    sendBtn.disabled = true;
    sendBtn.textContent = 'Отправка...';
    sendBtn.style.opacity = '0.7';

    // Отправляем FormData
    const res = await fetch("/comments/", {
      method: "POST",
      body: formData
    });

    const responseData = await res.json();

    if (!res.ok) {
      // Обработка ошибок сервера
      let errorMessage = responseData.message || "Ошибка сервера";

      // Специальная обработка для ошибок капчи
      if (errorMessage.includes("CAPTCHA") || errorMessage.includes("captcha")) {
        const captchaInput = document.getElementById('captcha');
        showError(captchaInput, errorMessage);
        // Обновляем капчу при ошибке
        document.getElementById('captchaImage').src = '/captcha?t=' + Date.now();
        captchaInput.value = ''; // Очищаем поле капчи
      } else {
        alert(`Ошибка при отправке: ${errorMessage}`);
      }

      throw new Error(errorMessage);
    }

    // Успешная отправка - очищаем ВСЕ поля
    textInput.value = "";
    imageUpload.value = "";
    textFileUpload.value = "";
    document.getElementById('captcha').value = "";
    clearErrors();

    if (!currentReplyId) {
      userInput.value = "";
      emailInput.value = "";
      homePageInput.value = "";
    }

    // Показываем временное сообщение об успехе
    showSuccessMessage();
    cancelReply();

    // Обновляем капчу после успешной отправки
    document.getElementById('captchaImage').src = '/captcha?t=' + Date.now();

  } catch (e) {
    console.error("Failed to send comment:", e);
    // Сообщение об ошибке уже показано в блоке выше

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

function safeHtml(text) {
    if (!text) return '';

    // ПРОСТАЯ И НАДЕЖНАЯ ВЕРСИЯ
    // Разрешаем ТОЛЬКО базовые теги через белый список
    const allowedTags = {
        '&lt;strong&gt;': '<strong>',
        '&lt;/strong&gt;': '</strong>',
        '&lt;i&gt;': '<i>',
        '&lt;/i&gt;': '</i>',
        '&lt;code&gt;': '<code>',
        '&lt;/code&gt;': '</code>',
        '&lt;a href="': '<a href="',
        '&lt;/a&gt;': '</a>',
        '&lt;a title="': '<a title="',
        '"&gt;': '">'  // Закрываем атрибуты
    };

    // 1. Сначала экранируем ВЕСЬ текст
    let safe = escapeHtml(text);

    // 2. Аккуратно заменяем ТОЛЬКО разрешенные теги
    for (const [escaped, original] of Object.entries(allowedTags)) {
        safe = safe.replace(new RegExp(escaped, 'g'), original);
    }

    console.log("HTML DEBUG:");
    console.log("Input:", text);
    console.log("Output:", safe);

    return safe;
}

// Улучшенные функции валидации
function validateUserName(name) {
  return /^[a-zA-Z0-9]{1,60}$/.test(name);
}

function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

function validateUrl(url) {
  if (!url) return true; // Пустое поле - ок (необязательное)
  try {
    const urlObj = new URL(url);
    return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
  } catch {
    return false;
  }
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

// Функция для валидации файлов
function validateFiles() {
  const imageFile = imageUpload.files[0];
  const textFile = textFileUpload.files[0];
  let isValid = true;

  if (imageFile) {
    // Проверка типа изображения
    const validImageTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!validImageTypes.includes(imageFile.type)) {
      showError(imageUpload, "Разрешены только JPEG, PNG, GIF и WebP изображения");
      isValid = false;
    }

    // Проверка размера (например, максимум 5MB)
    if (imageFile.size > 5 * 1024 * 1024) {
      showError(imageUpload, "Размер изображения не должен превышать 5MB");
      isValid = false;
    }
  }

  if (textFile) {
    // Проверка типа текстового файла
    const validTextTypes = ['text/plain', 'application/octet-stream'];
    if (!validTextTypes.includes(textFile.type) && !textFile.name.endsWith('.txt')) {
      showError(textFileUpload, "Разрешены только текстовые файлы (.txt)");
      isValid = false;
    }

    // Проверка размера (например, максимум 100KB)
    if (textFile.size > 100 * 1024) {
      showError(textFileUpload, "Размер текстового файла не должен превышать 100KB");
      isValid = false;
    }
  }

  return isValid;
}

// Улучшенная функция показа ошибок
function showError(inputElement, message) {
  // Сначала очищаем старые ошибки для этого поля
  const existingError = inputElement.parentNode.querySelector('.field-error');
  if (existingError) {
    existingError.remove();
  }

  const errorEl = document.createElement('span');
  errorEl.className = 'field-error';
  errorEl.textContent = message;
  inputElement.parentNode.appendChild(errorEl);
  inputElement.style.borderColor = '#e53e3e';
  inputElement.focus();
}

// Улучшенная функция очистки ошибок
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
// ОБРАБОТЧИКИ ДЛЯ HTML ПАНЕЛИ
function initHtmlToolbar() {
    const toolbar = document.querySelector('.html-toolbar');
    const textarea = document.getElementById('commentText');

    if (!toolbar || !textarea) return;

    // Обработчик для всех кнопок панели
    toolbar.addEventListener('click', (e) => {
        if (e.target.classList.contains('html-btn')) {
            const tag = e.target.getAttribute('data-tag');
            insertHtmlTag(tag, textarea);
        }
    });
}

// Функция для вставки HTML тегов
function insertHtmlTag(tag, textarea) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);

    let tagTemplate;

    switch(tag) {
        case 'strong':
            tagTemplate = selectedText ? `<strong>${selectedText}</strong>` : '<strong></strong>';
            break;
        case 'i':
            tagTemplate = selectedText ? `<i>${selectedText}</i>` : '<i></i>';
            break;
        case 'code':
            tagTemplate = selectedText ? `<code>${selectedText}</code>` : '<code></code>';
            break;
        case 'a':
            if (selectedText) {
                tagTemplate = `<a href="${prompt('Введите URL:', 'https://')}" title="${prompt('Введите заголовок (опционально):', '')}">${selectedText}</a>`;
            } else {
                tagTemplate = '<a href="https://" title=""></a>';
            }
            break;
        default:
            return;
    }

    // Вставляем тег в текстовое поле
    textarea.value = textarea.value.substring(0, start) + tagTemplate + textarea.value.substring(end);

    // Устанавливаем фокус обратно в textarea
    textarea.focus();

    // Для тегов без выделенного текста - ставим курсор внутрь тегов
    if (!selectedText) {
        let cursorPos;
        switch(tag) {
            case 'a':
                cursorPos = start + 9; // После <a href="">
                break;
            case 'strong':
                cursorPos = start + 8; // После <strong>
                break;
            case 'i':
                cursorPos = start + 3; // После <i>
                break;
            case 'code':
                cursorPos = start + 6; // После <code>
                break;
            default:
                cursorPos = start + tagTemplate.length;
        }
        textarea.setSelectionRange(cursorPos, cursorPos);
    }
}

// Обновление капчи
function initCaptcha() {
    const refreshBtn = document.getElementById('refreshCaptcha');
    console.log("Refresh button found:", refreshBtn);

    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            console.log("Refresh button clicked!");
            const captchaImage = document.getElementById('captchaImage');
            captchaImage.src = '/captcha?t=' + Date.now();
        });
    }
}

// Реализуем live-валидацию при вводе
function initLiveValidation() {
  // Валидация имени пользователя
  userInput.addEventListener('input', () => {
    const value = userInput.value.trim();
    const error = userInput.parentNode.querySelector('.field-error');

    if (value && !validateUserName(value)) {
      userInput.style.borderColor = '#e53e3e';
    } else {
      userInput.style.borderColor = '#e2e8f0';
      if (error && error.textContent.includes('английские')) {
        error.remove();
      }
    }
  });

  // Валидация email
  emailInput.addEventListener('input', () => {
    const value = emailInput.value.trim();
    const error = emailInput.parentNode.querySelector('.field-error');

    if (value && !isValidEmail(value)) {
      emailInput.style.borderColor = '#e53e3e';
    } else {
      emailInput.style.borderColor = '#e2e8f0';
      if (error && error.textContent.includes('email')) {
        error.remove();
      }
    }
  });

  // Валидация homepage
  homePageInput.addEventListener('input', () => {
    const value = homePageInput.value.trim();
    const error = homePageInput.parentNode.querySelector('.field-error');

    if (value && !validateUrl(value)) {
      homePageInput.style.borderColor = '#e53e3e';
    } else {
      homePageInput.style.borderColor = '#e2e8f0';
      if (error && error.textContent.includes('URL')) {
        error.remove();
      }
    }
  });

  // Валидация текста комментария
  textInput.addEventListener('input', () => {
    const value = textInput.value.trim();
    const error = textInput.parentNode.querySelector('.field-error');

    if (value) {
      textInput.style.borderColor = '#e2e8f0';
      if (error && error.textContent.includes('текст')) {
        error.remove();
      }
    }
  });

  // Валидация капчи
  const captchaInput = document.getElementById('captcha');
  if (captchaInput) {
    captchaInput.addEventListener('input', () => {
      const value = captchaInput.value.trim();
      const error = captchaInput.parentNode.querySelector('.field-error');

      if (value) {
        captchaInput.style.borderColor = '#e2e8f0';
        if (error && error.textContent.includes('код')) {
          error.remove();
        }
      }
    });
  }
}

// ----------------------------------------
// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
  await loadInitialComments();
  connectWS();
  initHtmlToolbar();
  initCaptcha();
  initLiveValidation();
});