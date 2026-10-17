import { test, expect, mock } from 'claude-code/testing'

const URDU = {
  language: 'urdu', script: 'roman', langKey: 'urdu:roman', mineKey: 'urdu:roman',
  bilingual: true, cliEnglish: false, openLabel: 'Roman-Urdu', otherLabel: 'English', otherKey: 'en',
  otherRtl: false, otherGuide: 'Plain English.', roles: ['qa'], primaryRole: 'QA / Tester',
  explainCommands: true, termHints: true, lead: 'story', knownTerms: [], enabled: true,
}
const ENGLISH_PO = { ...URDU, language: 'english', langKey: 'english', bilingual: false, openLabel: 'English', primaryRole: 'Product Owner' }

const REPLY = `Release mat karein. Do problems hain.

▸ English: "en" likhein`

const row = (text: string) => ({ component: 'AssistantMessage', props: { text, isFirstOfReply: true } }) as const
const SURFACES = ['terminal', 'desktop', 'vscode'] as const

function world(on: any, state: object, opts: { notice?: boolean } = {}) {
  mock.env(on, { SHOGA_STATE_JSON: JSON.stringify(state) })
  mock.store(on)
  mock.clock(on)
  on('ui.status', () => ({ value: undefined }))
  if (opts.notice !== false) on('ui.notice', () => ({ value: undefined }))
  on('ui.render', async ($: any, e: any) => { const { Text } = $.ui.resolve(e); return <Text>engine-default</Text> })
}

test('the other language is folded, a press translates and unfolds it, on every surface', async ($, on) => {
  world(on, URDU)
  let calls = 0
  on('model.complete', async () => { calls++; return { value: { isAnswered: true, text: 'Do not release. There are two problems.', usage: {} } } })
  for (const surface of SURFACES) {
    const ui = await $.ui.mount({ plugin: 'shoga-speaks', surface, ...row(REPLY) })
    expect(await ui.find({ type: 'Markdown', text: /Release mat karein/ })).toBeDefined()
    expect(await ui.find({ type: 'Markdown', text: /likhein/ })).toBeUndefined()
    expect(await ui.find({ type: 'Markdown', text: /Do not release/ })).toBeUndefined()
    const btn = await ui.find({ type: 'Button', text: /English/ })
    expect(btn).toBeDefined()
    await ui.press({ key: btn!.key! })
    await ui.redraw()
    expect(await ui.find({ type: 'Markdown', text: /Do not release/ })).toBeDefined()
    await ui.press({ key: btn!.key! })
    expect(await ui.find({ type: 'Markdown', text: /Do not release/ })).toBeUndefined()
    await ui.unmount()
  }
  expect(calls).toBe(1)
})

test('typing "en" unfolds every reply with no turn sent to Claude', async ($, on) => {
  world(on, URDU)
  on('model.complete', async () => ({ value: { isAnswered: true, text: 'Do not release.', usage: {} } }))
  const r: any = await $.prompt.submit({ text: 'en' } as any)
  expect(r.drop).toMatch(/English shown/)
  const ui = await $.ui.mount({ plugin: 'shoga-speaks', surface: 'terminal', ...row(REPLY) })
  await ui.redraw()
  expect(await ui.find({ type: 'Markdown', text: /Do not release/ })).toBeDefined()
  await ui.unmount()
})

test('a failed translation says so and points to the fallback', async ($, on) => {
  world(on, URDU)
  on('model.complete', async () => ({ value: { isAnswered: false, reason: 'aborted', usage: {} } }))
  const ui = await $.ui.mount({ plugin: 'shoga-speaks', surface: 'terminal', ...row(REPLY) })
  const btn = await ui.find({ type: 'Button', text: /English/ })
  await ui.press({ key: btn!.key! })
  await ui.redraw()
  expect(await ui.find({ type: 'Markdown', text: /Type "en" to ask Claude/ })).toBeDefined()
  await ui.unmount()
})

test('technical terms get a footer; a press shows the simple meaning', async ($, on) => {
  world(on, ENGLISH_PO)
  const ui = await $.ui.mount({ plugin: 'shoga-speaks', surface: 'terminal', ...row('The page is slow because of an N+1 query in the order list. A migration is not needed.') })
  const term = await ui.find({ type: 'Button', text: /N\+1 query/ })
  expect(term).toBeDefined()
  expect(await ui.find({ type: 'Button', text: /^migration$/ })).toBeDefined()
  await ui.press({ key: term!.key! })
  expect(await ui.find({ type: 'Text', text: /asks the database once per item/ })).toBeDefined()
  await ui.unmount()
})

