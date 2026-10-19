// Shoga-Speaks display mod (Claude Code 2.1.287+). Runs inside Claude Code and changes
// what is drawn; the classic hooks in hooks.json keep working without it.
//   - the "▸ English" line under a reply becomes a toggle; the other language is
//     translated on demand by a small model and folded away until asked for
//   - "en" / "tr" typed alone unfolds or folds every reply, with no Claude turn
//   - a reply's story and technical part: the one the settings lead with is shown, the
//     other folded away; "tech" (or "story") unfolds or folds them all
//   - terms Claude marked or listed are highlighted inside the answer; on the terminal a
//     hover opens a short card over the reply, elsewhere a click does
//   - shell commands get a plain-language line under the approval dialog and the tool row
//   - a status line shows the active language and role

import { atom, read, update } from 'claude-code'
import type { Register, EngineInterface } from 'claude-code'
import {
  idOf, matchCommand, entryText, findTerms, RISK_MARK,
  splitLayers, markTerms, markedTerms, unmark, termId, rowAt, ensureMarks, hasMark, inlineSegments,
} from '../scripts/lib/pure.mjs'
import COMMANDS from '../data/commands.mjs'
import GLOSSARY from '../data/glossary.mjs'
import type { ModSettings } from '../types'

const open = atom({ plugin: 'shoga-speaks', key: 'open' } as const, {} as Record<string, boolean>)
const showAll = atom({ plugin: 'shoga-speaks', key: 'showAll' } as const, false)
const foldOpen = atom({ plugin: 'shoga-speaks', key: 'foldOpen' } as const, {} as Record<string, boolean>)
const foldAll = atom({ plugin: 'shoga-speaks', key: 'foldAll' } as const, false)
// The term card open on each reply: "story:<term>", "tech:<term>", "chip:<term>" or "".
const card = atom({ plugin: 'shoga-speaks', key: 'card' } as const, {} as Record<string, string>)

const TRANSLATE_MODEL = 'haiku'
const PENDING = '…'
// Term links point here; .invalid never resolves, so a modified click opens nothing real.
const TERM_URL = 'https://shoga.invalid/term/'
const MAX_TERMS = 6

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

type Term = { id: string; term: string; meaning: string }

