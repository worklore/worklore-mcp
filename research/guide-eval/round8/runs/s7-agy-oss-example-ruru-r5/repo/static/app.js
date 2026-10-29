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
    if (st.connected) {
      card = `<div class="card">Connected to Intervals.icu as <b>${esc(st.athlete.name)}</b>
        (${esc(st.athlete.id)}), scope <code>${esc(st.scope)}</code>.
        <p><button class="btn" id="disconnect">Disconnect</button></p></div>`;
    } else {
      const why = st.status && st.status !== "disconnected" ? `<p class="muted">Status: ${esc(st.status)}</p>` : "";
      card = `<div class="card">Intervals.icu is not connected.${why}
        <p><button class="btn" id="connectBtn">Connect Intervals.icu</button></p></div>`;
      const connectBtn = document.getElementById("connectBtn");
      if (connectBtn) {
        connectBtn.onclick = async () => {
          try {
            const resp = await api("/api/intervals/auth/init");
            const data = resp; // api returns parsed JSON
            if (data.authorize_url) {
              window.location.assign(data.authorize_url);
            } else {
              throw new Error("No authorize_url");
            }
          } catch (e) {
            alert("Failed to init Connect: " + e.message);
          }
        };
      }
    }
    root.className = "";
    root.innerHTML = `<p>Signed in as <b>${esc(me.name)}</b>.</p>${card}`;
    const d = document.getElementById("disconnect");
    if (d) d.onclick = async () => { await api("/api/intervals/disconnect", { method: "POST" }); render(); };
  } catch (e) {
    root.innerHTML = `<p class="card">Error: ${esc(e.message)}</p>`;
  }
}

render();
