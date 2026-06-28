# WeChat OA Template Gallery

> A pluggable WeChat Official Account article template gallery with a Python publisher that auto-creates drafts via the WeChat MP API.

> 一套可插拔的微信公众号文章排版模板，配合 Python 发布脚本，自动创建草稿到公众号后台。

中文 | [English](README.md)

---

## Preview

6 styles, same content data, switch with one field:

| Template | Style | Background | Best For |
|----------|-------|------------|----------|
| apple-minimalist | Apple minimalism | White #FFFFFF | Tech news, daily briefings |
| dark-mode | Dark mode | Dark #1D1D1F | Tech blogs, developer newsletters |
| warm-paper | Warm journal | Cream #FAF9F5 | Humanities, long-form reading |
| card-layout | Card layout | White + gray cards | Product updates, multi-column |
| gradient-header | Gradient header | Purple gradient + white | Brand promotion, event previews |
| tech-terminal | Terminal style | GitHub Dark | Geek culture, open-source projects |

## Features

- 6 built-in templates, switch via `"style"` field
- Pluggable: drop a `composer.py` into `templates/your-style/` and it works
- Unified JSON input — switch templates without rewriting content
- Auto-upload inline images to WeChat image hosting
- Auto-crop cover to 900x383
- Finance data auto-coloring (green up, red down)
- Lazy credential loading — import without auth
- Pure stdlib + Pillow, zero external dependencies

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure credentials
cp creds.example.py creds.py
# Edit creds.py with your AppID and AppSecret

# 3. Publish (creates a draft)
python3 publish_generic.py templates/apple-minimalist/example.json
```

Output:
```json
{"success": true, "draft_id": "BONXQtyHTyt...", "style": "apple-minimalist",
 "message": "草稿创建成功，请到公众号后台手动发布"}
```

Log in to mp.weixin.qq.com → Content Management → Drafts → Publish manually.

## Input Format

See [README.md](README.md) for full JSON schema documentation.

## Known Limitations

- **Personal subscription accounts cannot publish via API** — returns 48001. Drafts must be published manually. This is a platform limitation.
- **IP whitelist** — server IP must be added at mp.weixin.qq.com → Settings → Basic Config → IP Whitelist.
- **Image upload limits** — Inline images use `/media/uploadimg` (no quota), covers use `/material/add_material` (counts against permanent media quota).

## License

MIT — use freely, no warranty.
