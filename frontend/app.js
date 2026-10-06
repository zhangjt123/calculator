// 后端 API 基地址：通过后端静态托管时用相对路径；
// 以 file:// 直接打开时回退到本地后端地址。
const API_BASE = location.protocol === "file:" ? "http://127.0.0.1:8000" : "";

const expressionEl = document.getElementById("expression");
const resultEl = document.getElementById("result");
const statusEl = document.getElementById("status");
const historyListEl = document.getElementById("history-list");
const searchEl = document.getElementById("search");
const prevBtn = document.getElementById("prev");
const nextBtn = document.getElementById("next");
const pageInfoEl = document.getElementById("page-info");
const copyBtn = document.getElementById("copy");
const clearHistoryBtn = document.getElementById("clear-history");
const toastEl = document.getElementById("toast");
const modeToggle = document.getElementById("mode-toggle");
const lanUrlEl = document.getElementById("lan-url");
const calcSection = document.querySelector(".calculator");

let currentExpression = "";
let justCalculated = false;
let page = 1;
let totalPages = 1;
let previewSeq = 0;
const PAGE_SIZE = 10;
const OPERATORS = ["+", "-", "*", "/", "**"];

// ---------- 工具 ----------
async function api(path, options = {}) {
  const res = await fetch(API_BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `请求失败 (${res.status})`);
  }
  return data;
}

function escapeHtml(s) {
  const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  return String(s).replace(/[&<>"']/g, (c) => map[c]);
}

function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

let toastTimer;
function showToast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove("show"), 1500);
}

// ---------- 健康检查 / 信息 ----------
async function checkHealth() {
  try {
    await api("/api/health");
    statusEl.textContent = "已连接";
    statusEl.classList.add("ok");
  } catch {
    statusEl.textContent = "后端未连接";
    statusEl.classList.remove("ok");
  }
}

async function loadInfo() {
  try {
    const data = await api("/api/info");
    lanUrlEl.textContent = data.lan_url;
  } catch {
    lanUrlEl.textContent = "";
  }
}

// ---------- 计算与实时预览 ----------
async function calculate() {
  const expr = currentExpression.trim();
  if (!expr) return;
  previewSeq++; // 使在途的预览结果失效
  try {
    const data = await api("/api/calculate", {
      method: "POST",
      body: JSON.stringify({ expression: expr, save: true }),
    });
    expressionEl.textContent = expr + " =";
    resultEl.textContent = data.result;
    resultEl.classList.remove("preview");
    currentExpression = data.result;
    justCalculated = true;
    await loadHistory();
  } catch (err) {
    resultEl.textContent = "错误";
    resultEl.classList.remove("preview");
    justCalculated = false;
    flashError(err.message);
  }
}

const preview = debounce(async () => {
  const mySeq = ++previewSeq;
  const expr = currentExpression.trim();
  if (justCalculated) return;
  if (!expr) {
    resultEl.textContent = "0";
    resultEl.classList.remove("preview");
    return;
  }
  try {
    const data = await api("/api/calculate", {
      method: "POST",
      body: JSON.stringify({ expression: expr, save: false }),
    });
    if (mySeq !== previewSeq) return;
    resultEl.textContent = data.result;
    resultEl.classList.add("preview");
  } catch {
    if (mySeq === previewSeq) {
      resultEl.textContent = "";
      resultEl.classList.remove("preview");
    }
  }
}, 250);

function flashError(msg) {
  expressionEl.textContent = msg;
  expressionEl.classList.add("error");
  setTimeout(() => {
    expressionEl.classList.remove("error");
    expressionEl.textContent = currentExpression;
  }, 2500);
}

function inputValue(v) {
  if (justCalculated) {
    currentExpression = OPERATORS.includes(v) ? resultEl.textContent : "";
    justCalculated = false;
    resultEl.classList.remove("preview");
  }
  currentExpression += v;
  render();
  preview();
}

function backspace() {
  currentExpression = currentExpression.slice(0, -1);
  justCalculated = false;
  render();
  preview();
}

function clearAll() {
  currentExpression = "";
  justCalculated = false;
  resultEl.textContent = "0";
  resultEl.classList.remove("preview");
  render();
}

function render() {
  expressionEl.textContent = currentExpression;
}

// ---------- 一元函数（整体包裹）----------
function applyUnary(wrap) {
  const expr = currentExpression.trim();
  if (!expr) return;
  currentExpression = wrap(expr);
  justCalculated = false;
  resultEl.classList.remove("preview");
  render();
  preview();
}

