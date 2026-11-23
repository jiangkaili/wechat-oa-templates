/**
 * wechat-publisher — DSH Host plugin.
 *
 * Drives the existing `wechat-oa-templates` pipeline instead of re-implementing
 * it: the article JSON is written to a temp directory, the repository's own
 * quality gates run first (any non-zero exit blocks publishing), and then
 * `publish_generic.py` creates the WeChat draft.
 *
 * Deliberate design points:
 *  - No dependencies. DSH packages do not resolve from a workspace bundle, so
 *    the tool definition is a plain object handed to `ctx.tools.register`.
 *  - Credentials are not handled here. `publish_generic.py` already reads
 *    WECHAT_APP_ID / WECHAT_APP_SECRET from the environment, then falls back
 *    to the repository's own `creds.py`. The plugin forwards the environment
 *    unchanged, so secrets stay where the user already keeps them.
 *  - `dryRun` composes the HTML through the repository's own template loader
 *    and writes a preview file, so the layout can be inspected before
 *    anything is uploaded to WeChat.
 */
import { spawn } from 'node:child_process'
import { existsSync, mkdirSync, readdirSync, rmSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'

export const name = 'wechat-publisher'
export const inject = ['tools']

const STYLES = [
  'apple-minimalist',
  'dark-mode',
  'warm-paper',
  'card-layout',
  'gradient-header',
  'tech-terminal',
]

const GATE_SCRIPTS = {
  typo: 'typo_check.py',
  images: 'check_image_source.py',
  facts: 'fact_check.py',
}

const DESCRIPTION = `Create a WeChat Official Account (公众号) article draft from structured data.

Runs the quality gates of the wechat-oa-templates repository, then composes the
article with the chosen visual template and creates a draft in the 公众号 backend.
The user still publishes the draft manually: the WeChat API cannot publish for
personal accounts (errcode 48001).

Use it when the user wants to turn written content into a 公众号 article. Ask for
missing required parameters (title, sections) instead of inventing them. Pass
dryRun:true first to produce an HTML preview and let the user approve the layout;
call again without dryRun to create the draft.

Requirements the plugin cannot remove: the 公众号 account must be authenticated
for the draft API, and the calling machine's public IP must be in the account's
IP whitelist (otherwise WeChat returns errcode 40164).`

/** Resolve the interpreter that owns the repository's installed dependencies. */
function resolvePython(repoPath, configured) {
  if (configured && configured.trim()) return configured.trim()
  const windows = join(repoPath, '.venv', 'Scripts', 'python.exe')
  if (existsSync(windows)) return windows
  const posix = join(repoPath, '.venv', 'bin', 'python')
  if (existsSync(posix)) return posix
  return 'python'
}

/** Run one child process and collect its output. Rejects on non-zero exit. */
function run(command, argv, options) {
  const { cwd, timeoutMs, signal, label, env } = options
  return new Promise((resolvePromise, rejectPromise) => {
    const child = spawn(command, argv, {
      cwd,
      env: env ? { ...process.env, ...env } : process.env,
      windowsHide: true,
      stdio: ['ignore', 'pipe', 'pipe'],
    })
    let stdout = ''
    let stderr = ''
    let settled = false
    const finish = (fn, value) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      fn(value)
    }
    const timer = setTimeout(() => {
      child.kill()
      finish(rejectPromise, new Error(`${label} timed out after ${timeoutMs}ms`))
    }, timeoutMs)
    if (signal) {
      if (signal.aborted) {
        child.kill()
        finish(rejectPromise, new Error(`${label} was cancelled before it started`))
      } else {
        signal.addEventListener('abort', () => {
          child.kill()
          finish(rejectPromise, new Error(`${label} was cancelled`))
        }, { once: true })
      }
    }
    child.stdout.setEncoding('utf8')
    child.stderr.setEncoding('utf8')
    child.stdout.on('data', (chunk) => { stdout += chunk })
    child.stderr.on('data', (chunk) => { stderr += chunk })
    child.on('error', (error) => finish(rejectPromise, new Error(`${label} could not start: ${error.message}`)))
    child.on('close', (code) => finish(resolvePromise, { code, stdout, stderr }))
  })
}

/** Keep the tail of a log so an error message stays readable. */
function tail(text, limit = 1200) {
  const trimmed = (text || '').trim()
  return trimmed.length <= limit ? trimmed : `…${trimmed.slice(-limit)}`
}

/** Extract the JSON result line that publish_generic.py prints on stdout. */
function lastJsonLine(stdout) {
  const lines = (stdout || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean)
  for (let index = lines.length - 1; index >= 0; index -= 1) {
    if (lines[index].startsWith('{')) {
      try { return JSON.parse(lines[index]) } catch { /* keep looking */ }
    }
  }
  return undefined
}

