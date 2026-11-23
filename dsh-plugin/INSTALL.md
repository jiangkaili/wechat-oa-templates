# 给别人的安装与使用指南

这份文档面向**第一次使用**的人。插件本身只有 8 个文件，但它驱动的是一个真实的发布流程，所以准备工作分两部分：**装插件**（几分钟）和**准备发布会话**（仓库、依赖、凭据、白名单，十几分钟）。

> 已经会用 `publish_generic.py` 的人，可以直接跳到 [第 1 步](#第-1-步装插件)。

---

## 前置条件

| 需要 | 说明 |
|---|---|
| DeepSeek Harness 桌面版 | `>= 0.2.2-rc.5`（插件的 `engines.dsh` 声明了范围） |
| 一个微信公众号 | 能建草稿。**个人订阅号也可以**，只是最后一步要在后台手点发布 |
| Python 3.10+ | 跑模板渲染和发布脚本 |
| git | 拉取模板仓库 |

公众号的接口能力先看清楚，后面所有"为什么失败"都源自这里：

| 你的账号 | 能建草稿 | 能 API 发布 |
|---|---|---|
| 个人订阅号（未认证） | 通常可以 | ❌ 返回 `48001`，去后台手点 |
| 个人订阅号（已认证） | ✅ | ❌ |
| 企业 / 个体工商户（已认证） | ✅ | ✅ |

---

## 第 1 步：装插件

1. 打开 DSH 的 **Plugins** 页面，切到 **Discover（发现）** 标签
2. 添加索引 URL：

   ```
   https://cdn.jsdelivr.net/gh/jiangkaili/wechat-oa-templates@main/market/index.json
   ```

   如果 jsDelivr 打不开，用这个备用：

   ```
   https://raw.githubusercontent.com/jiangkaili/wechat-oa-templates/main/market/index.json
   ```

3. 列表里会出现「**公众号发布**」，点安装
4. 安装后确认插件列表里有 `dsh-wechat-publisher`，状态是启用

安装来源被**锁死到一个具体 commit**，作者后续改仓库不会影响你已经装好的版本。

也可以直接让 agent 装：告诉它「从 <索引 URL> 装 dsh-wechat-publisher 这个插件」。

---

## 第 2 步：准备模板仓库

插件**不内置**排版引擎，它调用仓库里的 `publish_generic.py` 和 `templates/`。

```bash
git clone https://github.com/jiangkaili/wechat-oa-templates.git
cd wechat-oa-templates
```

**Windows（PowerShell）：**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**macOS / Linux：**

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

依赖只有两个：`Pillow`、`requests`。

> 建议克隆到**路径不含空格和中文**的地方，例如 `D:\work\wechat-oa-templates` 或 `~/work/wechat-oa-templates`。

---

## 第 3 步：告诉插件仓库在哪

插件默认 `repoPath` 是作者的路径，你得改成自己的。

编辑你的 profile patch 文件：

```
$DSH_HOME/profiles/<profile>/cordis.patch.yml
```

Windows 默认在 `C:\Users\<你>\.dsh\profiles\desktop\cordis.patch.yml`。

在**顶层数组**里加一条（或者如果已经有同名 `id` 的条目，就直接改它的 `config`）：

```yaml
- id: wechat-publisher
  name: dsh-wechat-publisher
  config:
    repoPath: D:\work\wechat-oa-templates
    defaultStyle: apple-minimalist
```

可用的 `defaultStyle`：`apple-minimalist`、`dark-mode`、`warm-paper`、`card-layout`、`gradient-header`、`tech-terminal`。

改完重启 DSH（或重新启用插件）生效。

---

## 第 4 步：填公众号凭据

公众号后台 → **设置与开发 → 基本配置**，拿到 `AppID` 和 `AppSecret`。

```bash
cp creds.example.py creds.py
```

编辑 `creds.py`：

```python
APP_ID = "wx1234567890abcdef"
APP_SECRET = "0123456789abcdef0123456789abcdef"
```

`creds.py` 已在仓库的 `.gitignore` 里，不会误提交。

> 插件**不接管凭据**。它把环境原样透传给子进程，`publish_generic.py` 自己读 `WECHAT_APP_ID`/`WECHAT_APP_SECRET` 环境变量，没有才回落到 `creds.py`。所以你也可以用环境变量，凭据不用落盘。

---

## 第 5 步：加 IP 白名单

公众号后台 → **设置与开发 → 基本配置 → IP 白名单**，加入你电脑的**公网出口 IP**。

查自己的公网 IP：

```powershell
(Invoke-WebRequest https://ifconfig.me/ip -UseBasicParsing).Content
```

```bash
curl -s https://ifconfig.me/ip
```

**这一步最容易反悔**：家用宽带 IP 会变（重启光猫、运营商重新分配），变了以后所有请求返回 `40164`，得回后台改白名单。GitHub Actions 之类的云 runner IP 不固定，**不能用来跑这个**——所以插件设计成在本地跑。

---

## 第 6 步：先绕过插件验证一次

在装插件之前或排除故障时，直接跑仓库脚本，能最快定位是「凭据问题」还是「插件问题」：

```powershell
cd D:\work\wechat-oa-templates
.\.venv\Scripts\python.exe publish_generic.py examples\ai_frontier_sample.json
```

成功会打印一行 JSON：

```json
{"success": true, "draft_id": "...", "style": "apple-minimalist",
 "message": "草稿创建成功，请到公众号后台手动发布"}
```

然后去 **mp.weixin.qq.com → 内容管理 → 草稿箱** 看有没有新草稿。有就说明凭据和白名单都没问题，可以回去用插件了。

---

## 第 7 步：正式使用

在 DSH 里直接说需求，agent 会调 `wechat_publish`。推荐两段式：

**先看排版（不上传任何东西）**

> 帮我把下面这篇文章用 `warm-paper` 模板排一下，先预览，不要发。
> 标题：…

agent 会返回一个 `previewPath`，用浏览器打开确认排版。**质控闸门在这一步也会跑**，所以排版和质检一次搞定。

**确认后再建草稿**

> 排版没问题，建草稿吧。

返回 `draft_id`，然后去公众号后台草稿箱点发布。

---

## 常见错误码

| errcode | 含义 | 怎么办 |
|---|---|---|
| `40164` | IP 不在白名单 | 把当前公网 IP 加进去（第 5 步） |
| `48001` | 该接口无权限 | 个人号不能 API 发布，去后台手动发布；这也是插件返回 `draft_id` 的原因 |
| `40013` | AppID 无效 | 检查 `creds.py` 或环境变量 |
| `40125` | AppSecret 无效 | 同上；注意别把两个字段写反 |
| `40001` | access_token 无效 | 通常重跑一次即可（插件每次调用都重新取 token） |
| `45009` | 接口调用次数超限 | 等第二天，或减少调用 |

插件还会单独报两类失败，那不是微信的问题：

- **`Blocked by the … gate`** —— 质控闸门拦下了，输出里会写明哪条内容缺来源、哪张图不合格
- **`wechat-oa-templates not found at …`** —— `repoPath` 配错了，或那个目录没有 `publish_generic.py`

---

## 质控闸门怎么选

| 闸门 | 检查对象 | 默认 |
|---|---|---|
| `images` | **这篇**文章的配图 | ✅ 开 |
| `facts` | **这篇**文章的来源与事实 | ✅ 开 |
| `typo` | **仓库自己的** `templates/`、`examples/`、README | ⬜ 关 |

`typo` 默认关，因为它的作用域是仓库内容而不是你正在发的文章——只有你改了仓库模板时才需要它。

`facts` 要求 `sections[].sources` 与 `items` **等长**，否则第 1 轮就拦下。

---

## 卸载

1. Plugins 页面删掉 `dsh-wechat-publisher`
2. 删掉第 3 步加的那条 profile patch 配置
3. 模板仓库可以留着（`publish_generic.py` 单独也能用）

---

## 一句话总结

**插件只负责调度，不负责魔法。** 它把「跑闸门 → 套模板 → 建草稿」串成一次调用，但仓库、依赖、凭据、白名单这四样必须你自己准备好——这四样在插件出现之前就要准备好，插件没有让它们变复杂，也没有让它们变简单。
