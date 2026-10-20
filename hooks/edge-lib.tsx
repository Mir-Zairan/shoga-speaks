// Helpers for shoga-mod.edge.test.tsx (not a test file itself): settings, a mount, and a
// compact outline of the drawn tree.
import { mock } from 'claude-code/testing'
export const URDU = {
  language: 'urdu', script: 'roman', langKey: 'urdu:roman', mineKey: 'urdu:roman',
  bilingual: true, cliEnglish: false, openLabel: 'Roman-Urdu', otherLabel: 'English', otherKey: 'en',
  otherRtl: false, otherGuide: 'Plain English.', roles: ['qa'], primaryRole: 'QA / Tester',
  explainCommands: true, termHints: true, lead: 'story', knownTerms: [], enabled: true,
}
export const ENGLISH = { ...URDU, language: 'english', langKey: 'english', bilingual: false, openLabel: 'English', otherLabel: 'Roman-Urdu', otherKey: 'tr', primaryRole: 'Product Owner' }
export function world(on: any, state: object) {
  mock.env(on, { SHOGA_STATE_JSON: JSON.stringify(state) })
  mock.store(on); mock.clock(on)
  on('ui.status', () => ({ value: undefined }))
  on('ui.notice', () => ({ value: undefined }))
  on('model.complete', async () => ({ value: { isAnswered: true, text: 'TRANSLATED', usage: {} } }))
  on('prompt.submit', async (_$: any, e: any) => ({ text: e.text }) as any)
  on('ui.render', async ($: any, e: any) => { const { Text } = $.ui.resolve(e); return <Text>engine-default</Text> })
}
export const row = (text: string) => ({ component: 'AssistantMessage', props: { text, isFirstOfReply: true } }) as const
// A compact outline of the drawn tree: M«markdown» for Markdown, R[...] for a word-by-word row,
// T«term»{top,left,width} for an underlined term with its card, B«label» for a button, _ for a gap.
export function outline(el: any): string {
  if (!el) return ''
  const p = el.props || {}
  if (el.type === 'Markdown') return `M«${p.text}»`
  if (el.type === 'Button') return `B«${p.label}»`
  if (el.type === 'Text' && p.underline) return `T«${(el.children || []).join('')}${p.bold ? '|b' : ''}»`
  if (el.type === 'Text') return (el.children || []).map((c: any) => (typeof c === 'string' ? c : outline(c))).join('')
  if (el.type === 'Box' && p.position === 'absolute') return `{top:${p.top},left:${p.left},w:${p.width}}`
  const inner = (el.children || []).map(outline).join('')
  if (p.flexWrap === 'wrap') return ` R[${inner}] `
  return inner === ' ' ? ' _ ' : inner
}
export async function mount($: any, surface: string, text: string, cols = 80) {
  return $.ui.mount({ plugin: 'shoga-speaks', surface, viewport: { columns: cols, rows: 40 }, ...row(text) })
}
export async function draw($: any, surface: string, text: string, cols = 80) {
  const ui = await mount($, surface, text, cols)
  const all = await ui.findAll({})
  const out = outline(all[0])
  await ui.unmount()
  return out
}
