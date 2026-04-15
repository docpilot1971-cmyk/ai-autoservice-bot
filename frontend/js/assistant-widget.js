(function () {
  "use strict";

  var isProdHost = window.location.hostname === "avtoritet34.ru" || window.location.hostname === "www.avtoritet34.ru";
  var defaultApiBase = isProdHost ? "https://avtoritet34.ru/api" : "http://localhost:8000/api";
  var apiBase = window.ASSISTANT_API_BASE || defaultApiBase;

  var style = document.createElement("style");
  style.textContent = ""
    + ".assistant-fab{position:fixed;right:20px;bottom:20px;z-index:3000;background:#ff6b00;color:#fff;border:none;border-radius:999px;padding:12px 16px;font-weight:700;cursor:pointer;box-shadow:0 10px 24px rgba(0,0,0,.35)}"
    + ".assistant-panel{position:fixed;right:20px;bottom:76px;z-index:3000;width:min(420px,calc(100vw - 24px));max-height:70vh;background:#161616;border:1px solid #2f2f2f;border-radius:14px;display:none;flex-direction:column;overflow:hidden;box-shadow:0 16px 32px rgba(0,0,0,.45)}"
    + ".assistant-panel.is-open{display:flex}"
    + ".assistant-head{padding:12px 14px;border-bottom:1px solid #2f2f2f;font-weight:700;background:#1e1e1e;display:flex;align-items:center;justify-content:space-between;gap:8px}"
    + ".assistant-close{width:28px;height:28px;border:1px solid #3a3a3a;border-radius:8px;background:#252525;color:#fff;cursor:pointer;font-size:18px;line-height:1}"
    + ".assistant-close:hover{background:#303030}"
    + ".assistant-log{padding:12px;overflow:auto;display:flex;flex-direction:column;gap:10px}"
    + ".assistant-msg{padding:10px 12px;border-radius:10px;line-height:1.45;font-size:14px;white-space:pre-wrap}"
    + ".assistant-msg.user{background:#2a2a2a;align-self:flex-end;max-width:90%}"
    + ".assistant-msg.bot{background:#202020;border:1px solid #303030;max-width:95%}"
    + ".assistant-form{display:flex;gap:8px;padding:10px;border-top:1px solid #2f2f2f;background:#181818}"
    + ".assistant-input{flex:1;min-height:40px;padding:8px 10px;border-radius:8px;border:1px solid #3b3b3b;background:#111;color:#fff}"
    + ".assistant-send{min-width:92px;border:none;border-radius:8px;background:#ff6b00;color:#fff;font-weight:700;cursor:pointer}"
    + "@media(max-width:767px){.assistant-fab{right:12px;bottom:12px}.assistant-panel{right:12px;bottom:66px;width:calc(100vw - 24px)}}";
  document.head.appendChild(style);

  var fab = document.createElement("button");
  fab.className = "assistant-fab";
  fab.type = "button";
  fab.textContent = "Спросить";

  var panel = document.createElement("section");
  panel.className = "assistant-panel";
  panel.innerHTML = ""
    + '<div class="assistant-head"><span>AI-консультант Авторитет</span><button type="button" class="assistant-close" aria-label="Закрыть чат">×</button></div>'
    + '<div class="assistant-log" id="assistant-log"></div>'
    + '<form class="assistant-form" id="assistant-form">'
    + '<input class="assistant-input" id="assistant-input" type="text" placeholder="Например: сколько занимает диагностика?" required>'
    + '<button class="assistant-send" type="submit">Отправить</button>'
    + '</form>';

  document.body.appendChild(fab);
  document.body.appendChild(panel);

  var log = panel.querySelector("#assistant-log");
  var form = panel.querySelector("#assistant-form");
  var input = panel.querySelector("#assistant-input");
  var closeBtn = panel.querySelector(".assistant-close");

  function addMsg(text, who) {
    var div = document.createElement("div");
    div.className = "assistant-msg " + who;
    div.textContent = text;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
  }

  addMsg("Здравствуйте. Я помогу с вопросами по ремонту и обслуживанию.", "bot");

  fab.addEventListener("click", function () {
    panel.classList.toggle("is-open");
    if (panel.classList.contains("is-open")) input.focus();
  });

  closeBtn.addEventListener("click", function () {
    panel.classList.remove("is-open");
  });

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    var question = input.value.trim();
    if (!question) return;

    addMsg(question, "user");
    input.value = "";
    addMsg("Думаю...", "bot");

    try {
      var res = await fetch(apiBase + "/chat/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: question, use_cache: true })
      });

      if (!res.ok) {
        throw new Error("HTTP " + res.status);
      }

      var data = await res.json();
      log.lastChild.remove();
      addMsg(data.answer || "Не удалось получить ответ", "bot");
    } catch (err) {
      log.lastChild.remove();
      addMsg("Сервис временно недоступен. Позвоните нам: +7 (988) 018-37-55", "bot");
    }
  });
})();