test('known terms and plain replies are drawn as usual', async ($, on) => {
  world(on, { ...ENGLISH_PO, knownTerms: ['n+1', 'migration'] })
  const ui = await $.ui.mount({ plugin: 'shoga-speaks', surface: 'terminal', ...row('Fixed the N+1 query. No migration.') })
  expect(await ui.find({ type: 'Text', text: 'engine-default' })).toBeDefined()
  await ui.unmount()
})

test('a risky shell command gets a plain line under its row, in the user language', async ($, on) => {
  world(on, URDU)
  const ui = await $.ui.mount({
    plugin: 'shoga-speaks', surface: 'terminal', component: 'ToolUse',
    props: { tool_use_id: 't1', tool: 'Bash', input: { command: 'git push --force origin main' }, isRunning: false, isErrored: false, isInterrupted: false },
  })
  expect(await ui.find({ type: 'Text', text: 'engine-default' })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /overwrite karega/ })).toBeDefined()
  await ui.unmount()
})

test('everything passes through when Shoga-Speaks is off', async ($, on) => {
  world(on, { ...URDU, enabled: false })
  const ui = await $.ui.mount({ plugin: 'shoga-speaks', surface: 'terminal', ...row(REPLY) })
  expect(await ui.find({ type: 'Text', text: 'engine-default' })).toBeDefined()
  await ui.unmount()
})

test('glossary meanings are translated once by a small model and cached', async ($, on) => {
  world(on, URDU)
  let calls = 0
  on('model.complete', async () => { calls++; return { value: { isAnswered: true, text: 'n+1: Code har item ke liye database se alag poochta hai, is liye slow ho jata hai.', usage: {} } } })
  const text = 'Page slow hai kyunke yahan N+1 query hai. Fix chhota hai aur test aasan hai.'
  let ui = await $.ui.mount({ plugin: 'shoga-speaks', surface: 'terminal', ...row(text) })
  const term = await ui.find({ type: 'Button', text: /N\+1 query/ })
  await ui.press({ key: term!.key! })
  await ui.redraw()
  expect(await ui.find({ type: 'Text', text: /har item ke liye/ })).toBeDefined()
  await ui.unmount()
  ui = await $.ui.mount({ plugin: 'shoga-speaks', surface: 'desktop', ...row(text) })
  expect(calls).toBe(1)
  await ui.unmount()
})

test('a risky shell command gets a plain line under the approval dialog', async ($, on) => {
  world(on, URDU, { notice: false })
  const notices: string[] = []
  on('ui.notice', (_$: any, e: any) => { notices.push(JSON.stringify(e)); return { value: undefined } })
  on('tool.call', async () => ({ result: { stdout: '', stderr: '', interrupted: false } }) as any)
  await $.tool.call({ tool: 'Bash', command: 'rm -rf build' } as any)
  expect(notices.join(' ')).toMatch(/hamesha ke liye delete/)
})

const LAYERED = `Orders page slow tha kyunke har order ke liye alag query chalti thi. Ab {{batching}} se sab ek saath aata hai, page 6x tez hai.

▸ Technical
\`OrderList.load()\` (\`src/orders/list.ts:42\`) ab customers ko ek {{batching}} query mein laata hai. \`{{not-a-mark}}\` code hai.

▸ Terms
- batching: bahut saare kaam ek hi baar mein karna

▸ English: "en" likhein`

test('the technical part is folded; a press unfolds it; marks never show as braces', async ($, on) => {
  world(on, URDU)
  const ui = await $.ui.mount({ plugin: 'shoga-speaks', surface: 'terminal', ...row(LAYERED) })
  expect(await ui.find({ type: 'Markdown', text: /Orders page slow tha.*Ab batching se/s })).toBeDefined()
  expect(await ui.find({ type: 'Markdown', text: /\{\{batching/ })).toBeUndefined()
  expect(await ui.find({ type: 'Markdown', text: /OrderList\.load/ })).toBeUndefined()
  expect(await ui.find({ type: 'Markdown', text: /▸ Terms|ek hi baar mein/ })).toBeUndefined()
  const btn = await ui.find({ type: 'Button', text: /Technical/ })
  await ui.press({ key: btn!.key! })
  expect(await ui.find({ type: 'Markdown', text: /ek batching query.*`\{\{not-a-mark\}\}`/s })).toBeDefined()
  await ui.unmount()
})

test('typing "tech" unfolds every technical part with no turn sent to Claude', async ($, on) => {
  world(on, URDU)
  const r: any = await $.prompt.submit({ text: 'tech' } as any)
  expect(r.drop).toMatch(/Technical part shown/)
  const ui = await $.ui.mount({ plugin: 'shoga-speaks', surface: 'terminal', ...row(LAYERED) })
  expect(await ui.find({ type: 'Markdown', text: /OrderList\.load/ })).toBeDefined()
  await ui.unmount()
})

test('fullscreen: a marked term is a link; a click opens its card over the reply, a second click closes it', async ($, on) => {
  world(on, URDU)
  const ui = await $.ui.mount({ plugin: 'shoga-speaks', surface: 'terminal', viewport: { columns: 100, rows: 40, isFullscreen: true }, ...row(LAYERED) })
  const story = await ui.find({ type: 'Markdown', text: /\[batching\]\(https:\/\/shoga\.invalid\/term\/batching\)/ })
  expect(story).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /ek hi baar mein/ })).toBeUndefined()
  await ui.press({ key: story!.key!, link: { href: 'https://shoga.invalid/term/batching' } })
  expect(await ui.find({ type: 'Text', text: /batching: bahut saare kaam/ })).toBeDefined()
  await ui.press({ key: story!.key!, link: { href: 'https://shoga.invalid/term/batching' } })
  expect(await ui.find({ type: 'Text', text: /ek hi baar mein/ })).toBeUndefined()
  await ui.unmount()
})

