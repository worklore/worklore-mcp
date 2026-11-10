"""Prerender one page per public note (s/<slug>) and per author with a public note (a/<handle>).
usage: build_pages.py content/stories.json .build/pages"""
import html, json, os, sys

src, out = sys.argv[1], sys.argv[2]
stories = [s for s in json.load(open(src)) if s.get("visibility", "public") == "public"]

def page(title, body):
    return (f"<!doctype html><html><head><meta charset=utf-8><title>{html.escape(title)} · fieldnotes</title>"
            f"<link rel=stylesheet href=/style.css></head><body>{body}<script src=/app.js></script></body></html>\n")

def write(key, text):
    p = os.path.join(out, key)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(text)

authors = {}
for s in stories:
    write(f"s/{s['slug']}", page(s["title"], f"<h1>{html.escape(s['title'])}</h1><p>{html.escape(s['summary'])}</p>"
                                 f"<p>by <a href=/a/{s['author']}>{s['author']}</a></p>"))
    authors.setdefault(s["author"], []).append(s)
for handle, mine in authors.items():
    items = "".join(f"<li><a href=/s/{s['slug']}>{html.escape(s['title'])}</a></li>" for s in mine)
    write(f"a/{handle}", page(handle, f"<h1>{handle}</h1><ul>{items}</ul>"))
print(f"  {len(stories)} notes, {len(authors)} authors")
