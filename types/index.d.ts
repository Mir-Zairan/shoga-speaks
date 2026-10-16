// What the classic SessionStart hook writes for the display mod (state/<session>.json → resolved).
export type ModSettings = {
  language: string
  script: string
  langKey: string
  mineKey: string
  bilingual: boolean
  cliEnglish: boolean
  openLabel: string
  otherLabel: string
  otherKey: 'en' | 'tr'
  otherRtl: boolean
  otherGuide: string
  roles: string[]
  primaryRole: string
  explainCommands: boolean
  glossaryHover: boolean
  knownTerms: string[]
  enabled: boolean
}

declare module 'claude-code' {
  interface PluginState {
    'shoga-speaks': {
      open: Record<string, boolean>
      showAll: boolean
      glossOpen: Record<string, boolean>
    }
  }
}
