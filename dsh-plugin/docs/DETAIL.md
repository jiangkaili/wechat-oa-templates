# 公众号发布（wechat-publisher）

把写好的内容变成微信公众号草稿。插件本身不重写排版引擎——它调度的是 **`wechat-oa-templates` 仓库里已有的 6 套模板和质控脚本**，所以你在仓库里改进模板，插件立刻受益。

## 它做什么

一次 `wechat_publish` 调用走完四步：

1. 把结构化内容写成一份文章 JSON（`title` / `digest` / `author` / `vol` / `cover` / `sections` / `trends`）
2. **串行跑质控闸门**，任何一道非 0 退出就中止，不发草稿
3. 用你选的模板把 JSON 渲染成公众号可用的内联样式 HTML
4. 调 `publish_generic.py`：取 token → 裁封面 900×383 → 上传内联图片 → 创建草稿

返回内容里有 `draft_id`，剩下的发布动作在公众号后台点一下。

## 质控闸门

约定是 **`exit 0` 才放行**。

| 闸门 | 脚本 | 检查什么 | 默认 |
|---|---|---|---|
| `images` | `check_image_source.py` | 配图三轮校验（来源水印、分辨率与体积、HTTP 可达且真图可解码） | ✅ 开 |
| `facts` | `fact_check.py` | 事实三轮核验（来源完备、来源可达、抓取正文核对锚点） | ✅ 开 |
| `typo` | `typo_check.py` | 错别字三轮扫描，但**扫的是仓库自己的 `templates/`、`examples/`、README**，不读传入的文章 | ⬜ 关 |

`typo` 默认关闭，因为它的作用域是仓库内容而非本次文章——只有你在改仓库模板时才需要它。想全跑就传 `gates: ["typo","images","facts"]`，想跳过就传 `gates: []`。

`facts` 要求 `sections[].sources` 与 `items` 等长，否则第 1 轮就会拦下。

## 预览

传 `dryRun: true` 用仓库自己的 `load_composer()` 渲染 HTML 写进工作目录，返回 `previewPath`，**不向微信上传任何东西**。

**闸门在预览时同样会跑**，所以一次调用就能同时完成「排版确认 + 质检」。

推荐流程：先 `dryRun` 确认排版，再正式调用。

## 六套模板

`apple-minimalist`（Apple 极简）、`dark-mode`（暗黑）、`warm-paper`（暖纸期刊）、`card-layout`（卡片）、`gradient-header`（渐变头部）、`tech-terminal`（终端风）。

## 配置

插件行在 `cordis.patch.yml`：

| 字段 | 默认 | 含义 |
|---|---|---|
| `repoPath` | `D:\workspace\wechat-oa-templates` | 仓库检出位置，必须是含 `publish_generic.py` 的目录 |
| `pythonExe` | 自动探测 | 解释器路径；默认用 `<repoPath>\.venv` 里的那个 |
| `defaultStyle` | `apple-minimalist` | 调用时未指定 `style` 用的模板 |
| `timeoutMs` | `240000` | 单次子进程超时 |
| `gates` | `["images","facts"]` | 默认要跑的闸门 |
| `workDir` | `<repoPath>\.dsh-work` | 每次调用的临时目录，保留最近 5 次 |

## 凭据

**插件不碰凭据。** `publish_generic.py` 自己先读环境变量 `WECHAT_APP_ID` / `WECHAT_APP_SECRET`，没有就回落到仓库根目录的 `creds.py`。插件把环境原样透传给子进程，所以密钥仍然待在你原本放置的地方。

## 已知限制

- **草稿能建，发布要手动。** 个人订阅号调 `freepublish/submit` 返回 `48001`，这是微信的平台限制，不是插件缺陷。已认证的企业/个体工商户主体才有 API 发布权限。
- **IP 白名单。** 调用方的公网 IP 必须在公众号后台的白名单里，否则返回 `40164`。家用宽带换 IP 后会重新遇到这个错误，需要去后台更新。
- **需要一份本地仓库。** 插件不内置模板和脚本，`repoPath` 指向的目录必须存在且装好 `requirements.txt`（`requests`、`Pillow`）。仓库缺失或依赖未装时会直接报错，不会静默失败。
- **工作目录写在仓库内。** 默认 `<repoPath>\.dsh-work`，因为沙箱子进程对系统 `%TEMP%` 可能没有写权限。建议把它加进仓库的 `.gitignore`。
- **未经验证的路径。** 已在 DSH 桌面版上装配并实测：工具注册、预览渲染、`images` 与 `facts` 闸门的通过/拦截分支、中文输出编码。**真实草稿创建未实测**——它依赖你的公众号凭据与 IP 白名单，需要你首次运行时确认。
