#!/usr/bin/env python3
"""WeChat OA draft publisher with pluggable template system.

Reads article JSON from file or stdin, generates cover, uploads images,
composes HTML using a user-selected template, creates a WeChat draft.

Input JSON format:
{
  "title": "Article title",
  "digest": "Short summary",
  "style": "apple-minimalist",
  "author": "Your Name",
  "vol": "VOL.001",
  "cover": {"bg_image": "https://example.com/image.jpg"},
  "sections": [
    {
      "heading": "Section Title",
      "items": ["Title<br/>Body text.（6月27日）", ...],
      "images": ["https://...", null, ...]
    }
  ],
  "trends": ["Trend 1", "Trend 2"]
}

The "style" field selects a template from templates/<style>/composer.py.
Default: "apple-minimalist".
"""
import os, sys, json, io, time, urllib.request
from PIL import Image

# ==================== Credentials (lazy) ====================

_creds = None

def _load_creds():
    """Load WeChat credentials lazily — env vars first, then creds.py fallback."""
    global _creds
    if _creds is not None:
        return _creds
    app_id = os.environ.get("WECHAT_APP_ID", "")
    app_secret = os.environ.get("WECHAT_APP_SECRET", "")
    if not app_id or not app_secret:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "creds",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "creds.py"))
            creds_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(creds_mod)
            app_id = app_id or creds_mod.APP_ID
            app_secret = app_secret or creds_mod.APP_SECRET
        except Exception as e:
            raise RuntimeError(f"Cannot load credentials: {e}")
    _creds = (app_id, app_secret)
    return _creds


BASE = "https://api.weixin.qq.com/cgi-bin"


# ==================== Config (lazy) ====================

_config = None

def _load_config():
    """Load config.json if it exists (gitignored, for personal defaults)."""
    global _config
    if _config is not None:
        return _config
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                _config = json.load(f)
        except Exception:
            _config = {}
    else:
        _config = {}
    return _config

def _cfg(key, default=None):
    """Get a config value with fallback."""
    return _load_config().get(key, default)


# ==================== WeChat API ====================

def get_token():
    app_id, app_secret = _load_creds()
    url = f"{BASE}/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    resp = urllib.request.urlopen(url, timeout=15)
    data = json.loads(resp.read())
    if "access_token" not in data:
        print(json.dumps({"success": False, "error": f"Token failed: {data}"}))
        sys.exit(1)
    return data["access_token"]


