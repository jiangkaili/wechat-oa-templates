# tech-terminal

A WeChat Official Account article template styled after a dark terminal window
(GitHub-dark palette). Best suited for tech digests, changelogs, and
"daily briefing" style posts.

## Look & feel

- **Background:** `#0D1117` (GitHub dark) with `#161B22` section cards.
- **Font:** `'Courier New', monospace` throughout.
- **Headers / prompts:** terminal green `#00FF41`, prefixed with a `$` prompt.
- **Body text:** light gray `#C9D1D9`; labels/secondary `#8B949E`.
- **Borders:** subtle green `#1a3a1a` on images, `#30363D` on cards.
- **Percentages:** auto-colored green (`#22C55E`) for `+x%`, red (`#EF4444`)
  for `-x%` via `colorUpDown`.
- Each section is a dark card with `border-radius:6px` and a `1px solid #30363D`
  border. Images get `border-radius:4px` and a green border.

## Files

| File | Purpose |
|------|---------|
| `composer.py` | `compose_html(article_data, image_urls)` — returns inline-styled HTML. |
| `example.json` | A fully-worked example payload you can feed to the composer. |
| `README.md` | This file. |

## `article_data` schema

```jsonc
{
  "title":   "Article title",
  "digest":  "One-line subtitle / summary",
  "vol":     "042",                       // volume / issue number
  "sections": [
    {
      "heading": "MODEL RELEASES",
      "items":   [
        "Item title<br/>Body text with optional +12.4% or -8.2% coloring（6月27日）"
      ],
      "images":  ["https://.../img.png"]  // optional
    }
  ],
  "trends":  ["+9.4% Agent stars", "-11.3% inference cost"]
}
```

`image_urls` is a dict with a `cover` key (and, optionally, pre-uploaded
section-image URLs).

## Usage

```python
import json
from composer import compose_html

data = json.load(open("example.json"))
html = compose_html(data["article_data"], data["image_urls"])
print(html)
```

## WeChat compatibility

Only inline CSS is emitted. No `flex`, `grid`, `position`, `<style>`, or
external resources are used — only `<section>` / `<p>` / `<span>` / `<img>`
tags, so the HTML pastes cleanly into the WeChat OA editor.

## License

MIT — see the project root `LICENSE`.
