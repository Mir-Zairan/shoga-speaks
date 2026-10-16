// Shoga-Speaks display mod (Claude Code 2.1.287+). Runs inside Claude Code and changes
// what is drawn; the classic hooks in hooks.json keep working without it.
//   - the "▸ English" line under a reply becomes a toggle; the other language is
//     translated on demand by a small model and folded away until asked for
//   - "en" / "tr" typed alone unfolds or folds every reply, with no Claude turn
//   - shell commands get a plain-language line under the approval dialog and the tool row
//   - technical terms in a reply get a footer; hover or press shows a simple meaning
//   - a status line shows the active language and role

import { atom, read, update } from 'claude-code'
import type { Register, EngineInterface } from 'claude-code'
import { HINT_LINE, idOf, matchCommand, entryText, findTerms, RISK_MARK } from '../scripts/lib/pure.mjs'
import COMMANDS from '../data/commands.mjs'
import GLOSSARY from '../data/glossary.mjs'
import type { ModSettings } from '../types'

const open = atom({ plugin: 'shoga-speaks', key: 'open' } as const, {} as Record<string, boolean>)
const showAll = atom({ plugin: 'shoga-speaks', key: 'showAll' } as const, false)
const glossOpen = atom({ plugin: 'shoga-speaks', key: 'glossOpen' } as const, {} as Record<string, boolean>)

const TRANSLATE_MODEL = 'haiku'
const PENDING = '…'

type $ = EngineInterface

// ---------- settings (written by the classic SessionStart hook) ----------

let cached: { at: number; value: ModSettings | null } = { at: 0, value: null }

async function shogaHome($: $): Promise<string> {
  const own = await $.env.get('SHOGA_HOME')
  if (own) return own
  const home = (await $.env.get('HOME')) || (await $.env.get('USERPROFILE')) || ''
  return `${home}/.claude/shoga-speaks`
}

async function settings($: $, fresh = false): Promise<ModSettings | null> {
  const now = await $.clock.now()
  if (!fresh && cached.value && now - cached.at < 30_000) return cached.value
  let value: ModSettings | null = null
  try {
    const inline = await $.env.get('SHOGA_STATE_JSON')
    if (inline) value = JSON.parse(inline)
    else {
      const dir = `${await shogaHome($)}/state`
      const id = String(await $.session.id()).replace(/[^\w.-]/g, '_')
      try { value = JSON.parse(await $.fs.read(`${dir}/${id}.json`)).resolved ?? null } catch {}
      if (!value) value = JSON.parse(await $.fs.read(`${dir}/latest.json`))
    }
  } catch {}
  cached = { at: now, value }
  return value
}

const isOn = (st: ModSettings | null): st is ModSettings => !!st && st.enabled !== false

async function showStatus($: $) {
  const st = await settings($)
  $.ui.status(isOn(st) ? `🦜 ${st.openLabel} · ${st.primaryRole}` : undefined)
}

// ---------- translation by a small model ----------

const inflight = new Set<string>()
// Finished translations live in memory (a render may read them; only handlers and
// finished calls write them), keyed by the reply's id.
const translations = new Map<string, string>()

// Starts a translation unless one is done or running; redraws when it lands.
function translate($: $, key: string, text: string, st: ModSettings) {
  if (translations.has(key) || inflight.has(key)) return
  inflight.add(key)
  const system = `You translate a reply from a coding assistant so the reader understands it easily.
Target: ${st.otherLabel}. Rules:
- Keep the markdown structure. Keep code, code blocks, file paths, commands, identifiers, URLs and error messages exactly as they are.
- Simple everyday words, short sentences. Same meaning, nothing added, nothing left out.
- Output only the translation.
Language guide:
${st.otherGuide}`
  void (async () => {
    let out: string
    try {
      const r = await $.model.complete({ model: TRANSLATE_MODEL, system, prompt: text, maxTokens: 4000, effort: 'low', timeoutMs: 45_000 })
      out = r.isAnswered ? r.text.trim() : `_(Translation unavailable: ${r.reason}. Type "${st.otherKey}" to ask Claude instead.)_`
    } catch {
      out = `_(Translation unavailable. Type "${st.otherKey}" to ask Claude instead.)_`
    }
    translations.set(key, out)
    inflight.delete(key)
    $.ui.invalidate('ui.render')
  })()
}

// Meanings of glossary terms in the user's language, cached across sessions.
async function glossMeanings($: $, ids: string[], st: ModSettings): Promise<Record<string, string>> {
  const out: Record<string, string> = {}
  const missing: { id: string; meaning: string }[] = []
  for (const id of ids) {
    const g = GLOSSARY.find((x: { id: string }) => x.id === id)
    if (!g) continue
    if (st.langKey === 'english') { out[id] = g.meaning; continue }
    const hit = await $.store.get(`gloss:${st.langKey}:${id}`)
    if (typeof hit === 'string') out[id] = hit
    else { out[id] = g.meaning; missing.push({ id, meaning: g.meaning }) }
  }
  if (missing.length && !inflight.has(`gloss:${missing.map((m) => m.id).join(',')}`)) {
    const key = `gloss:${missing.map((m) => m.id).join(',')}`
    inflight.add(key)
    void (async () => {
      try {
        const r = await $.model.complete({
          model: TRANSLATE_MODEL, effort: 'low', timeoutMs: 30_000, maxTokens: 1500,
          system: `Translate each line into ${st.openLabel} with simple everyday words. Keep technical terms in English. Keep the "id:" prefix. Output one line per input line, nothing else.`,
          prompt: missing.map((m) => `${m.id}: ${m.meaning}`).join('\n'),
        })
        if (r.isAnswered) {
          for (const line of r.text.split('\n')) {
            const m = line.match(/^\s*([\w+.-]+):\s*(.+)$/)
            if (m && missing.some((x) => x.id === m[1])) await $.store.set(`gloss:${st.langKey}:${m[1]}`, (m[2] ?? "").trim())
          }
          $.ui.invalidate('ui.render')
        }
      } catch {}
      inflight.delete(key)
    })()
  }
  return out
}

