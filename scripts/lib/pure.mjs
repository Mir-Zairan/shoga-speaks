// Pure helpers shared by the Node hook script and the display mod.
// No Node or engine imports here: both runtimes load this file.

// ---------- markdown docs (language and role files) ----------

export function parseDoc(text) {
  const meta = {};
  let body = String(text || "");
  const m = body.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (m) {
    body = body.slice(m[0].length);
    for (const line of m[1].split(/\r?\n/)) {
      const i = line.indexOf(":");
      if (i < 1) continue;
      const key = line.slice(0, i).trim();
      let val = line.slice(i + 1).trim();
      if (val.startsWith("[") && val.endsWith("]")) val = val.slice(1, -1).split(",").map((s) => s.trim()).filter(Boolean);
      else if (val === "true" || val === "false") val = val === "true";
      meta[key] = val;
    }
  }
  const sections = {};
  const parts = body.split(/^## +(\S+)[^\S\r\n]*$/m);
  sections._intro = parts[0].trim();
  for (let i = 1; i < parts.length; i += 2) sections[parts[i].toLowerCase()] = (parts[i + 1] || "").trim();
  return { meta, sections, body: body.trim() };
}

// "- hard / harder → easy" lines of a section, as [{ avoid: [...], use }]
export function avoidList(sectionText) {
  const out = [];
  for (const line of String(sectionText || "").split(/\r?\n/)) {
    const m = line.match(/^\s*-\s*(.+?)\s*→\s*(.+?)\s*$/);
    if (!m) continue;
    const avoid = m[1].split("/").map((s) => s.trim()).filter((s) => s.length > 1);
    if (avoid.length) out.push({ avoid, use: m[2] });
  }
  return out;
}

// ---------- reply text ----------

// Prose only: fenced code, inline code and URLs removed.
export function prose(text) {
  return String(text || "")
    .replace(/```[\s\S]*?(```|$)/g, " ")
    .replace(/`[^`\n]*`/g, " ")
    .replace(/https?:\/\/\S+/g, " ");
}

export const wordCount = (text) => (prose(text).match(/[\p{L}\p{N}][\p{L}\p{N}'’-]*/gu) || []).length;

const NATIVE_SCRIPT = /[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿ऀ-ॿ]/gu;
const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

// Deterministic checks of one reply against the user's settings.
//   opts: { avoid: avoidList(...), latinOnly, budget (words, 0 = none), noCode (bool),
//           shown (the part the length budget counts; default: all of text) }
export function checkReply(text, opts) {
  const p = prose(text);
  const issues = [];
  // The layer checks run on every reply: a short one can still fold a question away.
  const layers = splitLayers(text);
  if (layers.tech && foldedQuestion(layers.tech, opts.moreDetail)) issues.push({ kind: "question-folded", detail: [] });
  // A listed term the reply never uses has nothing to underline.
  const body = `${layers.story}\n${layers.tech}`;
  const missing = layers.terms.filter((t) => !markedTerms(ensureMarks(body, [t])).length).map((t) => t.term);
  if (missing.length) issues.push({ kind: "terms-missing", detail: missing });
  if (wordCount(text) < 15) return { words: wordCount(text), issues };
  const words = wordCount(opts.shown ?? text);

  const used = new Set();
  for (const { avoid } of opts.avoid || []) {
    for (const w of avoid) {
      const isLatin = /^[\p{Script=Latin}\s'’-]+$/u.test(w);
      const re = isLatin ? new RegExp(`(^|[^\\p{L}])${escapeRe(w)}(?=$|[^\\p{L}])`, "iu") : null;
      if (isLatin ? re.test(p) : p.includes(w)) used.add(w);
    }
  }
  if (used.size) issues.push({ kind: "hard-words", detail: [...used] });

  if (opts.latinOnly) {
    const mixed = p.match(NATIVE_SCRIPT);
    if (mixed) issues.push({ kind: "script-mix", detail: [...new Set(mixed)].slice(0, 8) });
  }
  if (opts.budget && words > opts.budget) issues.push({ kind: "too-long", detail: [words, opts.budget] });
  if (opts.noCode && /```/.test(text)) issues.push({ kind: "code-for-role", detail: [] });
  return { words, issues };
}

// A question or an offer to the reader inside the technical part, which is folded away
// unread: a "?" right after a word (not in code, quotes or a URL), the language's "more
// detail" line, or a usual offer phrase.
const OFFER = /\b(let me know|want me to|shall i|should i|do you want|would you like|chahein to|chahte hain to|kar doon|bata dein|batayein|zal ik|wil je|laat (me|het) weten)\b/i;
export function foldedQuestion(tech, moreDetail) {
  const t = prose(tech).replace(/"[^"\n]*"|“[^”\n]*”|'[^'\n]*'/g, " ");
  return /\p{L}[?؟](?=\s|$|[()[\].,;:!])/u.test(t) || !!(moreDetail && t.includes(moreDetail)) || OFFER.test(t);
}