function doSqrt() { applyUnary((e) => "sqrt(" + e + ")"); }
function doSquare() { applyUnary((e) => "(" + e + ")*(" + e + ")"); }
function doReciprocal() { applyUnary((e) => "1/(" + e + ")"); }
function doPercent() { applyUnary((e) => "(" + e + ")/100"); }
function doFactorial() { applyUnary((e) => "factorial(" + e + ")"); }
function doSin() { applyUnary((e) => "sin(" + e + ")"); }
function doCos() { applyUnary((e) => "cos(" + e + ")"); }
function doTan() { applyUnary((e) => "tan(" + e + ")"); }
function doAsin() { applyUnary((e) => "asin(" + e + ")"); }
function doAtan() { applyUnary((e) => "atan(" + e + ")"); }
function doLn() { applyUnary((e) => "ln(" + e + ")"); }
function doLog() { applyUnary((e) => "log(" + e + ")"); }

// 幂运算（二元）：追加 **
function doPower() { inputValue("**"); }

// 常量 π / e：若前一字符是数字或右括号则自动补乘号
function insertConstant(name) {
  if (justCalculated) {
    currentExpression = "";
    justCalculated = false;
  }
  const last = currentExpression.slice(-1);
  currentExpression += last && /[0-9)]/.test(last) ? "*" + name : name;
  render();
  preview();
}

function isOuterNegated(expr) {
  if (!expr.startsWith("-(") || !expr.endsWith(")")) return false;
  let depth = 0;
  for (let i = 1; i < expr.length - 1; i++) {
    const c = expr[i];
    if (c === "(") depth++;
    else if (c === ")") {
      depth--;
      if (depth < 0) return false;
    }
  }
  return depth === 1;
}

function negate() {
  const expr = currentExpression.trim();
  if (!expr) return;
  currentExpression = isOuterNegated(expr) ? expr.slice(2, -1) : "-(" + expr + ")";
  justCalculated = false;
  resultEl.classList.remove("preview");
  render();
  preview();
}

async function copyResult() {
  const text = resultEl.textContent;
  if (!text || text === "0" || text === "错误") return;
  try {
    await navigator.clipboard.writeText(text);
    showToast("已复制");
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand("copy");
      showToast("已复制");
    } catch {
      showToast("复制失败");
    }
    document.body.removeChild(ta);
  }
}

// ---------- 历史记录 ----------
async function loadHistory() {
  const search = searchEl.value.trim();
  const params = new URLSearchParams({ page, page_size: PAGE_SIZE });
  if (search) params.set("search", search);

  try {
    const data = await api("/api/history?" + params.toString());
    totalPages = Math.max(1, Math.ceil(data.total / data.page_size));
    page = data.page;
    renderHistory(data.items);
    updatePagination();
  } catch (err) {
    historyListEl.innerHTML = `<li class="empty">加载失败：${escapeHtml(err.message)}</li>`;
  }
}

function renderHistory(items) {
  if (!items.length) {
    historyListEl.innerHTML = '<li class="empty">暂无记录</li>';
    return;
  }
  historyListEl.innerHTML = items
    .map((item) => {
      const time = new Date(item.created_at).toLocaleString();
      return `
        <li class="history-item" data-expr="${escapeHtml(item.expression)}">
          <div class="hist-body">
            <div class="hist-expr">${escapeHtml(item.expression)}</div>
            <div class="hist-res">= ${escapeHtml(item.result)}</div>
            <div class="hist-time">${time}</div>
          </div>
          <button class="del" data-id="${item.id}" title="删除">×</button>
        </li>`;
    })
    .join("");
}

function updatePagination() {
  pageInfoEl.textContent = `${page} / ${totalPages}`;
  prevBtn.disabled = page <= 1;
  nextBtn.disabled = page >= totalPages;
}

async function deleteRecord(id) {
  try {
    await api(`/api/history/${id}`, { method: "DELETE" });
    await loadHistory();
  } catch (err) {
    showToast(err.message);
  }
}

async function clearHistory() {
  if (!window.confirm("确定清空所有历史记录吗？")) return;
  try {
    await api("/api/history", { method: "DELETE" });
    page = 1;
    await loadHistory();
    showToast("已清空");
  } catch (err) {
    showToast(err.message);
  }
}

