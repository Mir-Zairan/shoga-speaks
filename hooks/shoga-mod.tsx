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
  splitLayers, markTerms, markedTerms, unmark, termId, termText, ensureMarks, hasMark, inlineSegments,
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
      let web = false
      try {
        const state = JSON.parse(await $.fs.read(`${dir}/${id}.json`))
        value = state.resolved ?? null
        web = state.web === true
      } catch {}
      if (!value) value = JSON.parse(await $.fs.read(`${dir}/latest.json`))
      if (value) value = { ...value, web }
    }
    // A cloud session is read in a browser, where nothing this mod draws appears.
    if (value && (await $.env.get('CLAUDE_CODE_REMOTE')) === 'true') value = { ...value, web: true }
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

// The marker that tells the classic hooks this mod is running. It is touched on session
// start, each prompt and each shell command; an untouched one goes stale (scripts/shoga.mjs).
async function touchMarker($: $) {
  try {
    const id = String(await $.session.id()).replace(/[^\w.-]/g, '_')
    await $.fs.write(`${await shogaHome($)}/state/${id}.mod`, String(await $.clock.now()))
  } catch {}
}

export const register: Register = (on) => {
  on('session.start', async ($, e, next) => {
    const result = await next(e)
    await touchMarker($)
    try { await showStatus($) } catch {}
    return result
  })

  on('prompt.submit', async ($, e, next) => {
    await touchMarker($)
    const st = await settings($, true)
    try { await showStatus($) } catch {}
    const cmd = e.text.trim().toLowerCase()
    // Read in a browser, nothing folds: the keywords go to Claude, which answers them.
    if (st?.web) return next(e)
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
    await touchMarker($)
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

    const text = e.props.text.replace(/\r\n?/g, '\n')
    const { story, tech, terms: listed, hint } = splitLayers(text)
    const hasHint = st.bilingual && !!hint
    const hasMarks = markedTerms(`${story}\n${tech}`).length > 0
    const terms = st.termHints ? await termsOf($, story, tech, listed, st) : []
    if (!hasHint && !tech && !hasMarks && !terms.length && !listed.length) return next(e)

    // Translations are shared by equal replies; fold and card state belong to this one.
    const id = idOf(text)
    const at = `${id}:${(e as { requestId?: string }).requestId ?? ''}`
    const { Box, Text, Markdown, Button, Link } = $.ui.resolve(e)
    const cols = e.viewport?.columns ?? 80
    const width = Math.max(10, Math.min(64, cols - 4))
    // On the terminal a term opens on hover (a Text inside a Text cannot start a hover there,
    // so lines with terms are drawn word by word). Desktop, VS Code and mobile get links
    // that open the card on a click.
    const hover = e.surface === 'terminal'
    const byId = new Map(terms.map((t) => [t.id, t]))
    // A plural use ("migrations") finds its listed term ("migration").
    const termFor = (tid: string) => byId.get(tid) ?? byId.get(tid.replace(/s$/, '')) ?? byId.get(tid.replace(/es$/, ''))
    const pinned = (await read($, card))[at] ?? ''
    const pin = (where: string) => update($, card, (c) => ({ ...c, [at]: c[at] === where ? '' : where }))
    const marked = (md: string) => markTerms(ensureMarks(md, terms), (t) => (termFor(termId(t)) ? `{{${t}}}` : termText(t)))

    // The layer the settings lead with is shown, the other folded until pressed, or while
    // "tech" / "story" is on. With no story, the technical part leads.
    const techFirst = !!tech && (st.lead === 'technical' || st.lead === 'technical-only' || !story)
    const [lead, rest] = techFirst ? [tech, story] : [story, tech]
    const restOpen = !!rest && ((await read($, foldAll)) || (await read($, foldOpen))[at] === true)
    const otherOpen = hasHint && ((await read($, showAll)) || (await read($, open))[at] === true)

    // About how many rows the reply takes, to open each card where it fits. When it fits
    // nowhere, rows are added under the reply so the card below is not cut off.
    const rowsOf = (md: string) => unmark(md).split('\n').reduce((n, l) => n + Math.max(1, Math.ceil(l.length / Math.max(10, cols - 2))), 0)
    const leadRows = rowsOf(lead)
    const total = leadRows + (rest ? 2 + (restOpen ? rowsOf(rest) : 0) : 0) + (hasHint ? 2 : 0)
    let room = 0
    const cardWidth = (t: Term) => Math.min(width, t.term.length + t.meaning.length + 6)
    const cardRows = (t: Term) => Math.ceil((t.term.length + t.meaning.length + 2) / Math.max(1, cardWidth(t) - 2))
    const above = (t: Term, row: number) => {
      if (row >= cardRows(t)) return true
      room = Math.max(room, cardRows(t) - (total - row - 1))
      return false
    }

    // A term's card, drawn over the reply on a solid background; nothing below it moves.
    // A key makes a Box a hover scope, so the hidden hover card gets none.
    const cardOf = (t: Term, key: string | undefined, top: number, left: number, extra: Record<string, unknown> = {}) => (
      <Box key={key} position="absolute" top={top} left={left} width={cardWidth(t)} backgroundColor="suggestion" paddingX={1} {...extra}>
        <Text color="inverseText" wrap="wrap"><Text bold>{t.term}</Text>: {t.meaning}</Text>
      </Box>
    )

    // One line drawn word by word so it wraps, its markdown styles kept; each term carries
    // its hover card. `row` is about how many rows of the reply sit above this line.
    const termLine = (name: string, line: string, n: number, row: number) => {
      const head = line.match(/^(\s*)(?:([-*+])|(\d+[.)])|(>))\s+/)
      const body = head ? line.slice(head[0].length) : line.trimStart()
      const indent = head ? head[1] : (line.match(/^\s*/) || [''])[0]
      let col = head ? head[0].length : indent.length
      const span = Math.max(20, cols - 4)
      const cells: unknown[] = []
      const mark = head ? (head[2] ? '• ' : head[3] ? `${head[3]} ` : '│ ') : ''
      if (head || indent) cells.push(<Text key={`shoga-l-${n}`} dimColor={!!head?.[4]}>{indent}{mark}</Text>)
      inlineSegments(body).forEach((seg, i) => {
        const look = { bold: !!seg.bold, italic: !!seg.italic, strikethrough: !!seg.strike }
        const t = seg.kind === 'term' ? termFor(seg.id) : undefined
        if (t) {
          const left = -Math.max(0, (col % span) + cardWidth(t) - (cols - 2))
          const top = above(t, row + Math.floor(col / span)) ? -cardRows(t) : 1
          cells.push(
            <Box key={`shoga-t-${at}-${name}-${n}-${i}`}>
              <Text underline {...look} color={seg.code ? 'permission' : 'suggestion'} hover={{ inverse: true }}>{seg.text}</Text>
              {cardOf(t, undefined, top, left, { display: 'none', hover: { display: 'flex' } })}
            </Box>,
          )
        } else {
          for (const [j, word] of (seg.text.match(/\S+\s*|\s+/g) || []).entries()) {
            const k = `shoga-w-${n}-${i}-${j}`
            cells.push(seg.href
              ? <Text key={k} {...look}><Link href={seg.href}>{word}</Link></Text>
              : <Text key={k} {...look} color={seg.code ? 'permission' : undefined}>{word}</Text>)
          }
        }
        col += seg.text.length
      })
      return <Box key={`shoga-row-${at}-${name}-${n}`} flexDirection="row" flexWrap="wrap">{cells}</Box>
    }

    // The story or the technical part. Blocks without terms stay markdown.
    const part = (name: 'story' | 'tech', md: string, base = 0) => {
      const drawn = terms.length ? marked(md) : md
      if (!hasMark(drawn)) return <Markdown key={`shoga-${name}-${at}`} text={unmark(drawn)} />
      if (hover) {
        // Paragraphs and lists split at blank lines (outside code fences). A term-free one
        // stays markdown, joined with its term-free neighbours so markdown spaces them; one
        // with terms is drawn line by line, with a blank row around it as in the source.
        const chunks: string[][] = [[]]
        let fence = false
        for (const line of drawn.split('\n')) {
          if (/^\s*```/.test(line)) fence = !fence
          if (!fence && !line.trim()) { if (chunks[chunks.length - 1].length) chunks.push([]) } else chunks[chunks.length - 1].push(line)
        }
        // Table rows, headings and code fences keep their markdown, without the highlight.
        const termy = (line: string) => hasMark(line) && !/^\s*(\||#|```)/.test(line)
        const items: { terms: boolean; lines: string[] }[] = []
        for (const chunk of chunks.filter((c) => c.length)) {
          const has = chunk.some(termy)
          const last = items[items.length - 1]
          if (!has && last && !last.terms) last.lines.push('', ...chunk)
          else items.push({ terms: has, lines: chunk })
        }
        const blocks: unknown[] = []
        let row = base
        items.forEach((item, k) => {
          if (k > 0) { blocks.push(<Text key={`shoga-gap-${at}-${name}-${k}`}> </Text>); row += 1 }
          if (!item.terms) {
            const block = item.lines.join('\n')
            blocks.push(<Markdown key={`shoga-${name}-${at}-${k}`} text={unmark(block)} />)
            row += rowsOf(block)
            return
          }
          // In a chunk with terms, markdown keeps tables and fences; every other line is
          // drawn as a row, so a nested list keeps its indent instead of turning into code.
          let keepMd: string[] = []
          let inFence = false
          const flushMd = (n: number) => {
            if (keepMd.length) blocks.push(<Markdown key={`shoga-${name}-${at}-${k}-${n}`} text={unmark(keepMd.join('\n'))} />)
            keepMd = []
          }
          item.lines.forEach((line, n) => {
            const fenceLine = /^\s*```/.test(line)
            if (fenceLine) inFence = !inFence
            if (fenceLine || inFence || /^\s*(\||#)/.test(line)) keepMd.push(line)
            else { flushMd(n); blocks.push(termLine(name, line, k * 1000 + n, row)) }
            row += rowsOf(line)
          })
          flushMd(item.lines.length)
        })
        return <Box flexDirection="column">{blocks}</Box>
      }
      const linked = markTerms(drawn, (t) => { const term = termFor(termId(t)); return term ? `[${termText(t)}](${TERM_URL}${term.id})` : termText(t) })
      const shown = pinned.startsWith(`${name}:`) ? byId.get(pinned.slice(name.length + 1)) : undefined
      const idx = shown ? linked.indexOf(`](${TERM_URL}${shown.id})`) : -1
      // The row is counted on the text as shown, not on the long link markdown.
      const shownRow = idx >= 0 ? Math.max(0, rowsOf(linked.slice(0, idx).replace(/\]\(https:\/\/shoga\.invalid\/term\/[^)]*\)/g, '').replace(/\[/g, '')) - 1) : 0
      return (
        <Box flexDirection="column">
          <Markdown
            key={`shoga-${name}-${at}`}
            text={linked}
            pressableLinks={terms.map((t) => TERM_URL + t.id)}
            onLinkPress={(link) => {
              const tid = link.href.slice(TERM_URL.length)
              if (byId.has(tid)) void pin(`${name}:${tid}`)
            }}
          />
          {shown && idx >= 0 ? cardOf(shown, `shoga-card-${at}`, above(shown, base + shownRow) ? shownRow - cardRows(shown) : shownRow + 1, 2) : null}
        </Box>
      )
    }

    const leadPart = part(techFirst ? 'tech' : 'story', lead)
    let fold = null
    if (rest) {
      const restPart = restOpen ? part(techFirst ? 'story' : 'tech', rest, leadRows + 2) : null
      fold = (
        <Box flexDirection="column" marginTop={1}>
          <Button
            key={`shoga-fold-${at}`}
            plain
            dimColor
            label={`${restOpen ? '▾' : '▸'} ${techFirst ? 'Story' : 'Technical'}`}
            onPress={() => update($, foldOpen, (o) => ({ ...o, [at]: !o[at] }))}
          />
          {restPart}
        </Box>
      )
    }

    // Other language: folded until pressed, or while "en"/"tr" is on.
    let other = null
    if (hasHint) {
      const plain = unmark(lead)
      const done = translations.get(id)
      if (otherOpen && done === undefined) translate($, id, plain, st)
      other = (
        <Box flexDirection="column" marginTop={1}>
          <Button
            key={`shoga-toggle-${at}`}
            plain
            dimColor
            label={`${otherOpen ? '▾' : '▸'} ${st.otherLabel}`}
            onPress={async () => {
              const now = await update($, open, (o) => ({ ...o, [at]: !o[at] }))
              if (now[at]) translate($, id, plain, st)
            }}
          />
          {otherOpen ? (
            done === undefined
              ? <Text dimColor>  {PENDING}</Text>
              : <Markdown key={`shoga-other-${at}`} text={done} />
          ) : null}
        </Box>
      )
    }

    return (
      <Box flexDirection="column">
        {leadPart}
        {fold}
        {other}
        {Array.from({ length: room }, (_, i) => <Text key={`shoga-room-${at}-${i}`}> </Text>)}
      </Box>
    )
  })
}