export function describeIssues(issues) {
  return issues.map((i) => {
    if (i.kind === "hard-words") return `used hard words (${i.detail.join(", ")})`;
    if (i.kind === "script-mix") return `mixed in characters from another script (${i.detail.join(" ")})`;
    if (i.kind === "too-long") return `was ${i.detail[0]} words, the limit is about ${i.detail[1]}`;
    if (i.kind === "code-for-role") return "showed a code block to a non-developer role";
    if (i.kind === "terms-missing") return `listed terms that are not in the text (${i.detail.join(", ")}): list each term exactly as written in the reply`;
    if (i.kind === "question-folded") return "ended the folded technical part with a question or offer (put it at the end of the story, before ▸ Technical)";
    return i.kind;
  }).join("; ");
}

export const isSevere = (issues) => issues.some((i) =>
  i.kind === "script-mix" || (i.kind === "hard-words" && i.detail.length >= 2) || (i.kind === "too-long" && i.detail[0] > i.detail[1] * 1.5));

// ---------- commands ----------

const RISK_RANK = { danger: 3, caution: 2, info: 1 };

// The most serious entry of the table that matches a shell command, or null.
// The command as a risky-command pattern reads it: text quoted for echo or printf, a commit
// message and a grep pattern are words, not commands, so they are blanked.
export function commandShape(command) {
  return String(command || "").replace(/(\b(?:echo|printf)\b|(?:^|\s)(?:-m|--message|--grep)(?=[\s=])|\b(?:grep|egrep|fgrep|rg|ag)\b(?:\s+-{1,2}[\w=-]+)*)\s*=?\s*("(?:[^"\\]|\\.)*"|'[^']*')/g, (_, pre) => `${pre} ''`);
}

export function matchCommand(command, table) {
  let best = null;
  const shape = commandShape(command);
  for (const entry of table || []) {
    let re;
    // Case-insensitive unless the entry says otherwise ("-D" is not "-d").
    try { re = new RegExp(entry.match, entry.flags ?? "i"); } catch { continue; }
    if (!re.test(shape)) continue;
    if (!best || RISK_RANK[entry.risk] > RISK_RANK[best.risk]) best = entry;
  }
  return best;
}

export const riskAtLeast = (risk, floor) => (RISK_RANK[risk] || 0) >= (RISK_RANK[floor] || 99);

// Text of an entry in the user's language: "urdu:roman", then "urdu", then English.
export function entryText(entry, langKey) {
  const t = entry?.text || {};
  return t[langKey] || t[String(langKey).split(":")[0]] || t.english || "";
}

export const RISK_MARK = { danger: "⚠️", caution: "•", info: "ℹ️" };

// ---------- glossary ----------

// Terms of the glossary that a reply uses, in order of first use, minus the known ones.
export function findTerms(text, glossary, known = [], max = 5) {
  const p = prose(text);
  const knownSet = new Set(known.map((k) => k.toLowerCase()));
  const hits = [];
  for (const g of glossary || []) {
    if (knownSet.has(g.id) || knownSet.has(g.term.toLowerCase())) continue;
    let at = -1;
    for (const alias of [g.term, ...(g.aliases || [])]) {
      const m = p.match(new RegExp(`(^|[^\\p{L}\\p{N}])${escapeRe(alias)}(?=$|[^\\p{L}\\p{N}])`, "iu"));
      if (m && (at < 0 || m.index < at)) at = m.index;
    }
    if (at >= 0) hits.push({ ...g, at });
  }
  return hits.sort((a, b) => a.at - b.at).slice(0, max);
}

// ---------- layers: the story, the technical part, terms ----------
// A reply written in the "folded" layout (core/layers.md):
//   story … ▸ Technical … technical part … ▸ Terms … "- term: meaning" … language line

const TERM_MARK = /\{\{(\S(?:[^{}\n]{0,58}\S)?)\}\}/g;
const CODE_SPAN = /(```[\s\S]*?(?:```|$)|`[^`\n]*`)/g;
// Spans no term is marked in: code, markdown links (text and target), autolinks, bare URLs.
const PROTECTED = /(```[\s\S]*?(?:```|$)|`[^`\n]*`|!?\[[^\]\n]*\]\([^)\n]*\)|<https?:[^>\s]*>|https?:\/\/[^\s)>\]]+)/g;
// Starts a mark made from a code span that is exactly the term, so it keeps its code look.
export const CODE_TERM = "⁣";

