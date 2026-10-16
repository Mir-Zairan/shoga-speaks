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
//   opts: { avoid: avoidList(...), latinOnly, budget (words, 0 = none), noCode (bool) }
export function checkReply(text, opts) {
  const p = prose(text);
  const issues = [];
  const words = wordCount(text);
  if (words < 15) return { words, issues };

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

export function describeIssues(issues) {
  return issues.map((i) => {
    if (i.kind === "hard-words") return `used hard words (${i.detail.join(", ")})`;
    if (i.kind === "script-mix") return `mixed in characters from another script (${i.detail.join(" ")})`;
    if (i.kind === "too-long") return `was ${i.detail[0]} words, the limit is about ${i.detail[1]}`;
    if (i.kind === "code-for-role") return "showed a code block to a non-developer role";
    return i.kind;
  }).join("; ");
}

export const isSevere = (issues) => issues.some((i) =>
  i.kind === "script-mix" || (i.kind === "hard-words" && i.detail.length >= 2) || (i.kind === "too-long" && i.detail[0] > i.detail[1] * 1.5));

// ---------- commands ----------

const RISK_RANK = { danger: 3, caution: 2, info: 1 };

// The most serious entry of the table that matches a shell command, or null.
export function matchCommand(command, table) {
  let best = null;
  for (const entry of table || []) {
    let re;
    try { re = new RegExp(entry.match, "i"); } catch { continue; }
    if (!re.test(String(command || ""))) continue;
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

// ---------- shortcuts ----------

export const HINT_LINE = /^[ \t]*▸[^\n]*"(en|tr)"[^\n]*$/m;

export function idOf(text) {
  let h = 0;
  for (let i = 0; i < text.length; i++) h = (h * 31 + text.charCodeAt(i)) | 0;
  return "m" + (h >>> 0).toString(36);
}