// ---------- hooks ----------

export const register: Register = (on) => {
  on('session.start', async ($, e, next) => {
    const result = await next(e)
    try {
      const id = String(await $.session.id()).replace(/[^\w.-]/g, '_')
      await $.fs.write(`${await shogaHome($)}/state/${id}.mod`, '1')
    } catch {}
    try { await showStatus($) } catch {}
    return result
  })

  on('prompt.submit', async ($, e, next) => {
    const st = await settings($, true)
    try { await showStatus($) } catch {}
    const cmd = e.text.trim().toLowerCase()
    if (isOn(st) && st.bilingual && (cmd === 'en' || cmd === 'tr')) {
      const now = await update($, showAll, (v) => !v)
      return { drop: now ? `🦜 ${st.otherLabel} shown under each reply. Type "${cmd}" again to fold it.` : `🦜 ${st.otherLabel} folded away.` }
    }
    return next(e)
  })

  // A plain line under the approval dialog for shell commands.
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    try {
      const st = await settings($)
      if (isOn(st) && st.explainCommands) {
        const entry = matchCommand(e.command, COMMANDS)
        if (entry) $.ui.notice(e.tool_use_id, `🦜 ${entryText(entry, st.langKey)}`)
      }
    } catch {}
    return next(e)
  })

  // The same line under the tool's row in the transcript.
  on('ui.render', { component: 'ToolUse' }, async ($, e, next) => {
    const row = await next(e)
    if (e.props.tool !== 'Bash') return row
    const st = await settings($)
    if (!isOn(st) || !st.explainCommands) return row
    const entry = matchCommand((e.props.input as { command?: string })?.command, COMMANDS)
    if (!entry) return row
    const { Box, Text } = $.ui.resolve(e)
    return (
      <Box flexDirection="column">
        {row}
        <Text dimColor>  {RISK_MARK[entry.risk as keyof typeof RISK_MARK]} {entryText(entry, st.langKey)}</Text>
      </Box>
    )
  })

  on('ui.render', { component: 'AssistantMessage' }, async ($, e, next) => {
    if (e.props.isSummary) return next(e)
    const st = await settings($)
    if (!isOn(st)) return next(e)

    const text = e.props.text
    const hasHint = st.bilingual && HINT_LINE.test(text)
    const terms = st.glossaryHover ? findTerms(text, GLOSSARY, st.knownTerms || []) : []
    if (!hasHint && !terms.length) return next(e)

    const id = idOf(text)
    const main = hasHint ? text.replace(HINT_LINE, '').trimEnd() : text
    const { Box, Text, Markdown, Button } = $.ui.resolve(e)

    // Other language: folded until pressed, or while "en"/"tr" is on.
    let other = null
    if (hasHint) {
      const isOpen = (await read($, showAll)) || (await read($, open))[id] === true
      const done = translations.get(id)
      if (isOpen && done === undefined) translate($, id, main, st)
      other = (
        <Box flexDirection="column">
          <Button
            key={`shoga-toggle-${id}`}
            plain
            dimColor
            label={`${isOpen ? '▾' : '▸'} ${st.otherLabel}`}
            onPress={async () => {
              const now = await update($, open, (o) => ({ ...o, [id]: !o[id] }))
              if (now[id]) translate($, id, main, st)
            }}
          />
          {isOpen ? (
            done === undefined
              ? <Text dimColor>  {PENDING}</Text>
              : <Markdown key={`shoga-other-${id}`} text={done} />
          ) : null}
        </Box>
      )
    }

    // Glossary footer: hover shows a card, a press shows the meaning inline.
    let glossary = null
    if (terms.length) {
      const meanings = await glossMeanings($, terms.map((t) => t.id), st)
      const shown = await read($, glossOpen)
      glossary = (
        <Box flexDirection="column">
          <Box flexDirection="row">
            <Text dimColor>📖 </Text>
            {terms.map((t) => (
              <Box key={`shoga-g-${id}-${t.id}`} marginRight={2}>
                <Button
                  key={`shoga-gb-${id}-${t.id}`}
                  plain
                  dimColor
                  label={t.term}
                  onPress={() => update($, glossOpen, (o) => ({ ...o, [`${id}:${t.id}`]: !o[`${id}:${t.id}`] }))}
                />
                <Box position="absolute" top={-3} left={0} display="none" hover={{ display: 'flex' }} borderStyle="round" paddingX={1}>
                  <Text>{t.term}: {meanings[t.id]}</Text>
                </Box>
              </Box>
            ))}
          </Box>
          {terms.filter((t) => shown[`${id}:${t.id}`]).map((t) => (
            <Text key={`shoga-gm-${id}-${t.id}`} dimColor>  {t.term}: {meanings[t.id]}</Text>
          ))}
        </Box>
      )
    }

    return (
      <Box flexDirection="column">
        <Markdown text={main} />
        {glossary}
        {other}
      </Box>
    )
  })
}