export const termId = (term) => String(term).toLowerCase().replace(/[`*_⁣]/g, "").trim().replace(/[^\p{L}\p{M}\p{N}+#.]+/gu, "-").replace(/^-+|-+$/g, "");
// What a mark draws as: its words, a code span again for a mark made from one.
export const termText = (mark) => (String(mark).startsWith(CODE_TERM) ? `\`${mark.slice(1)}\`` : mark);

// Applies fn to the prose of a markdown text, leaving code spans and fences alone.
function mapProse(text, fn) {
  return String(text || "").split(CODE_SPAN).map((part, i) => (i % 2 ? part : fn(part))).join("");
}

// Rewrites each {{term}} mark outside code: fn(term) returns what to draw.
export const markTerms = (text, fn) => mapProse(text, (p) => p.replace(TERM_MARK, (_, t) => fn(t)));
export const unmark = (text) => markTerms(text, termText);

// The marked terms of a text, in order, once each.
export function markedTerms(text) {
  const seen = new Map();
  markTerms(text, (t) => { const id = termId(t); if (id && !seen.has(id)) seen.set(id, t.replace(CODE_TERM, "")); return t; });
  return [...seen].map(([id, term]) => ({ id, term }));
}

export const hasMark = (line) => markedTerms(line).length > 0;

// Marks the first plain use of each listed term that is not marked yet, longest term first
// so "idempotency key" wins over "key". Case is free, and a Latin word may take a plural
// "s"/"es". Never inside code, links, URLs or another mark; a code span that is exactly the
// term becomes the mark. Terms not found are left out: nothing to highlight.
export function ensureMarks(text, terms) {
  let out = String(text || "");
  const have = new Set(markedTerms(out).map((t) => t.id));
  for (const { id, term } of [...terms].sort((a, b) => b.term.length - a.term.length)) {
    if (have.has(id) || !term) continue;
    const plural = /^[\p{Script=Latin}\p{N}\s'’+#.-]*\p{L}$/u.test(term) ? "(?:e?s)?" : "";
    const word = new RegExp(`(^|[^\\p{L}\\p{M}\\p{N}{])(${escapeRe(term)}${plural})(?=$|[^\\p{L}\\p{M}\\p{N}}])`, "iu");
    let done = false;
    out = out.split(PROTECTED).map((part, i) => {
      if (done) return part;
      if (i % 2) {
        if (!part.startsWith("`") || part.startsWith("```")) return part;
        if (part.slice(1, -1).trim().toLowerCase() !== term.toLowerCase()) return part;
        done = true;
        return `{{${CODE_TERM}${part.slice(1, -1).trim()}}}`;
      }
      return part.split(/(\{\{[^{}\n]*\}\})/).map((bit, j) => (done || j % 2 ? bit
        : bit.replace(word, (_, pre, hit) => { done = true; return `${pre}{{${hit}}}`; }))).join("");
    }).join("");
    if (done) have.add(id);
  }
  return out;
}

// One line of markdown as runs: { kind: "text" | "code" | "term", text, id?, and the styles
// bold, italic, strike, code, href }. Knows code, links, bold, italic, strikethrough, a few
// HTML tags, escapes and {{term}} marks, nested, so none of their syntax is drawn raw.
const INLINE = /`([^`\n]+)`|!?\[([^\]\n]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)|(\*\*\*|___)(.+?)\4|(\*\*|__)(.+?)\6|~~(.+?)~~|<(b|strong|i|em|s|del|code)>(.*?)<\/\9>|(?<![\p{L}\p{N}*])\*(?![\s*])(.+?)(?<![\s*])\*(?![\p{L}\p{N}*])|(?<![\p{L}\p{N}_])_(?![\s_])(.+?)(?<![\s_])_(?![\p{L}\p{N}_])|\\([\\`*_{}[\]()#+\-.!~>|<])|\{\{(\S(?:[^{}\n]{0,58}\S)?)\}\}/gu;
const styleOf = (st) => Object.fromEntries(Object.entries(st).filter(([, v]) => v));
export function inlineSegments(line, style = {}, out = []) {
  const s = String(line);
  const re = new RegExp(INLINE.source, "gu");
  const plain = (t) => { if (t) out.push({ kind: style.code ? "code" : "text", text: t, ...styleOf(style) }); };
  let last = 0;
  let m;
  while ((m = re.exec(s))) {
    plain(s.slice(last, m.index));
    last = re.lastIndex;
    if (m[1] !== undefined) out.push({ kind: "code", text: m[1], ...styleOf({ ...style, code: true }) });
    else if (m[3] !== undefined) inlineSegments(m[2], { ...style, href: m[3] }, out);
    else if (m[4]) inlineSegments(m[5], { ...style, bold: true, italic: true }, out);
    else if (m[6]) inlineSegments(m[7], { ...style, bold: true }, out);
    else if (m[8] !== undefined) inlineSegments(m[8], { ...style, strike: true }, out);
    else if (m[9]) {
      const tag = { b: "bold", strong: "bold", i: "italic", em: "italic", code: "code" }[m[9]] || "strike";
      inlineSegments(m[10], { ...style, [tag]: true }, out);
    } else if (m[11] !== undefined) inlineSegments(m[11], { ...style, italic: true }, out);
    else if (m[12] !== undefined) inlineSegments(m[12], { ...style, italic: true }, out);
    else if (m[13] !== undefined) plain(m[13]);
    else if (m[14] !== undefined) {
      const code = m[14].startsWith(CODE_TERM);
      out.push({ kind: "term", text: code ? m[14].slice(1) : m[14], id: termId(m[14]), ...styleOf({ ...style, code: code || style.code }) });
    }
  }
  plain(s.slice(last));
  return out;
}

