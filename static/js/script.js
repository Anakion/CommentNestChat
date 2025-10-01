// ----------------------------------------
// DOM элементы
const statusEl = document.getElementById("status");
const commentsEl = document.getElementById("comments");
const userInput = document.getElementById("userName");
const emailInput = document.getElementById("userEmail");
const textInput = document.getElementById("commentText");
const sendBtn = document.getElementById("sendButton");

const protocol = location.protocol === "https:" ? "wss" : "ws";
let ws;
let heartbeatInterval;

// ----------------------------------------
// Рекурсивный рендер комментариев (полное дерево)
function renderComments(comments) {
  commentsEl.innerHTML = "";
  comments.forEach(c => renderCommentTree(c, commentsEl));
}

function renderCommentTree(comment, parentEl) {
  const li = document.createElement("li");
  li.textContent = `#${comment.id} ${comment.user_name}: ${comment.text} (${comment.created_at})`;
  li.setAttribute("data-id", comment.id);
  parentEl.appendChild(li);

  if (comment.replies && comment.replies.length > 0) {
    const ul = document.createElement("ul");
    ul.className = "reply";
    li.appendChild(ul);
    comment.replies.forEach(r => renderCommentTree(r, ul));
  }
}

// ----------------------------------------
// Вставка нового комментария по WebSocket
function addCommentToParent(comment) {
  const li = document.createElement("li");
  li.textContent = `#${comment.id} ${comment.user_name}: ${comment.text} (${comment.created_at})`;
  li.setAttribute("data-id", comment.id);

  let targetEl = commentsEl;
  if (comment.parent_id) {
    const parentLi = document.querySelector(`li[data-id='${comment.parent_id}']`);
    if (parentLi) {
      let ul = parentLi.querySelector("ul.reply");
      if (!ul) {
        ul = document.createElement("ul");
        ul.className = "reply";
        parentLi.appendChild(ul);
      }
      targetEl = ul;
    }
  }

  targetEl.appendChild(li);
}

// ----------------------------------------
// WebSocket с пингом и автопереподключением
function connectWS() {
  if (ws) ws.close();
  if (heartbeatInterval) clearInterval(heartbeatInterval);

  ws = new WebSocket(`${protocol}://${location.host}/ws/comments`);

  ws.onopen = () => {
    console.log("WS connected");
    statusEl.textContent = "Подключено";
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
      addCommentToParent(msg.data);
    }
  };

  ws.onerror = (err) => {
    console.error("WebSocket error:", err);
    if (heartbeatInterval) clearInterval(heartbeatInterval);
  };

  ws.onclose = () => {
    console.log("WS closed, reconnecting...");
    statusEl.textContent = "Отключено";
    statusEl.className = "status disconnected";
    if (heartbeatInterval) clearInterval(heartbeatInterval);
    setTimeout(connectWS, 1000);
  };
}

// ----------------------------------------
// REST загрузка текущих комментариев
async function loadInitialComments() {
  try {
    const res = await fetch("/comments/");
    if (!res.ok) throw new Error(`HTTP error: ${res.status}`);
    const data = await res.json();
    renderComments(data);
  } catch (e) {
    console.error("Failed to load comments:", e);
    commentsEl.innerHTML = "<p>Не удалось загрузить комментарии</p>";
  }
}

// ----------------------------------------
// Отправка нового комментария
sendBtn.addEventListener("click", async (e) => {
  e.preventDefault(); // чтобы форма не сабмитилась

  const payload = {
    user_name: userInput.value.trim(),
    email: emailInput.value.trim(),
    text: textInput.value.trim(),
    captcha: "12345" // временно дефолт
  };

  if (!payload.user_name || !payload.email || !payload.text) {
    alert("Заполните все поля!");
    return;
  }

  try {
    const res = await fetch("/comments/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      console.error("Failed to send comment:", err);
      alert("Ошибка при отправке комментария");
      return;
    }

    textInput.value = "";
    userInput.value = "";
    emailInput.value = "";
  } catch (e) {
    console.error("Failed to send comment (network error):", e);
    alert("Ошибка сети при отправке комментария");
  }
});

// ----------------------------------------
// Инициализация
(async () => {
  await loadInitialComments();
  connectWS();
})();
