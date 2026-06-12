/* GraphyStyle — 비공개 페이지 공유 암호 게이트
 * 4자리 코드(SHA-256 비교). 한 번 통과하면 세션 동안 /plan/ 전 페이지 공유.
 * 클라이언트 게이트이므로 절대적 보안이 아니라 "URL+코드 아는 사람만" 수준의 접근 제한입니다.
 */
(function () {
  var HASH = "c59f438f16c5a409eb2a040b299e82de37503321b9cbfec4fb351547261dd1b1"; // sha256("7369")
  var KEY = "gs_plan_auth_v1";

  // 이미 통과한 세션이면 즉시 종료
  try {
    if (sessionStorage.getItem(KEY) === "ok") return;
  } catch (e) {}

  async function sha256(text) {
    var buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
    return Array.prototype.map
      .call(new Uint8Array(buf), function (b) { return b.toString(16).padStart(2, "0"); })
      .join("");
  }

  // 본문 숨김 (게이트 통과 전 컨텐츠 노출 방지)
  var style = document.createElement("style");
  style.id = "gs-gate-hide";
  style.textContent = "body>*:not(#gs-gate){filter:blur(18px) brightness(.5);pointer-events:none;user-select:none}";
  document.documentElement.appendChild(style);

  function mount() {
    var wrap = document.createElement("div");
    wrap.id = "gs-gate";
    wrap.innerHTML = [
      '<div class="gs-gate-card">',
      '  <div class="gs-gate-lock">●</div>',
      '  <div class="gs-gate-brand">GraphyStyle · Confidential</div>',
      '  <h1 class="gs-gate-title">비공개 사업 전략</h1>',
      '  <p class="gs-gate-sub">접근 코드를 입력하세요</p>',
      '  <form id="gs-gate-form" autocomplete="off">',
      '    <input id="gs-gate-input" inputmode="numeric" pattern="[0-9]*" maxlength="8" placeholder="• • • •" aria-label="접근 코드" />',
      '    <button type="submit">입장</button>',
      '  </form>',
      '  <p id="gs-gate-err" class="gs-gate-err"></p>',
      '  <p class="gs-gate-foot">이 자료는 핵심 관계자 회의용 내부 문서입니다.</p>',
      '</div>'
    ].join("");
    document.body.appendChild(wrap);

    var css = document.createElement("style");
    css.textContent = [
      '#gs-gate{position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;padding:24px;',
      'background:radial-gradient(120% 120% at 50% 0%,#241c17 0%,#14110f 60%,#0c0a09 100%);font-family:Pretendard,system-ui,sans-serif}',
      '.gs-gate-card{width:100%;max-width:360px;text-align:center;color:#f4ece3}',
      '.gs-gate-lock{width:54px;height:54px;margin:0 auto 18px;border-radius:50%;display:flex;align-items:center;justify-content:center;',
      'font-size:13px;color:#ff8a4c;background:rgba(255,107,43,.12);border:1px solid rgba(255,107,43,.35);box-shadow:0 0 0 6px rgba(255,107,43,.05)}',
      '.gs-gate-brand{font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:#c9a27a;margin-bottom:10px}',
      '.gs-gate-title{font-size:26px;font-weight:800;margin:0 0 6px;letter-spacing:-.01em}',
      '.gs-gate-sub{font-size:14px;color:#a99b8c;margin:0 0 22px}',
      '#gs-gate-form{display:flex;gap:8px}',
      '#gs-gate-input{flex:1;min-width:0;padding:14px 16px;font-size:20px;letter-spacing:.4em;text-align:center;border-radius:12px;',
      'border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.04);color:#fff;outline:none;transition:border-color .2s}',
      '#gs-gate-input:focus{border-color:#ff6b2b}',
      '#gs-gate-form button{padding:0 20px;font-size:15px;font-weight:700;border:0;border-radius:12px;cursor:pointer;',
      'color:#fff;background:linear-gradient(135deg,#ff7a35,#ff5e1a);white-space:nowrap}',
      '#gs-gate-form button:active{transform:translateY(1px)}',
      '.gs-gate-err{min-height:18px;font-size:13px;color:#ff7a6b;margin:14px 0 0}',
      '.gs-gate-foot{font-size:12px;color:#7a6e62;margin-top:26px;line-height:1.6}',
      '@keyframes gs-shake{0%,100%{transform:translateX(0)}20%,60%{transform:translateX(-7px)}40%,80%{transform:translateX(7px)}}',
      '.gs-shake{animation:gs-shake .4s}'
    ].join("");
    document.head.appendChild(css);

    var form = document.getElementById("gs-gate-form");
    var input = document.getElementById("gs-gate-input");
    var err = document.getElementById("gs-gate-err");
    input.focus();

    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      var val = (input.value || "").trim();
      var h = await sha256(val);
      if (h === HASH) {
        try { sessionStorage.setItem(KEY, "ok"); } catch (e) {}
        var hide = document.getElementById("gs-gate-hide");
        if (hide) hide.remove();
        wrap.style.opacity = "0";
        wrap.style.transition = "opacity .35s";
        setTimeout(function () { wrap.remove(); }, 360);
      } else {
        err.textContent = "코드가 일치하지 않습니다.";
        var card = wrap.querySelector(".gs-gate-card");
        card.classList.remove("gs-shake");
        void card.offsetWidth;
        card.classList.add("gs-shake");
        input.value = "";
        input.focus();
      }
    });
  }

  if (document.body) mount();
  else document.addEventListener("DOMContentLoaded", mount);
})();