// The terms a reply explains, with the meaning Claude gave or the glossary's: the ones it
// marked, else the ones it only listed under ▸ Terms, else glossary terms the story uses.
// A term that never appears in the text is dropped, since there is nothing to highlight.
async function termsOf($: $, story: string, tech: string, listed: { id: string; term: string; meaning: string }[], st: ModSettings): Promise<Term[]> {
  const known = new Set((st.knownTerms || []).map(termId))
  const both = `${story}\n${tech}`
  let picked: { id: string; term: string }[] = markedTerms(both)
  if (!picked.length) picked = listed.filter((t) => markedTerms(ensureMarks(both, [t])).length > 0)
  picked = picked.filter((m) => !known.has(m.id))
  if (!picked.length) {
    const found = findTerms(story, GLOSSARY, st.knownTerms || [])
    const meanings = await glossMeanings($, found.map((t: { id: string }) => t.id), st)
    return found.map((t: { id: string; term: string }) => ({ id: termId(t.term), term: t.term, meaning: meanings[t.id] ?? '' }))
      .filter((t: Term) => t.meaning && markedTerms(ensureMarks(story, [t])).length > 0)
  }
  const given = new Map(listed.map((t) => [t.id, t.meaning]))
  const fromGlossary = new Map<string, string>()
  for (const m of picked) {
    if (given.has(m.id)) continue
    const g = GLOSSARY.find((x: { id: string; term: string; aliases?: string[] }) =>
      [x.id, x.term, ...(x.aliases || [])].some((a) => termId(a) === m.id))
    if (g) fromGlossary.set(m.id, g.id)
  }
  const meanings = fromGlossary.size ? await glossMeanings($, [...fromGlossary.values()], st) : {}
  const out: Term[] = []
  for (const m of picked) {
    const meaning = given.get(m.id) ?? meanings[fromGlossary.get(m.id) ?? '']
    if (meaning) out.push({ id: m.id, term: m.term, meaning })
  }
  return out.slice(0, MAX_TERMS)
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
    // The keyword of the folded layer; the other one goes on to Claude (core/layers.md).
    const folded = st?.lead === 'technical' ? 'story' : st?.lead === 'technical-only' ? null : 'tech'
    if (isOn(st) && folded && cmd === folded) {
      const now = await update($, foldAll, (v) => !v)
      const what = folded === 'tech' ? 'Technical part' : 'Story'
      return { drop: now ? `🦜 ${what} shown under each reply. Type "${cmd}" again to fold it.` : `🦜 ${what} folded away.` }
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
    const { story, tech, terms: listed, hint } = splitLayers(text)
    const hasHint = st.bilingual && !!hint
    const hasMarks = markedTerms(`${story}\n${tech}`).length > 0
    const terms = st.termHints ? await termsOf($, story, tech, listed, st) : []
    if (!hasHint && !tech && !hasMarks && !terms.length) return next(e)

    const id = idOf(text)
    const { Box, Text, Markdown, Button } = $.ui.resolve(e)
    const cols = e.viewport?.columns ?? 80
    const width = Math.max(20, Math.min(64, cols - 4))
    // On the terminal a term opens on hover (a Text inside a Text cannot start a hover there,
    // so lines with terms are drawn word by word). Desktop, VS Code and mobile get links
    // that open the card on a click.
    const hover = e.surface === 'terminal'
    const byId = new Map(terms.map((t) => [t.id, t]))
    const pinned = (await read($, card))[id] ?? ''
    const pin = (where: string) => update($, card, (c) => ({ ...c, [id]: c[id] === where ? '' : where }))
    const marked = (md: string) => markTerms(ensureMarks(md, terms), (t) => (byId.has(termId(t)) ? `{{${t}}}` : t))

    // A term's card, drawn over the reply on a solid background; nothing below it moves.
    // A key makes a Box a hover scope, so the hidden hover card gets none.
    const cardOf = (t: Term, key: string | undefined, top: number, left: number, extra: Record<string, unknown> = {}) => (
      <Box key={key} position="absolute" top={top} left={left} width={Math.min(width, t.term.length + t.meaning.length + 6)} backgroundColor="suggestion" paddingX={1} {...extra}>
        <Text color="inverseText" wrap="wrap"><Text bold>{t.term}</Text>: {t.meaning}</Text>
      </Box>
    )

    // One line holding terms, word by word so it wraps; each term carries its hover card.
    const termLine = (name: string, line: string, n: number) => {
      const lead = line.match(/^(\s*)(?:([-*+])|(\d+[.)]))\s+/)
      const body = lead ? line.slice(lead[0].length) : line
      let col = lead ? lead[0].length : 0
      const cells: unknown[] = []
      if (lead) cells.push(<Text key={`shoga-l-${n}`}>{lead[1]}{lead[2] ? '• ' : `${lead[3]} `}</Text>)
      inlineSegments(body).forEach((seg, i) => {
        const t = seg.kind === 'term' ? byId.get(seg.id) : undefined
        if (t) {
          const at = col % Math.max(20, cols - 4)
          const w = Math.min(width, t.term.length + t.meaning.length + 6)
          const left = -Math.max(0, at + w - (cols - 2))
          cells.push(
            <Box key={`shoga-t-${id}-${name}-${n}-${i}`}>
              <Text underline color="suggestion" hover={{ inverse: true }}>{seg.text}</Text>
              {cardOf(t, undefined, 1, left, { display: 'none', hover: { display: 'flex' } })}
            </Box>,
          )
        } else {
          for (const [j, word] of (seg.text.match(/\S+\s*|\s+/g) || []).entries()) {
            cells.push(
              <Text key={`shoga-w-${n}-${i}-${j}`} bold={seg.kind === 'bold'} color={seg.kind === 'code' ? 'permission' : undefined}>{word}</Text>,
            )
          }
        }
        col += seg.text.length
      })
      return <Box key={`shoga-row-${id}-${name}-${n}`} flexDirection="row" flexWrap="wrap">{cells}</Box>
    }

    // The story or the technical part. Lines without terms stay markdown.
    const part = (name: 'story' | 'tech', md: string) => {
      if (!terms.length) return <Markdown key={`shoga-${name}-${id}`} text={unmark(md)} />
      const drawn = marked(md)
      if (hover) {
        const blocks: unknown[] = []
        let buf: string[] = []
        let fence = false
        const flush = () => {
          if (buf.join('').trim()) blocks.push(<Markdown key={`shoga-${name}-${id}-${blocks.length}`} text={unmark(buf.join('\n'))} />)
          buf = []
        }
        drawn.split('\n').forEach((line, n) => {
          if (/^\s*```/.test(line)) fence = !fence
          if (!fence && hasMark(line)) { flush(); blocks.push(termLine(name, line, n)) } else buf.push(line)
        })
        flush()
        return <Box flexDirection="column">{blocks}</Box>
      }
      const linked = markTerms(drawn, (t) => (byId.has(termId(t)) ? `[${t}](${TERM_URL}${termId(t)})` : t))
      const shown = pinned.startsWith(`${name}:`) ? byId.get(pinned.slice(name.length + 1)) : undefined
      const at = shown ? linked.indexOf(`](${TERM_URL}${shown.id})`) : -1
      return (
        <Box flexDirection="column">
          <Markdown
            key={`shoga-${name}-${id}`}
            text={linked}
            pressableLinks={terms.map((t) => TERM_URL + t.id)}
            onLinkPress={(link) => {
              const tid = link.href.slice(TERM_URL.length)
              if (byId.has(tid)) void pin(`${name}:${tid}`)
            }}
          />
          {shown && at >= 0 ? cardOf(shown, `shoga-card-${id}`, rowAt(linked, at, cols) + 1, 2) : null}
        </Box>
      )
    }

    // The layer the settings lead with is shown; the other is folded until pressed, or
    // while "tech" / "story" is on.
    const techFirst = st.lead === 'technical' && !!tech
    const [lead, rest] = techFirst ? [tech, story] : [story, tech]
    let fold = null
    if (rest) {
      const isOpen = (await read($, foldAll)) || (await read($, foldOpen))[id] === true
      fold = (
        <Box flexDirection="column">
          <Button
            key={`shoga-fold-${id}`}
            plain
            dimColor
            label={`${isOpen ? '▾' : '▸'} ${techFirst ? 'Story' : 'Technical'}`}
            onPress={() => update($, foldOpen, (o) => ({ ...o, [id]: !o[id] }))}
          />
          {isOpen ? part(techFirst ? 'story' : 'tech', rest) : null}
        </Box>
      )
    }

    // Other language: folded until pressed, or while "en"/"tr" is on.
    let other = null
    if (hasHint) {
      const plain = unmark(lead)
      const isOpen = (await read($, showAll)) || (await read($, open))[id] === true
      const done = translations.get(id)
      if (isOpen && done === undefined) translate($, id, plain, st)
      other = (
        <Box flexDirection="column">
          <Button
            key={`shoga-toggle-${id}`}
            plain
            dimColor
            label={`${isOpen ? '▾' : '▸'} ${st.otherLabel}`}
            onPress={async () => {
              const now = await update($, open, (o) => ({ ...o, [id]: !o[id] }))
              if (now[id]) translate($, id, plain, st)
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

    return (
      <Box flexDirection="column">
        {part(techFirst ? 'tech' : 'story', lead)}
        {fold}
        {other}
      </Box>
    )
  })
}
