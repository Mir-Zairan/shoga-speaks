# Shoga-Speaks: artifacts and pages

Applies to every artifact, HTML page or shareable document you create.
A Shoga page must be read in under a minute for the main point, and must never
feel heavy. Focus comes first, decoration last.

## Page structure (top to bottom)
1. **Title**: plain words, what this is about.
2. **One line**: the point of the whole page in one sentence.
3. **Key points**: three at most, each one short line.
4. **Picture over paragraph**: if a table, before/after, flow or diagram can replace
   three or more sentences, use it.
5. **What you need to do**: a short checklist for the reader's role(s).
6. **Details**: anything technical or long goes in collapsed `<details>` sections.

## Writing
- Same rules as chat: simple words, one idea per line, point first, role-aware.
- Short sections. A section that needs scrolling is too long; split or collapse it.
- Bold one thing per section at most.
- No filler intros ("In this document we will …"), no closing summaries that repeat.
- No decoration that does not help understanding.

## Language switch
- Add a switch at the top for every entry in `artifacts.switch_languages`
  (format `language:script`, for example `urdu:roman`, `urdu:native`, `english`).
- The page opens in the user's own language and script.
- Write the full content once per language. Same structure, same facts.
- Mark each block with the right `lang` attribute, and `dir="rtl"` for right-to-left scripts.
- Remember the reader's choice in `localStorage` (wrap reads/writes in try/catch;
  the page must work without it).
- If `artifacts.role_switch` is true, also add a "View as" switch for the roles listed.
  Otherwise write for the user's roles only.

## Fonts per script
Load from Google Fonts only what the page uses:
- Urdu / Kashmiri / Punjabi (Shahmukhi) native: `Noto Nastaliq Urdu`, generous line-height (2+)
- Arabic / Persian: `Noto Naskh Arabic`
- Hindi / Devanagari: `Noto Sans Devanagari`
- Latin scripts (English, Roman-Urdu, Dutch …): a clean sans-serif

## If artifacts are not available
If there is no artifact tool in this session, write the same page as a single
self-contained `.html` file and tell the user where it is.
