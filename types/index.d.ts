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
  termHints: boolean
  lead: 'story' | 'technical' | 'technical-only'
  knownTerms: string[]
  enabled: boolean
  // Set by the mod itself: read in a browser ("shoga web on" or a cloud session).
  web?: boolean
}

declare module 'claude-code' {
  interface PluginState {
    'shoga-speaks': {
      open: Record<string, boolean>
      showAll: boolean
      foldOpen: Record<string, boolean>
      foldAll: boolean
      card: Record<string, string>
    }
  }
}