// "- term: meaning" lines of a ▸ Terms block.
function parseTermList(block) {
  const out = [];
  for (const line of String(block || "").split(/\r?\n/)) {
    const m = line.match(/^\s*[-*•]\s*(.+?)\s*(?::|—|–| - )\s+(.+?)\s*$/);
    if (!m) continue;
    const term = m[1].replace(/[{}`*]/g, "").trim();
    if (term) out.push({ id: termId(term), term, meaning: m[2] });
  }
  return out;
}

// A marker line: "▸ Name", maybe as a heading or in bold, maybe with a colon. On the
// Technical line, text after it starts the technical part; the plain-layout offer
// (`▸ Technical: "tech" …`) names its keyword in quotes and is no marker.
const markerLine = (name) => new RegExp(`^[ \\t]*(?:#{1,6}[ \\t]+)?(?:\\*\\*|__)?[ \\t]*▸[ \\t]*${name}[ \\t]*(?:\\*\\*|__)?[ \\t]*:?[ \\t]*(?:\\*\\*|__)?[ \\t]*(.*?)[ \\t]*$`);
const TECH_MARK = markerLine("Technical");
const TERMS_MARK = markerLine("Terms");
const HINT_ROW = /^[ \t]*▸[^\n]*"(en|tr)"[^\n]*$/;

// Splits a reply into its layers. Markers inside code fences are code. A reply without the
// markers is all story.
export function splitLayers(text) {
  const lines = String(text || "").replace(/\r\n?/g, "\n").split("\n");
  let fence = false;
  let hintAt = -1, techAt = -1, termsAt = -1, techHead = "";
  lines.forEach((line, i) => {
    if (/^\s*(```|~~~)/.test(line)) { fence = !fence; return; }
    if (fence) return;
    if (HINT_ROW.test(line)) { hintAt = i; return; }
    if (techAt < 0 && termsAt < 0) {
      const m = line.match(TECH_MARK);
      if (m && !/"tech"/.test(m[1])) { techAt = i; techHead = m[1]; return; }
    }
    if (termsAt < 0 && TERMS_MARK.test(line)) termsAt = i;
  });
  const hint = hintAt >= 0 ? lines[hintAt].trim() : null;
  const keep = (from, to) => lines.slice(from, to).filter((_, k) => from + k !== hintAt).join("\n");
  const end = lines.length;
  const terms = termsAt >= 0 ? parseTermList(keep(termsAt + 1, end)) : [];
  const techEnd = termsAt >= 0 ? termsAt : end;
  const tech = techAt >= 0 ? [techHead, keep(techAt + 1, techEnd)].filter((x) => x.trim()).join("\n").trim() : "";
  const storyEnd = techAt >= 0 ? techAt : termsAt >= 0 ? termsAt : end;
  return { story: keep(0, storyEnd).trim(), tech, terms, hint };
}

// The part of a reply shown unfolded, the one the length check counts, marks removed.
export function shownOf(text, lead = "story") {
  const l = splitLayers(text);
  return unmark((lead === "technical" || lead === "technical-only" || !l.story) && l.tech ? l.tech : l.story);
}

// About which row of a drawn markdown block a character index lands on.
export function rowAt(text, index, columns) {
  const cols = Math.max(20, columns || 80);
  let row = 0;
  for (const line of String(text).slice(0, index).split("\n").slice(0, -1)) row += Math.max(1, Math.ceil(line.length / cols));
  const last = String(text).slice(0, index).split("\n").pop() || "";
  return row + Math.floor(last.length / cols);
}

// ---------- shortcuts ----------

export const HINT_LINE = /^[ \t]*▸[^\n]*"(en|tr)"[^\n]*$/m;

export function idOf(text) {
  let h = 0;
  for (let i = 0; i < text.length; i++) h = (h * 31 + text.charCodeAt(i)) | 0;
  return "m" + (h >>> 0).toString(36);
}
