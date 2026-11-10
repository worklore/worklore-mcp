// The shell page: lists the latest notes from /notes.json when it exists.
fetch('/notes.json').then(r => r.ok ? r.json() : []).then(list => {
  document.getElementById('app').innerHTML = list.map(n => `<p><a href="/s/${n.slug}">${n.title}</a></p>`).join('');
}).catch(() => {});
