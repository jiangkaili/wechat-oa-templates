# 贡献指南 Contributing

感谢你对 wechat-oa-templates 的兴趣！欢迎提交新模板、修复 bug 或改进文档。

## 提交新模板

1. 在 `templates/` 下创建你的模板目录：

```
templates/your-style/
├── composer.py      # 必需：定义 compose_html(article_data, image_urls) -> str
├── example.json     # 必需：示例文章（使用统一格式）
└── README.md        # 必需：风格说明、配色表
```

2. `composer.py` 必须导入共享工具：

```python
"""Your style — describe the aesthetic."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared import colorUpDown, parse_item


def compose_html(article_data, image_urls):
    """Returns HTML string for WeChat article body."""
    ...
```

3. `example.json` 使用与其他模板相同的字段结构（参考 `templates/apple-minimalist/example.json`）。

4. 遵守微信 CSS 限制：
   - 只用 inline style
   - 不用 `position` / `flex` / `grid` / `display`
   - 不用 `<style>` 块和 `<script>`
   - 可用标签：`<section>`, `<p>`, `<span>`, `<img>`

5. 运行验证：

```bash
python3 -m pyflakes templates/your-style/composer.py
python3 -c "
import publish_generic as p
fn = p.load_composer('your-style')
html = fn({'title':'Test','vol':'V.1','sections':[{'heading':'Test','items':['Hi<br/>Body（6月28日）'],'images':[]}],'trends':[]}, {'cover':''})
assert len(html) > 100
print('OK')
"
```

## 提交 Bug 报告

请使用 GitHub Issues，描述：
- 复现步骤
- 期望行为 vs 实际行为
- Python 版本、操作系统

## 代码风格

- pyflakes 零警告
- f-string 优于 % 或 .format()
- 函数有 docstring
- 公开函数有类型提示（可选但推荐）

## License

提交即表示你同意以 MIT 许可发布你的贡献。
