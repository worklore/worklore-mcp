// tricoach SPA. The sign-in token lives in localStorage and travels on every
// API call via the fetch wrapper below.
const TOKEN = localStorage.getItem("tc_token") || "tok-okafor";
const root = document.getElementById("app");

async function api(path, opts = {}) {
  const headers = Object.assign({ "Authorization": "Bearer " + TOKEN }, opts.headers || {});
  const res = await fetch(path, Object.assign({}, opts, { headers }));
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || ("HTTP " + res.status));
  return body;
}

function esc(s) { return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

async function render() {
  try {
    const me = await api("/api/me");
    const st = await api("/api/intervals/status");
    let card;
    const oauthErr = new URLSearchParams(location.search).get("intervals_error");
    if (st.connected) {
      const missing = (st.missing_scopes || []).length
        ? `<p class="muted">Missing access: <code>${esc(st.missing_scopes.join(", "))}</code>.
           <button class="btn" id="connect">Reconnect Intervals.icu</button></p>` : "";
      card = `<div class="card">Connected to Intervals.icu as <b>${esc(st.athlete.name)}</b>
        (${esc(st.athlete.id)}), scope <code>${esc(st.scope)}</code>.${missing}
        <p><button class="btn" id="disconnect">Disconnect</button></p></div>`;
    } else {
      const why = st.status && st.status !== "disconnected" ? `<p class="muted">Status: ${esc(st.status)}</p>` : "";
      const err = oauthErr ? `<p class="muted">Intervals.icu said: ${esc(oauthErr)}</p>` : "";
      card = `<div class="card">Intervals.icu is not connected.${why}${err}
        <p><button class="btn" id="connect">Connect Intervals.icu</button></p></div>`;
    }
    root.className = "";
    root.innerHTML = `<p>Signed in as <b>${esc(me.name)}</b>.</p>${card}`;
    // The authorize URL is fetched through api() so the Bearer token is sent;
    // a plain <a href> navigation carries no Authorization header (-> 401).
    const c = document.getElementById("connect");
    if (c) c.onclick = async () => {
      try { location.href = (await api("/api/intervals/auth/init")).url; }
      catch (e) { root.innerHTML = `<p class="card">Error: ${esc(e.message)}</p>`; }
    };
    const d = document.getElementById("disconnect");
    if (d) d.onclick = async () => { await api("/api/intervals/disconnect", { method: "POST" }); render(); };
  } catch (e) {
    root.innerHTML = `<p class="card">Error: ${esc(e.message)}</p>`;
  }
}

render();