// ---------- 事件绑定 ----------
document.querySelectorAll(".key").forEach((btn) => {
  btn.addEventListener("click", () => {
    const value = btn.dataset.value;
    const action = btn.dataset.action;
    if (action === "clear") clearAll();
    else if (action === "backspace") backspace();
    else if (action === "equals") calculate();
    else if (action === "sqrt") doSqrt();
    else if (action === "square") doSquare();
    else if (action === "power") doPower();
    else if (action === "reciprocal") doReciprocal();
    else if (action === "factorial") doFactorial();
    else if (action === "percent") doPercent();
    else if (action === "negate") negate();
    else if (action === "sin") doSin();
    else if (action === "cos") doCos();
    else if (action === "tan") doTan();
    else if (action === "asin") doAsin();
    else if (action === "atan") doAtan();
    else if (action === "ln") doLn();
    else if (action === "log") doLog();
    else if (action === "pi") insertConstant("pi");
    else if (action === "e") insertConstant("e");
    else if (value) inputValue(value);
  });
});

modeToggle.addEventListener("click", () => {
  const sci = calcSection.classList.toggle("sci-mode");
  modeToggle.textContent = sci ? "基础" : "科学";
  modeToggle.classList.toggle("active", sci);
});

copyBtn.addEventListener("click", copyResult);
clearHistoryBtn.addEventListener("click", clearHistory);

historyListEl.addEventListener("click", (e) => {
  const delBtn = e.target.closest(".del");
  if (delBtn) {
    deleteRecord(delBtn.dataset.id);
    return;
  }
  const item = e.target.closest(".history-item");
  if (item) {
    currentExpression = item.dataset.expr;
    justCalculated = false;
    resultEl.textContent = "0";
    resultEl.classList.remove("preview");
    render();
    preview();
  }
});

prevBtn.addEventListener("click", () => {
  if (page > 1) {
    page--;
    loadHistory();
  }
});

nextBtn.addEventListener("click", () => {
  if (page < totalPages) {
    page++;
    loadHistory();
  }
});

searchEl.addEventListener("input", debounce(() => {
  page = 1;
  loadHistory();
}, 300));

document.addEventListener("keydown", (e) => {
  if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA")) return;

  if (e.key >= "0" && e.key <= "9") inputValue(e.key);
  else if (e.key === ".") inputValue(".");
  else if (["+", "-", "*", "/"].includes(e.key)) inputValue(e.key);
  else if (e.key === "(" || e.key === ")") inputValue(e.key);
  else if (e.key === "%") doPercent();
  else if (e.key === "^") doPower();
  else if (e.key === "Enter" || e.key === "=") {
    e.preventDefault();
    calculate();
  } else if (e.key === "Backspace") backspace();
  else if (e.key === "Escape") clearAll();
});

// ---------- URL 参数（用于演示/截图）：?expr=...&mode=sci ----------
async function applyUrlParams() {
  const params = new URLSearchParams(location.search);
  if (params.get("mode") === "sci") {
    calcSection.classList.add("sci-mode");
    modeToggle.textContent = "基础";
    modeToggle.classList.add("active");
  }
  const expr = params.get("expr");
  if (expr) {
    currentExpression = expr;
    render();
    try {
      const data = await api("/api/calculate", {
        method: "POST",
        body: JSON.stringify({ expression: expr, save: false }),
      });
      expressionEl.textContent = expr + " =";
      resultEl.textContent = data.result;
      resultEl.classList.remove("preview");
      justCalculated = true;
    } catch (err) {
      resultEl.textContent = "错误";
      expressionEl.textContent = err.message;
    }
  }
}

// ---------- 服务端预渲染初始值（?expr= 由后端注入 window.__INITIAL__）----------
function applyInitial() {
  const init = window.__INITIAL__;
  if (!init) return;
  if (init.mode === "sci") {
    calcSection.classList.add("sci-mode");
    modeToggle.textContent = "基础";
    modeToggle.classList.add("active");
  }
  if (init.expr) {
    currentExpression = init.expr;
    expressionEl.textContent = init.expr + " =";
    resultEl.textContent = init.result;
    resultEl.classList.remove("preview");
    justCalculated = true;
  }
}

// ---------- 初始化 ----------
checkHealth();
loadInfo();
if (window.__INITIAL__) {
  applyInitial();
} else {
  loadHistory();
  render();
  applyUrlParams();
}
setInterval(checkHealth, 15000);
