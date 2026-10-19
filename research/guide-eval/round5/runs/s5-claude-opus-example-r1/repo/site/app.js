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
    // The content couldn't be loaded (network error, blocked fetch, 5xx).
    // That is not "this page doesn't exist", so don't say so.
    app.innerHTML = `<section class="error"><h1>Couldn't load this note</h1><p>Please try again in a moment.</p><p><a href="/">Back to all notes</a></p></section>`;
  }
  // Only a real 404 from the API means the note doesn't exist; tell crawlers too.
  function notFound() {
    const meta = document.querySelector('meta[name="robots"]');
    if (meta) meta.setAttribute("content", "noindex");
    app.innerHTML = `<section class="notfound"><h1>NOT FOUND</h1><p>No note lives at this address.</p><p><a href="/">Back to all notes</a></p></section>`;
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
})();
