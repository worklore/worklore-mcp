// Renders the home list or one note, depending on the path.
(async function () {
  const app = document.getElementById("app");
  const m = location.pathname.match(/^\/n\/([a-z0-9-]+)$/);
  try {
    if (m) {
      const r = await fetch(`/v1/notes/${m[1]}`);
      if (r.status === 404) return notFound();
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const note = await r.json();
      document.title = `${note.title} · Field notes`;
      app.innerHTML = `<article><h1>${esc(note.title)}</h1><p class="meta">${esc(note.date)}</p>${note.html}</article>`;
    } else {
      const r = await fetch("/v1/notes?limit=50");
      if (r.status === 404) return notFound();
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const notes = await r.json();
      app.innerHTML = "<ul>" + notes.map(n => `<li><a href="/n/${n.slug}">${esc(n.title)}</a></li>`).join("") + "</ul>";
    }
  } catch (e) {
    // Network/robots/5xx failure: the note may well exist, so don't claim it doesn't.
    app.innerHTML = `<section class="error"><h1>Couldn't load this page</h1><p>Please try again in a moment.</p><p><a href="/">Back to all notes</a></p></section>`;
  }
  function notFound() {
    // A real missing note: tell crawlers not to index this 200 shell.
    const meta = document.querySelector('meta[name="robots"]');
    if (meta) meta.content = "noindex";
    document.title = "Not found · Field notes";
    app.innerHTML = `<section class="notfound"><h1>NOT FOUND</h1><p>No note lives at this address.</p><p><a href="/">Back to all notes</a></p></section>`;
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
})();
