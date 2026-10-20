// Hard cases for the display mod, from an adversarial test pass: markdown inside term lines,
// links and URLs, overlapping terms, card placement, spacing and layer markers.
import { test, expect } from 'claude-code/testing'
import { URDU, ENGLISH, world, outline, mount, draw } from './edge-lib'

const T = (story: string, terms: string[]) => `${story}\n\n▸ Terms\n${terms.map((t) => `- ${t}: meaning of ${t}`).join('\n')}`
const rowsOf = (o: string) => [...o.matchAll(/ R\[(.*?)\] /gs)].map((m) => m[1].replace(/\{top:[^}]*\}/g, ''))
const termsIn = (o: string) => [...o.matchAll(/T«([^»|]*)/g)].map((m) => m[1])
async function cards($: any, surface: string, text: string, cols = 80) {
  const ui = await mount($, surface, text, cols)
  const all = await ui.findAll({})
  const out = all.filter((e: any) => e.props?.position === 'absolute').map((e: any) => ({ ...e.props, text: e.text }))
  await ui.unmount()
  return out
}

for (const [name, story, leak] of [
  ['italic *x*', 'Use *batching* now.', /\*/],
  ['italic _x_', 'Use _batching_ now.', /(^|\s)_|_(\s|$)/],
  ['bold italic', 'Use ***batching*** now.', /\*/],
  ['link on same line', 'The batching is in [docs](https://x.io) and *very* fast.', /\]\(|\*/],
  ['blockquote', '> The batching is slow.', /^>/],
  ['strikethrough', '~~batching~~ gone.', /~~/],
  ['html tag', 'Use <b>batching</b> here.', /<b>/],
  ['escaped star', 'Use \\*batching\\* here.', /\\/],
] as const) {
  test(`terminal: no raw markdown leaks into a term line (${name})`, async ($, on) => {
    world(on, ENGLISH)
    const o = await draw($, 'terminal', T(story, ['batching']))
    expect(termsIn(o)).toEqual(['batching'])
    for (const r of rowsOf(o)) expect(r).not.toMatch(leak)
  })
}

test('a term is not marked inside a link URL: the link keeps its target on both surfaces', async ($, on) => {
  world(on, ENGLISH)
  const text = T('See [docs](https://cache.io/x) for the cache.', ['cache'])
  expect(await draw($, 'desktop', text)).toMatch(/\[docs\]\(https:\/\/cache\.io\/x\)/)
  const ui = await mount($, 'terminal', text)
  const link = (await ui.findAll({})).find((e: any) => e.type === 'Link')
  const term = await ui.find({ type: 'Text', text: /^cache$/ })
  await ui.unmount()
  expect(link?.props?.href).toBe('https://cache.io/x')
  expect(term).toBeDefined()
})

test('a term inside link text is left alone (no nested link), and no link syntax shows', async ($, on) => {
  world(on, ENGLISH)
  for (const surface of ['terminal', 'desktop']) {
    const o = await draw($, surface, T('See [the batching docs](https://x.io/a) now.', ['batching']))
    expect(termsIn(o)).toEqual([])
    expect(o).not.toMatch(/shoga\.invalid/)
  }
})

test('a term is not marked inside a bare URL (both surfaces)', async ($, on) => {
  world(on, ENGLISH)
  for (const surface of ['terminal', 'desktop']) {
    const o = await draw($, surface, T('Open https://example.com/cache?x=1 then the cache.', ['cache']))
    expect(o).toMatch(/https:\/\/example\.com\/cache\?x=1/)
  }
})