def upload_permanent(token, image_bytes, filename="cover.png"):
    """Upload permanent material (cover/thumbnail). Returns (media_id, url)."""
    boundary = "----FormBoundary" + str(int(time.time()))
    body = f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'.encode()
    body += b'Content-Type: image/png\r\n\r\n'
    body += image_bytes
    body += f"\r\n--{boundary}--\r\n".encode()
    url = f"{BASE}/material/add_material?access_token={token}&type=image"
    req = urllib.request.Request(url, data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    if "media_id" not in result:
        print(json.dumps({"success": False, "error": f"Upload failed: {result}"}))
        sys.exit(1)
    return result["media_id"], result.get("url", "")


def upload_content_image(token, image_bytes, filename="section.png"):
    """Upload content image (inline in article body). Returns WeChat CDN URL."""
    boundary = "----FormBoundary" + str(int(time.time()))
    body = f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'.encode()
    body += b'Content-Type: image/png\r\n\r\n'
    body += image_bytes
    body += f"\r\n--{boundary}--\r\n".encode()
    url = f"{BASE}/media/uploadimg?access_token={token}"
    req = urllib.request.Request(url, data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    if "url" not in result:
        print(json.dumps({"success": False, "error": f"Content image upload failed: {result}"}))
        sys.exit(1)
    return result["url"]


def create_draft(token, title, content_html, digest, thumb_media_id, author=""):
    """Create a WeChat draft. Returns media_id (draft ID)."""
    if not author:
        author = os.environ.get("WECHAT_AUTHOR", "Your Name")
    article = {"articles": [{
        "title": title,
        "author": author,
        "digest": digest,
        "content": content_html,
        "content_source_url": "",
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }]}
    url = f"{BASE}/draft/add?access_token={token}"
    req = urllib.request.Request(url,
            data=json.dumps(article, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    if "media_id" not in result:
        print(json.dumps({"success": False, "error": f"Draft creation failed: {result}"}))
        sys.exit(1)
    return result["media_id"]


# ==================== Cover Generation ====================

def generate_cover(cover_config=None):
    """Generate cover — download bg_image, crop to 900x383. No text overlay."""
    W, H = 900, 383
    cc = cover_config or {}
    bg_image_url = cc.get("bg_image", "")

    img = Image.new('RGB', (W, H), '#FFFFFF')

    if bg_image_url:
        try:
            req = urllib.request.Request(bg_image_url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=15)
            bg_bytes = resp.read()
            bg_img = Image.open(io.BytesIO(bg_bytes)).convert('RGB')
            bg_ratio = bg_img.width / bg_img.height
            target_ratio = W / H
            if bg_ratio > target_ratio:
                new_w = int(bg_img.height * target_ratio)
                left = (bg_img.width - new_w) // 2
                bg_img = bg_img.crop((left, 0, left + new_w, bg_img.height))
            else:
                new_h = int(bg_img.width / target_ratio)
                top = (bg_img.height - new_h) // 3
                bg_img = bg_img.crop((0, top, bg_img.width, top + new_h))
            bg_img = bg_img.resize((W, H), Image.LANCZOS)
            img.paste(bg_img, (0, 0))
        except Exception:
            pass

    return img


# ==================== Template Loader ====================

def load_composer(style_name="apple-minimalist"):
    """Load a template composer from templates/<style>/composer.py.

    Each composer must define: compose_html(article_data, image_urls) -> str
    """
    import importlib.util
    script_dir = os.path.dirname(os.path.abspath(__file__))

    def _try_load(name):
        path = os.path.join(script_dir, "templates", name, "composer.py")
        if not os.path.exists(path):
            return None
        spec = importlib.util.spec_from_file_location(f"templates.{name}.composer", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.compose_html

    style_name = style_name or "apple-minimalist"
    compose = _try_load(style_name)
    if compose is None and style_name != "apple-minimalist":
        print(f"WARNING: Template '{style_name}' not found, falling back to apple-minimalist", file=sys.stderr)
        compose = _try_load("apple-minimalist")
    if compose is None:
        raise RuntimeError(f"No templates found. Expected templates/apple-minimalist/composer.py")
    return compose


# ==================== Main ====================

def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            article_data = json.loads(f.read())
    else:
        article_data = json.loads(sys.stdin.read())

    today = time.strftime("%Y年%m月%d日")
    title = article_data.get("title", f"Article | {today}")
    digest = article_data.get("digest", "")
    style = article_data.get("style", article_data.get("article_type", _cfg("default_style", "apple-minimalist")))
    author = article_data.get("author", os.environ.get("WECHAT_AUTHOR", _cfg("author", "Your Name")))

    print(f"=== {author} · 草稿创建 (style: {style}) ===", file=sys.stderr)
    print(f"标题: {title}", file=sys.stderr)

    # 1. Get token
    token = get_token()
    print(f"Token: OK", file=sys.stderr)

    # 2. Generate and upload cover
    cover_config = article_data.get("cover", {})
    cover_img = generate_cover(cover_config)
    buf = io.BytesIO(); cover_img.save(buf, format='PNG')
    thumb_media_id, cover_url = upload_permanent(token, buf.getvalue(), "cover.png")
    print(f"封面: OK", file=sys.stderr)

    image_urls = {"cover": cover_url}
    sections = article_data.get("sections", [])

    # 3. Download and upload inline content images
    for section in sections:
        imgs = section.get("images", [])
        for i, img_url in enumerate(imgs):
            if not img_url or img_url.startswith("https://mmbiz"):
                continue
            try:
                req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
                resp = urllib.request.urlopen(req, timeout=15)
                img_bytes = resp.read()
                wechat_url = upload_content_image(token, img_bytes, f"item_{i}.jpg")
                imgs[i] = wechat_url
                print(f"  图片上传: {img_url[:50]}... -> OK", file=sys.stderr)
            except Exception as e:
                print(f"  图片上传失败: {img_url[:50]}... -> {e}", file=sys.stderr)
                imgs[i] = None

    # 4. Compose HTML using selected template
    compose_html = load_composer(style)
    html = compose_html(article_data, image_urls)
    print(f"文章: {len(html)} chars", file=sys.stderr)

    # 5. Create draft
    draft_id = create_draft(token, title, html, digest, thumb_media_id, author)
    print(f"草稿: {draft_id}", file=sys.stderr)

    result = {
        "success": True,
        "draft_id": draft_id,
        "title": title,
        "style": style,
        "message": "草稿创建成功，请到公众号后台手动发布"
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
