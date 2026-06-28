# 微信公众号模板库 WeChat OA Template Gallery

> 一套可插拔的微信公众号文章排版模板，配合 Python 发布脚本，自动创建草稿到公众号后台。

> A pluggable WeChat Official Account article template gallery with a Python publisher that auto-creates drafts via the WeChat MP API.

[English](README.en.md) | 中文

---

## 预览 Preview

![模板画廊](docs/images/hero_templates.png)

6 种风格，同一份内容数据，一键切换：

| 模板 | 风格 | 背景 | 适合场景 |
|------|------|------|----------|
| apple-minimalist | Apple 极简风 | 纯白 #FFFFFF | 科技资讯、每日简报 |
| dark-mode | 暗黑模式 | 深色 #1D1D1F | 技术博客、开发者周刊 |
| warm-paper | 暖纸期刊风 | 米色 #FAF9F5 | 人文、深度阅读 |
| card-layout | 卡片布局 | 白底 + 灰卡 | 产品更新、多栏目 |
| gradient-header | 渐变头部 | 紫色渐变 + 白底 | 品牌推广、活动预告 |
| tech-terminal | 终端风格 | GitHub Dark | 极客文化、开源项目 |

实际效果（Apple 极简风 · AI 简报）：

![实际效果](docs/images/preview_full.png)

## 特性 Features

- 6 种内置模板，`"style"` 字段一键切换
- 模板可插拔：放一个 `composer.py` 到 `templates/your-style/` 即可
- 统一 JSON 输入格式，模板间无缝切换
- 自动上传内联图片到微信图床
- 封面自动裁剪 900x383
- 美股/财经数据自动标色（涨绿跌红）
- 凭证懒加载，import 不触发认证
- 纯标准库 + Pillow，零外部依赖

## 快速开始 Quickstart

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置凭证
cp creds.example.py creds.py
# 编辑 creds.py，填入你的 AppID 和 AppSecret

# 3. (可选) 配置个人默认值
cp config.example.json config.json
# 编辑 config.json，设置署名和默认模板

# 4. 发布文章（创建草稿）
python3 publish_generic.py templates/apple-minimalist/example.json
```

输出：
```json
{"success": true, "draft_id": "BONXQtyHTyt...", "style": "apple-minimalist",
 "message": "草稿创建成功，请到公众号后台手动发布"}
```

登录 mp.weixin.qq.com → 内容管理 → 草稿箱 → 手动发布。

## 输入格式 Input Format

```json
{
  "style": "apple-minimalist",
  "title": "新闻关键词，一句解读",
  "digest": "一句话摘要",
  "author": "你的署名",
  "cover": {
    "bg_image": "https://example.com/cover-image.jpg"
  },
  "sections": [
    {
      "heading": "前沿速递",
      "items": [
        "标题<br/>正文内容，150-250字。（6月27日）"
      ],
      "images": [
        "https://example.com/article-image.jpg"
      ]
    }
  ],
  "trends": [
    "趋势1：分析+影响",
    "趋势2：分析+影响"
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| style | string | 否 | 模板名，默认 apple-minimalist |
| title | string | 是 | 文章标题 |
| digest | string | 否 | 摘要，显示在消息列表 |
| author | string | 否 | 署名，默认读 config.json → 环境变量 WECHAT_AUTHOR → "Your Name" |
| cover.bg_image | string | 否 | 封面图 URL，自动裁剪 900x383 |
| sections[].heading | string | 是 | 栏目标题 |
| sections[].items[] | string | 是 | 正文，用 `<br/>` 分隔标题和正文 |
| sections[].images[] | string | 否 | 内联图片 URL，与 items 等长 |
| trends[] | string | 否 | 趋势观察栏目 |

## 自定义模板 Custom Template

创建 `templates/your-style/composer.py`：

```python
def compose_html(article_data, image_urls):
    """Returns HTML string for WeChat article body."""
    import time, re

    sections = article_data.get("sections", [])
    parts = []

    for section in sections:
        heading = section["heading"]
        for item in section.get("items", []):
            head, body = item.split("<br/>", 1) if "<br/>" in item else (item, "")
            parts.append(f'<p style="font-size:16px;">{head}</p>')
            parts.append(f'<p style="font-size:15px;">{body}</p>')

    return "\n".join(parts)
```

JSON 中设 `"style": "your-style"` 即可使用。

### 微信 CSS 限制

- 只能用 inline style (`style="..."`)
- 不能用 `position` / `flex` / `grid` / `display`
- 不能用 `<style>` 块和 `<script>`
- 可用标签：`<section>`, `<p>`, `<span>`, `<img>`
- 可用属性：`background-color`, `padding`, `margin`, `border`, `font-size`, `color`, `text-align`, `border-radius`, `box-shadow`

## 自动化 Automation

### Crontab
```bash
# 每天 10:00 发布 AI 简报
0 10 * * * cd /path/to/wechat_publisher && python3 publish_generic.py /tmp/today_ai.json
```

### Hermes Agent / AI Agent
配合 AI Agent（如 Hermes Agent）自动搜索新闻、生成 JSON、调用脚本。详见 [examples/](examples/) 目录。

### GitHub Actions
注意：GitHub Runner IP 不固定，无法加入微信 IP 白名单。建议用自建服务器或本地 cron。

## 已知限制 Known Limitations

- **个人订阅号不能 API 直接发布** — 返回 48001，只能创建草稿后手动发布。这是平台限制，不是 bug。
- **IP 白名单** — 服务器 IP 必须加入 mp.weixin.qq.com → 设置与开发 → 基本配置 → IP 白名单。
- **图片上传限制** — 内联图片用 `/media/uploadimg`（不占素材库配额），封面用 `/material/add_material`（占永久素材配额）。

## 项目结构 Project Layout

```
wechat_publisher/
├── publish_generic.py       # 发布脚本 (主入口)
├── clean_drafts.py          # 草稿批量清理工具
├── creds.example.py         # 凭证模板
├── requirements.txt         # Python 依赖
├── templates/               # 模板画廊
│   ├── apple-minimalist/    # Apple 极简风
│   ├── dark-mode/           # 暗黑模式
│   ├── warm-paper/          # 暖纸期刊风
│   ├── card-layout/         # 卡片布局
│   ├── gradient-header/     # 渐变头部
│   └── tech-terminal/       # 终端风格
├── examples/                # 完整文章示例
└── docs/
    └── images/              # 模板预览图
```

## 贡献模板 Contributing

欢迎提交新模板！每个模板需要：

1. `templates/your-style/composer.py` — 定义 `compose_html(article_data, image_urls) -> str`
2. `templates/your-style/example.json` — 示例文章
3. `templates/your-style/README.md` — 风格说明、配色表

## License

MIT — 随便用，不负责。