test('desktop: a term inside link text does not make a nested link', async ($, on) => {
  world(on, ENGLISH)
  const o = await draw($, 'desktop', T('See [the cache docs](https://x.io/a) now.', ['cache']))
  expect(o).not.toMatch(/\[[^\]]*\[cache\]\(https:\/\/shoga/)
})

test('overlapping terms: both are underlined whatever the list order', async ($, on) => {
  world(on, ENGLISH)
  for (const order of [['key', 'idempotency key'], ['idempotency key', 'key']]) {
    const o = await draw($, 'terminal', T('Use an idempotency key, the key matters.', order))
    expect(termsIn(o).sort()).toEqual(['idempotency key', 'key'])
  }
})

test('regex-special, accented and native-script terms are underlined', async ($, on) => {
  world(on, ENGLISH)
  const o = await draw($, 'terminal', T('The N+1 query in C++ and .NET, Café, ریلیز and रिलीज़.', ['N+1', 'C++', '.NET', 'Café', 'ریلیز', 'रिलीज़']))
  expect(termsIn(o)).toEqual(['N+1', 'C++', '.NET', 'Café', 'ریلیز', 'रिलीज़'])
})

test('desktop: a Devanagari term gets a link id that keeps its letters', async ($, on) => {
  world(on, ENGLISH)
  const o = await draw($, 'desktop', T('Yeh रिलीज़ hai.', ['रिलीज़']))
  expect(o).not.toMatch(/term\/र-ल-ज/)
})

test('case and a plural "s" are free: both are underlined', async ($, on) => {
  world(on, ENGLISH)
  expect(termsIn(await draw($, 'terminal', T('The Webhook fired.', ['webhook'])))).toEqual(['Webhook'])
  expect(termsIn(await draw($, 'terminal', T('Two migrations ran.', ['migration'])))).toEqual(['migrations'])
})

test('term in bold, numbered list, nested list, start/end of line, punctuation', async ($, on) => {
  world(on, ENGLISH)
  expect(await draw($, 'terminal', T('**The cache is cold** now.', ['cache']))).toMatch(/T«cache\|b»/)
  expect(await draw($, 'terminal', T('1. The cache is cold.\n2. Second.', ['cache']))).toMatch(/R\[1\. The T«cache»/)
  expect(termsIn(await draw($, 'terminal', T('cache: hot, (webhook)!', ['cache', 'webhook'])))).toEqual(['cache', 'webhook'])
})

test('a nested list keeps its deeper items as a list, not an indented code block', async ($, on) => {
  world(on, ENGLISH)
  const o = await draw($, 'terminal', T('- Top\n  - The cache is cold.\n    - deeper item', ['cache']))
  expect(o).not.toMatch(/M«    - deeper/)
})

test('tables and headings keep their markdown on the terminal', async ($, on) => {
  world(on, ENGLISH)
  expect(await draw($, 'terminal', T('| a | b |\n|---|---|\n| cache | x |', ['cache']))).toMatch(/M«\| a \| b \|/)
  expect(await draw($, 'terminal', T('### The cache\nText.', ['cache']))).toMatch(/M«### The cache/)
})

test('code: a term only in code is not underlined; inline code that is exactly the term keeps its code look', async ($, on) => {
  world(on, ENGLISH)
  expect(termsIn(await draw($, 'terminal', T('Run `cache:clear` now.', ['cache'])))).toEqual([])
  const ui = await mount($, 'terminal', T('Run `cache` now.', ['cache']))
  const t = await ui.find({ type: 'Text', text: /^cache$/ })
  await ui.unmount()
  expect(t?.props?.color).toBe('permission')
})

test('CRLF replies: no carriage return reaches a drawn Text', async ($, on) => {
  world(on, ENGLISH)
  const ui = await mount($, 'terminal', 'The cache is cold.\r\n\r\nSecond para.\r\n\r\n▸ Terms\r\n- cache: store\r\n')
  const texts = (await ui.findAll({ type: 'Text' })).map((e: any) => e.text)
  await ui.unmount()
  expect(texts.join('|')).not.toMatch(/\r/)
})

test('more than six listed terms: at most six underlined; the same term in story and technical part is underlined in both', async ($, on) => {
  world(on, ENGLISH)
  expect(termsIn(await draw($, 'terminal', T('a1 a2 a3 a4 a5 a6 a7 words.', ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7']))).length).toBe(6)
  await $.prompt.submit({ text: 'tech' } as any)
  expect(termsIn(await draw($, 'terminal', 'The cache is cold.\n\n▸ Technical\nThe cache TTL is 5s.\n\n▸ Terms\n- cache: store'))).toEqual(['cache', 'cache'])
})

test('known terms are not underlined; termHints off underlines nothing and shows no braces', async ($, on) => {
  world(on, { ...ENGLISH, knownTerms: ['idempotency key', 'n+1'] })
  const o = await draw($, 'terminal', T('Use an idempotency key and the cache.', ['idempotency key', 'cache']))
  expect(termsIn(o)).toEqual(['cache'])
  expect(await draw($, 'terminal', 'The N+1 query is slow and the code is bad today.')).toBe('engine-default')
})

test('termHints off: no underline, no links, no braces, on every surface', async ($, on) => {
  world(on, { ...URDU, termHints: false })
  for (const surface of ['terminal', 'desktop', 'vscode']) {
    const o = await draw($, surface, 'Uses {{cache}} now.\n\n▸ Technical\nTech {{batching}}.\n\n▸ Terms\n- cache: x\n\n▸ English: "en" likhein')
    expect(o).not.toMatch(/T«|shoga\.invalid|\{\{|▸ Terms/)
  }
})

test('termHints off with no hint and no technical part: old {{marks}} are still removed', async ($, on) => {
  world(on, { ...ENGLISH, termHints: false })
  expect(await draw($, 'desktop', 'Uses {{cache}} now.')).not.toMatch(/\{\{/)
})

// ---------- hover card placement ----------

// Blank rows the reply adds at its end to make room for a card.
async function roomRows($: any, surface: string, text: string, cols = 80) {
  const ui = await mount($, surface, text, cols)
  const n = (await ui.findAll({ type: 'Text', text: /^ $/ })).length
  await ui.unmount()
  return n
}

test('one-line reply (no hint, no fold): the card opens below and the reply makes room for it', async ($, on) => {
  world(on, ENGLISH)
  const text = T('Uses the cache.', ['cache'])
  const [c] = await cards($, 'terminal', text)
  expect(c.top).toBe(1)
  const rows = Math.ceil(('cache'.length + 'meaning of cache'.length + 2) / (c.width - 2))
  expect(await roomRows($, 'terminal', text)).toBeGreaterThanOrEqual(rows)
})

test('one-line reply with the language line: a long card gets the rows it needs below', async ($, on) => {
  world(on, URDU)
  const long = 'x'.repeat(150)
  const text = `Cache use hota hai.\n\n▸ Terms\n- Cache: ${long}\n\n▸ English: "en" likhein`
  const [c] = await cards($, 'terminal', text)
  const rows = Math.ceil((5 + 150 + 2) / (c.width - 2))
  // Rows below the term: the language line's margin and button (2), plus the room added.
  expect(c.top).toBe(1)
  expect(2 + (await roomRows($, 'terminal', text))).toBeGreaterThanOrEqual(rows)
})

test('first line: the card opens below; last line: above', async ($, on) => {
  world(on, ENGLISH)
  const body = 'The cache is first.\n\nLine two.\n\nLine three.\n\nAnd the webhook last.'
  const cs = await cards($, 'terminal', T(body, ['cache', 'webhook']))
  expect(cs[0].top).toBe(1)
  expect(cs[1].top).toBeLessThan(0)
})

for (const cols of [40, 80, 200]) {
  test(`right edge at ${cols} columns: the card stays inside the viewport`, async ($, on) => {
    world(on, ENGLISH)
    const pad = 'w'.repeat(Math.max(1, cols - 12))
    const cs = await cards($, 'terminal', T(`${pad} cache`, ['cache']), cols)
    const at = (pad.length + 1) % Math.max(20, cols - 4)
    expect(at + cs[0].left + cs[0].width).toBeLessThanOrEqual(cols - 2)
    expect(cs[0].width).toBeLessThanOrEqual(cols - 4)
  })
}

test('20 columns: the card is not wider than the viewport', async ($, on) => {
  world(on, ENGLISH)
  const [c] = await cards($, 'terminal', T('The cache.', ['cache']), 20)
  expect(c.width).toBeLessThanOrEqual(18)
})

test('word wrap at 40 columns: a term pushed to the next row by a long word gets its card on the right row', async ($, on) => {
  world(on, ENGLISH)
  // 30 chars then a 12-char word that wraps; the term follows on the second visual row.
  const [c] = await cards($, 'terminal', T(`${'a'.repeat(30)} ${'b'.repeat(12)} cache`, ['cache']), 40)
  // Estimated col = 44 → row 1 by character count; with word wrap it is also row 1, so the card opens above.
  expect(c.top).toBeLessThan(0)
})

test('desktop: the clicked card of a term on the last line is not placed below the reply', async ($, on) => {
  world(on, ENGLISH)
  const text = T('Line one.\n\nLine two.\n\nThe last line has the cache.', ['cache'])
  const ui = await mount($, 'desktop', text)
  const md = await ui.find({ type: 'Markdown', text: /shoga\.invalid/ })
  await ui.press({ key: md!.key!, link: { href: 'https://shoga.invalid/term/cache' } })
  const all = await ui.findAll({})
  const card = all.find((e: any) => e.props?.position === 'absolute')
  await ui.unmount()
  expect(card).toBeDefined()
  // Five source lines → the term sits on row 4 (0-based); a card at top 5 is under the last row.
  expect(card.props.top).toBeLessThanOrEqual(4)
})

test('desktop: the card row is estimated from the shown text, not the long link markdown', async ($, on) => {
  world(on, ENGLISH)
  const text = T('a1 a2 a3 a4 a5 and the cache.', ['a1', 'a2', 'a3', 'a4', 'a5', 'cache'])
  const ui = await mount($, 'desktop', text, 80)
  const md = await ui.find({ type: 'Markdown', text: /shoga\.invalid/ })
  await ui.press({ key: md!.key!, link: { href: 'https://shoga.invalid/term/cache' } })
  const card = (await ui.findAll({})).find((e: any) => e.props?.position === 'absolute')
  await ui.unmount()
  // One shown row of 30 characters: the card belongs at row 1.
  expect(card.props.top).toBe(1)
})

// ---------- spacing ----------

test('spacing: no double gaps, no markdown block with blank edges, no gap inside a list', async ($, on) => {
  world(on, ENGLISH)
  const o = await draw($, 'terminal', T('Intro para.\n\n\n\n- a\n- b has cache\n- c\n\n```\ncode\n```\n\n| t | u |\n|---|---|\n| 1 | 2 |\n\nEnd with webhook.', ['cache', 'webhook']))
  expect(o).not.toMatch(/ _ \s* _ /)
  expect(o).not.toMatch(/M«\n|\n»/)
  // A list with a term is drawn row by row, with no gap inside it.
  expect(o).toMatch(/R\[• a\]\s*R\[• b has T«cache»[^\]]*\]\s*R\[• c\]/)
})

test('spacing: a paragraph, then a fence with no blank line between, keeps no gap', async ($, on) => {
  world(on, ENGLISH)
  const o = await draw($, 'terminal', T('The cache is cold.\n```\ncode\n```', ['cache']))
  expect(o).not.toMatch(/ _ /)
})

// ---------- layers ----------

for (const [name, line] of [['colon', '▸ Technical:'], ['bold', '**▸ Technical**'], ['heading', '## ▸ Technical'], ['trailing text', '▸ Technical: details']] as const) {
  test(`layers: a "${line}" line folds the technical part (${name})`, async ($, on) => {
    world(on, URDU)
    const o = await draw($, 'terminal', `Story line.\n\n${line}\nTECH DETAIL\n\n▸ English: "en" likhein`)
    expect(o).toMatch(/B«▸ Technical»/)
    expect(o).not.toMatch(/TECH DETAIL/)
  })
}

test('layers: ▸ Technical inside a code fence is code, not a fold', async ($, on) => {
  world(on, URDU)
  const o = await draw($, 'terminal', 'Look:\n```\n▸ Technical\n```\nend of story.')
  expect(o).not.toMatch(/B«▸ Technical»/)
})

test('layers: ▸ Technical at the very end (empty technical part) draws no fold', async ($, on) => {
  world(on, URDU)
  const o = await draw($, 'terminal', 'Story line.\n\n▸ Technical\n\n▸ English: "en" likhein')
  expect(o).not.toMatch(/B«▸ Technical»/)
})

test('layers: ▸ Technical at the very top (no story) shows the technical part, no empty story', async ($, on) => {
  world(on, URDU)
  const o = await draw($, 'terminal', '▸ Technical\nTECH ONLY\n\n▸ English: "en" likhein')
  expect(o).toMatch(/TECH ONLY/)
})

test('layers: ▸ Terms without a technical part and without a language line', async ($, on) => {
  world(on, URDU)
  const o = await draw($, 'terminal', 'Story uses batching.\n\n▸ Terms\n- batching: together')
  expect(termsIn(o)).toEqual(['batching'])
  expect(o).not.toMatch(/▸ Terms|B«/)
})

test('layers: lead technical-only and a reply that still has a story: the technical part leads', async ($, on) => {
  world(on, { ...URDU, lead: 'technical-only' })
  const o = await draw($, 'terminal', 'STORY LINE\n\n▸ Technical\nTECH LINE\n\n▸ English: "en" likhein')
  expect(o).toMatch(/^[^B]*TECH LINE/)
})

test('layers: lead technical folds the story; "tech" goes to Claude, "story" toggles', async ($, on) => {
  world(on, { ...URDU, lead: 'technical' })
  const r1: any = await $.prompt.submit({ text: 'tech' } as any)
  expect(r1?.drop).toBeUndefined(); expect(r1?.text).toBe('tech')
  const r2: any = await $.prompt.submit({ text: 'STORY' } as any)
  expect(r2?.drop).toMatch(/Story shown/)
})

test('en / tr for an English user: not swallowed by the mod', async ($, on) => {
  world(on, ENGLISH)
  for (const t of ['en', 'tr']) { const r: any = await $.prompt.submit({ text: t } as any); expect(r?.drop).toBeUndefined() }
})

test('two identical replies keep their own fold state', async ($, on) => {
  world(on, URDU)
  const text = 'Same story.\n\n▸ Technical\nTECH\n\n▸ English: "en" likhein'
  const a = await mount($, 'terminal', text)
  const b = await mount($, 'terminal', text)
  const btn = await a.find({ type: 'Button', text: /Technical/ })
  await a.press({ key: btn!.key! })
  const bAll = outline((await b.findAll({}))[0])
  await a.unmount(); await b.unmount()
  expect(bAll).not.toMatch(/TECH/)
})

test('web mode: "tech", "story", "en" and "tr" go on to Claude instead of toggling a fold nobody sees', async ($, on) => {
  world(on, { ...URDU, web: true })
  for (const t of ['tech', 'story', 'en', 'tr']) {
    const r: any = await $.prompt.submit({ text: t } as any)
    expect(r?.drop).toBeUndefined()
    expect(r?.text).toBe(t)
  }
})
