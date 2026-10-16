import { test, expect, mock } from 'claude-code/testing'

const URDU = {
  language: 'urdu', script: 'roman', langKey: 'urdu:roman', mineKey: 'urdu:roman',
  bilingual: true, cliEnglish: false, openLabel: 'Roman-Urdu', otherLabel: 'English', otherKey: 'en',
  otherRtl: false, otherGuide: 'Plain English.', roles: ['qa'], primaryRole: 'QA / Tester',
  explainCommands: true, glossaryHover: true, knownTerms: [], enabled: true,
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
