const chatEl = document.getElementById("chat");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const fileInput = document.getElementById("file-input");
const uploadStatus = document.getElementById("upload-status");
const statusEl = document.getElementById("status-text");
const statusWrap = statusEl.closest(".status");

function setStatus(text, live = false) {
  statusEl.textContent = text;
  statusWrap.classList.toggle("live", live);
}

function addMessage(role, text) {
  const empty = document.getElementById("empty");
  if (empty) empty.remove();

  const msg = document.createElement("div");
  msg.className = `msg ${role}`;
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "🧑" : "🤖";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  msg.appendChild(avatar);
  msg.appendChild(bubble);
  chatEl.appendChild(msg);
  chatEl.scrollTop = chatEl.scrollHeight;
  return bubble;
}

function addSources(sources, bubble) {
  if (!sources || sources.length === 0) return;
  const details = document.createElement("details");
  details.className = "sources";
  const summary = document.createElement("summary");
  summary.textContent = `🔍 引用 ${sources.length} 个知识块`;
  details.appendChild(summary);

  sources.forEach((src) => {
    const item = document.createElement("div");
    item.className = "source-item";
    const head = document.createElement("div");
    head.className = "src-head";
    const name = document.createElement("span");
    name.textContent = src.source || "未知来源";
    const score = document.createElement("span");
    score.className = "src-score";
    score.textContent = `相关度 ${(src.score * 100).toFixed(1)}%`;
    head.append(name, score);
    const text = document.createElement("div");
    text.className = "src-text";
    text.textContent = src.text || "";
    item.append(head, text);
    details.appendChild(item);
  });

  bubble.appendChild(details);
}

function typingBubble() {
  const msg = document.createElement("div");
  msg.className = "msg assistant typing";
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = "🤖";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = "正在检索知识库并生成回答…";
  msg.appendChild(avatar);
  msg.appendChild(bubble);
  chatEl.appendChild(msg);
  chatEl.scrollTop = chatEl.scrollHeight;
  return msg;
}

async function sendMessage() {
  const question = inputEl.value.trim();
  if (!question || sendBtn.disabled) return;

  addMessage("user", question);
  inputEl.value = "";
  sendBtn.disabled = true;
  const typing = typingBubble();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: question }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "请求失败");
    typing.remove();
    const bubble = addMessage("assistant", data.answer);
    addSources(data.sources, bubble);
    setStatus("在线", true);
  } catch (err) {
    typing.remove();
    addMessage("assistant", `⚠️ ${err.message}`);
    setStatus("异常", false);
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
  }
}

async function uploadFile(file) {
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  uploadStatus.textContent = `正在导入 ${file.name}…`;
  uploadStatus.classList.remove("error");
  try {
    const res = await fetch("/api/ingest", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "导入失败");
    uploadStatus.textContent = data.message;
    addMessage("assistant", `📚 ${data.message}`);
    await refreshStats();
  } catch (err) {
    uploadStatus.textContent = `❌ ${err.message}`;
    uploadStatus.classList.add("error");
  }
  fileInput.value = "";
}

async function refreshStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();
    document.getElementById("stat-chunks").textContent = data.chunk_count || 0;
    document.getElementById("stat-model").textContent = data.llm_model || "-";
  } catch {
    document.getElementById("stat-chunks").textContent = "?";
  }
}

async function loadHistory() {
  try {
    const res = await fetch("/api/sessions/default/messages");
    const rows = await res.json();
    rows.forEach((row) => addMessage(row.role, row.content));
    setStatus("在线", true);
  } catch {
    setStatus("离线", false);
  }
  await refreshStats();
}

formEl.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage();
});

inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    sendMessage();
  }
});

fileInput.addEventListener("change", () => uploadFile(fileInput.files[0]));

loadHistory();