const COMPOSE_ONLY = `
import json, sys
sys.path.insert(0, sys.argv[1])
import publish_generic
with open(sys.argv[2], encoding="utf-8") as handle:
    data = json.load(handle)
compose = publish_generic.load_composer(data.get("style") or "apple-minimalist")
html = compose(data, {"cover": ""})
with open(sys.argv[3], "w", encoding="utf-8") as handle:
    handle.write(html)
print(len(html))
`

export function apply(ctx, config) {
  const settings = config || {}
  const repoPath = resolve(settings.repoPath || '.')
  const timeoutMs = Number(settings.timeoutMs) > 0 ? Number(settings.timeoutMs) : 240000
  const defaultStyle = STYLES.includes(settings.defaultStyle) ? settings.defaultStyle : STYLES[0]
  // Work inside the workspace, not the OS temp directory: a sandboxed child
  // process may be denied write access to %TEMP% while the repository path is
  // writable. The directory is created on demand and is safe to delete.
  const workRoot = resolve(settings.workDir || join(repoPath, '.dsh-work'))
  // Python on Windows defaults to the ANSI code page for stdout; force UTF-8 so
  // the Chinese gate output is not mojibake when Node decodes it.
  const childEnv = {
    TEMP: workRoot,
    TMP: workRoot,
    TMPDIR: workRoot,
    PYTHONIOENCODING: 'utf-8',
    PYTHONUTF8: '1',
  }
  const configuredGates = Array.isArray(settings.gates) && settings.gates.length
    ? settings.gates.filter((gate) => gate in GATE_SCRIPTS)
    : ['images', 'facts']

  ctx.tools.register({
    name: 'wechat_publish',
    description: DESCRIPTION,
    timeoutMs,
    parameters: {
      type: 'object',
      additionalProperties: false,
      required: ['title', 'sections'],
      properties: {
        title: { type: 'string', description: 'Article title shown in the message list.' },
        digest: { type: 'string', description: 'One-sentence summary shown under the title.' },
        author: { type: 'string', description: 'Byline. Falls back to the repository config.json.' },
        style: { type: 'string', enum: STYLES, description: 'Visual template. Defaults from the plugin config.' },
        vol: { type: 'string', description: 'Issue label such as "AI.001".' },
        coverImage: { type: 'string', description: 'Public URL of the cover image; cropped to 900x383 automatically.' },
        sections: {
          type: 'array',
          description: 'Article sections, in display order.',
          items: {
            type: 'object',
            additionalProperties: false,
            required: ['heading', 'items'],
            properties: {
              heading: { type: 'string', description: 'Section heading.' },
              items: {
                type: 'array',
                items: { type: 'string' },
                description: 'Paragraphs. Use "<br/>" to split a bold lead from its body text.',
              },
              images: {
                type: 'array',
                items: { type: 'string' },
                description: 'Inline image URLs, positionally aligned with items. Empty string to skip one.',
              },
              sources: {
                type: 'array',
                items: { type: 'string' },
                description: 'Original source URLs, aligned with items. Required by the facts gate.',
              },
            },
          },
        },
        trends: { type: 'array', items: { type: 'string' }, description: 'Closing trend observations.' },
        gates: {
          type: 'array',
          items: { type: 'string', enum: ['typo', 'images', 'facts'] },
          description: 'Quality gates to run. Default: images + facts, which inspect this article. "typo" lints the repository\'s own templates/READMEs instead, so it only applies when the repository was edited.',
        },
        noNetwork: {
          type: 'boolean',
          description: 'Pass --no-network to the image and facts gates for an offline check.',
        },
        dryRun: {
          type: 'boolean',
          description: 'Compose the HTML preview only. Gates still run; nothing is uploaded to WeChat.',
        },
      },
    },
    output: {
      schema: {
        type: 'object',
        additionalProperties: false,
        required: ['success', 'mode', 'style', 'gates', 'message'],
        properties: {
          success: { type: 'boolean' },
          mode: { type: 'string' },
          style: { type: 'string' },
          message: { type: 'string' },
          draftId: { type: 'string' },
          previewPath: { type: 'string' },
          htmlLength: { type: 'integer' },
          gates: {
            type: 'array',
            items: {
              type: 'object',
              additionalProperties: false,
              required: ['name', 'passed'],
              properties: {
                name: { type: 'string' },
                passed: { type: 'boolean' },
                detail: { type: 'string' },
              },
            },
          },
        },
      },
      render: (_args, value) => {
        const gateLine = value.gates.length
          ? value.gates.map((gate) => `${gate.passed ? 'PASS' : 'FAIL'} ${gate.name}`).join(' · ')
          : 'no gates'
        const lines = [value.message, `gates: ${gateLine}`]
        for (const gate of value.gates) {
          if (!gate.passed && gate.detail) lines.push(`--- ${gate.name} ---`, gate.detail)
        }
        if (value.draftId) lines.push(`draft_id: ${value.draftId}`)
        if (value.previewPath) lines.push(`preview: ${value.previewPath}`)
        return [{ type: 'text', text: lines.join('\n') }]
      },
    },
    async execute(args, exec) {
      if (!existsSync(repoPath)) {
        throw new Error(`wechat-oa-templates not found at ${repoPath}. Set repoPath on the wechat-publisher plugin row.`)
      }
      const publisher = join(repoPath, 'publish_generic.py')
      if (!existsSync(publisher)) {
        throw new Error(`${publisher} is missing: repoPath must point at a wechat-oa-templates checkout.`)
      }
      const python = resolvePython(repoPath, settings.pythonExe)

      const style = args.style || defaultStyle
      const article = {
        style,
        title: args.title,
        digest: args.digest ?? '',
        sections: args.sections,
      }
      if (args.author) article.author = args.author
      if (args.vol) article.vol = args.vol
      if (args.coverImage) article.cover = { bg_image: args.coverImage }
      if (Array.isArray(args.trends) && args.trends.length) article.trends = args.trends

      const workDir = join(workRoot, `run-${Date.now()}`)
      mkdirSync(workDir, { recursive: true })
      // Keep the directory bounded: each call leaves an article JSON and often a
      // preview behind, and nothing prunes them otherwise.
      try {
        const previous = readdirSync(workRoot, { withFileTypes: true })
          .filter((entry) => entry.isDirectory() && entry.name.startsWith('run-'))
          .map((entry) => entry.name)
          .sort()
        for (const stale of previous.slice(0, Math.max(0, previous.length - 5))) {
          rmSync(join(workRoot, stale), { recursive: true, force: true })
        }
      } catch { /* pruning is best-effort and must never fail a publish */ }
      const articlePath = join(workDir, 'article.json')
      writeFileSync(articlePath, JSON.stringify(article, null, 2), 'utf8')

      // ---- quality gates: a non-zero exit blocks both preview and publish ----
      // Running them in preview mode too means a layout review and a gate run
      // can happen in one call, before anything touches the WeChat API.
      const gates = []
      {
        const selected = Array.isArray(args.gates) ? args.gates.filter((gate) => gate in GATE_SCRIPTS) : configuredGates
        for (const gate of selected) {
          const script = join(repoPath, GATE_SCRIPTS[gate])
          if (!existsSync(script)) {
            gates.push({ name: gate, passed: false, detail: `${GATE_SCRIPTS[gate]} is missing` })
            break
          }
          // typo_check.py lints the repository's own content (templates, examples,
          // READMEs) — it does not read an arbitrary article file. The image and
          // fact gates do take the article JSON.
          const argv = gate === 'typo'
            ? [script, repoPath]
            : [script, articlePath, ...(args.noNetwork ? ['--no-network'] : [])]
          const result = await run(python, argv, {
            cwd: repoPath,
            timeoutMs,
            signal: exec.signal,
            label: `gate ${gate}`,
            env: childEnv,
          })
          gates.push({
            name: gate,
            passed: result.code === 0,
            detail: tail(result.stdout || result.stderr, 600),
          })
          if (result.code !== 0) {
            return {
              success: false,
              mode: 'gate-blocked',
              style,
              gates,
              message: `Blocked by the ${gate} gate. Fix the findings, then publish again.`,
            }
          }
        }
      }
      // ---- compose-only preview ----
      if (args.dryRun) {
        const previewPath = join(workDir, 'preview.html')
        const result = await run(python, ['-c', COMPOSE_ONLY, repoPath, articlePath, previewPath], {
          cwd: repoPath,
          timeoutMs,
          signal: exec.signal,
          label: 'compose',
          env: childEnv,
        })
        if (result.code !== 0) {
          throw new Error(`Composing the preview failed:\n${tail(result.stderr)}`)
        }
        const htmlLength = Number.parseInt((result.stdout || '0').trim(), 10) || 0
        return {
          success: true,
          mode: 'preview',
          style,
          gates,
          previewPath,
          htmlLength,
          message: `Preview written for the "${style}" template. Open it in a browser and approve the layout.`,
        }
      }

      // ---- create the WeChat draft ----
      const result = await run(python, [publisher, articlePath], {
        cwd: repoPath,
        timeoutMs,
        signal: exec.signal,
        label: 'publish',
        env: childEnv,
      })
      const parsed = lastJsonLine(result.stdout)
      if (result.code !== 0 || !parsed || parsed.success !== true) {
        const reason = parsed?.error ?? tail(result.stderr || result.stdout)
        throw new Error(`Creating the draft failed:\n${reason}`)
      }
      return {
        success: true,
        mode: 'draft',
        style: parsed.style || style,
        gates,
        draftId: String(parsed.draft_id ?? ''),
        message: `${parsed.message || 'Draft created.'} Open mp.weixin.qq.com → 内容管理 → 草稿箱 to publish it.`,
      }
    },
  })
}
