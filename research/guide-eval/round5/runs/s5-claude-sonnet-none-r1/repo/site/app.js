// Renders the home list or one note, depending on the path.
(async function () {
  const app = document.getElementById("app");
  const m = location.pathname.match(/^\/n\/([a-z0-9-]+)$/);
  try {
    if (m) {
      const r = await fetch(`/v1/notes/${m[1]}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const note = await r.json();
      document.title = `${note.title} · Field notes`;
      app.innerHTML = `<article><h1>${esc(note.title)}</h1><p class="meta">${esc(note.date)}</p>${note.html}</article>`;
    } else {
      const r = await fetch("/v1/notes?limit=50");
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const notes = await r.json();
      app.innerHTML = "<ul>" + notes.map(n => `<li><a href="/n/${n.slug}">${esc(n.title)}</a></li>`).join("") + "</ul>";
    }
  } catch (e) {
    // Error states must never be indexed as if they were real pages.
    const meta = document.createElement("meta");
    meta.name = "robots";
    meta.content = "noindex";
    document.head.appendChild(meta);
    app.innerHTML = `<section class="notfound"><h1>NOT FOUND</h1><p>No note lives at this address.</p><p><a href="/">Back to all notes</a></p></section>`;
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
})();