test('main screen: marked terms become chips; a press pins the card, its ✕ closes it', async ($, on) => {
  world(on, URDU)
  const ui = await $.ui.mount({ plugin: 'shoga-speaks', surface: 'terminal', viewport: { columns: 100, rows: 40, isFullscreen: false }, ...row(LAYERED) })
  expect(await ui.find({ type: 'Markdown', text: /shoga\.invalid/ })).toBeUndefined()
  const chip = await ui.find({ type: 'Button', text: /^batching$/ })
  expect(chip).toBeDefined()
  await ui.press({ key: chip!.key! })
  const close = await ui.find({ type: 'Button', text: '✕' })
  expect(close).toBeDefined()
  await ui.press({ key: close!.key! })
  expect(await ui.find({ type: 'Button', text: '✕' })).toBeUndefined()
  await ui.unmount()
})

test('term hints off: no chips or links, marks still removed', async ($, on) => {
  world(on, { ...URDU, termHints: false })
  const ui = await $.ui.mount({ plugin: 'shoga-speaks', surface: 'desktop', ...row(LAYERED) })
  expect(await ui.find({ type: 'Button', text: /^batching$/ })).toBeUndefined()
  expect(await ui.find({ type: 'Markdown', text: /shoga\.invalid|\{\{batching/ })).toBeUndefined()
  await ui.unmount()
})

test('the other language is translated from the story alone, without marks', async ($, on) => {
  world(on, URDU)
  let sent = ''
  on('model.complete', async (_$: any, e: any) => { sent = e.prompt; return { value: { isAnswered: true, text: 'The orders page was slow.', usage: {} } } })
  const ui = await $.ui.mount({ plugin: 'shoga-speaks', surface: 'terminal', ...row(LAYERED) })
  const btn = await ui.find({ type: 'Button', text: /English/ })
  await ui.press({ key: btn!.key! })
  await ui.redraw()
  expect(sent).toMatch(/Ab batching se/)
  expect(sent).not.toMatch(/\{\{|OrderList|Terms/)
  await ui.unmount()
})

test('technical first: the technical part is shown, the story is folded, "story" unfolds them all', async ($, on) => {
  world(on, { ...URDU, lead: 'technical' })
  let ui = await $.ui.mount({ plugin: 'shoga-speaks', surface: 'terminal', ...row(LAYERED) })
  expect(await ui.find({ type: 'Markdown', text: /OrderList\.load/ })).toBeDefined()
  expect(await ui.find({ type: 'Markdown', text: /Orders page slow tha/ })).toBeUndefined()
  const btn = await ui.find({ type: 'Button', text: /Story/ })
  await ui.press({ key: btn!.key! })
  expect(await ui.find({ type: 'Markdown', text: /Orders page slow tha/ })).toBeDefined()
  await ui.unmount()
  const r: any = await $.prompt.submit({ text: 'story' } as any)
  expect(r.drop).toMatch(/Story shown/)
})

test('technical only: a reply with no story is drawn as one part', async ($, on) => {
  world(on, { ...URDU, lead: 'technical-only' })
  const reply = '`OrderList.load()` ek query per order chalata hai, {{N+1}} problem.\n\n▸ Terms\n- N+1: har item ke liye alag query\n\n▸ English: "en" likhein'
  const ui = await $.ui.mount({ plugin: 'shoga-speaks', surface: 'terminal', ...row(reply) })
  expect(await ui.find({ type: 'Markdown', text: /ek query per order chalata hai, N\+1 problem/ })).toBeDefined()
  expect(await ui.find({ type: 'Button', text: /Story|Technical/ })).toBeUndefined()
  expect(await ui.find({ type: 'Button', text: /^N\+1$/ })).toBeDefined()
  await ui.unmount()
})
