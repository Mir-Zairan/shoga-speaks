#!/usr/bin/env node
// Shoga-Speaks hook entry point (classic command hooks).
//   session-start  loads rules, language, roles, glossary, level and known terms into context
//   prompt         per-prompt reminder + shortcuts (en/tr, ??, shoga ...)
//   stop           checks the finished reply (hard words, script mix, length, code for role)
//   pre-tool       explains risky shell commands in the approval prompt
//   tool-failure   asks for a plain explanation when a test/build command fails
//   resolve        prints the active settings as JSON (used by the skills)
// No dependencies. Any failure exits 0 silently so Claude Code is never blocked.

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";
import {
  parseDoc, avoidList, checkReply, describeIssues, isSevere,
  matchCommand, riskAtLeast, entryText, shownOf, unmark,
} from "./lib/pure.mjs";
import COMMANDS from "../data/commands.mjs";

const ROOT = process.env.CLAUDE_PLUGIN_ROOT || path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const HOME = process.env.SHOGA_HOME || path.join(os.homedir(), ".claude", "shoga-speaks");
const LENGTH_GUIDE = {
  short: "short: 3-5 lines per point, the whole answer fits on one screen",
  medium: "medium: up to about 15 lines, still structured",
  detailed: "detailed: full explanation allowed, but still point first and structured",
};
const WORD_BUDGET = { short: 250, medium: 450, detailed: 0 };
const LEVELS = {
  "-2": "The user is new to tech. No jargon at all; everyday examples; very short sentences.",
  "-1": "Explain every technical term in a few everyday words; add one simple example when it helps.",
  "0": "",
  "1": "The user knows the basics of their field; skip basic explanations.",
  "2": "The user is an expert; be terse and skip explanations of standard terms.",
};
const NON_CODE_ROLES = new Set(["po", "pm", "support"]);
const FAILURE_WORTHY = /\b(test|tests|phpunit|pytest|jest|vitest|build|compile|tsc|webpack|vite|lint|eslint|phpstan|psalm|install|migrate|migration|deploy|make)\b/i;
const GLOSSARY_LIMIT = 3000;

// ---------- io ----------

const readText = (p) => { try { return fs.readFileSync(p, "utf8"); } catch { return null; } };
const readJson = (p) => {
  const t = readText(p);
  if (t == null) return null;
  try { return JSON.parse(t); } catch { return { __invalid: p }; }
};
const writeJson = (p, v) => {
  try { fs.mkdirSync(path.dirname(p), { recursive: true }); fs.writeFileSync(p, JSON.stringify(v, null, 1)); } catch {}
};
const readStdin = () => { try { return JSON.parse(fs.readFileSync(0, "utf8") || "{}"); } catch { return {}; } };
const emit = (obj) => process.stdout.write(JSON.stringify(obj));

function deepMerge(base, over) {
  if (!over || typeof over !== "object" || Array.isArray(over)) return base;
  const out = { ...base };
  for (const [k, v] of Object.entries(over)) {
    out[k] = v && typeof v === "object" && !Array.isArray(v) && base[k] && typeof base[k] === "object" ? deepMerge(base[k], v) : v;
  }
  return out;
}

// ---------- settings, profile, session state ----------

function settingsPaths(cwd) {
  const project = process.env.CLAUDE_PROJECT_DIR || cwd || process.cwd();
  return {
    user: path.join(os.homedir(), ".claude", "shoga-speaks.json"),
    team: path.join(project, ".claude", "shoga-speaks.json"),
    local: path.join(project, ".claude", "shoga-speaks.local.json"),
    glossary: path.join(project, ".claude", "shoga-speaks", "glossary.md"),
  };
}

// Precedence: plugin defaults < team (project) < user < personal project override.
function loadSettings(cwd) {
  const p = settingsPaths(cwd);
  const notes = [];
  let s = readJson(path.join(ROOT, "defaults", "settings.json")) || {};
  let found = false;
  for (const file of [p.team, p.user, p.local]) {
    const j = readJson(file);
    if (!j) continue;
    if (j.__invalid) { notes.push(`could not read ${file} (invalid JSON), ignoring it`); continue; }
    s = deepMerge(s, j);
    found = true;
  }
  if (typeof s.roles === "string") s.roles = [s.roles];
  return { settings: s, notes, found, paths: p };
}

const profilePath = () => path.join(HOME, "profile.json");
function loadProfile() {
  const p = readJson(profilePath());
  const prof = p && !p.__invalid ? p : {};
  return { level: Math.max(-2, Math.min(2, Number(prof.level) || 0)), known_terms: prof.known_terms || [], stats: prof.stats || { checked: 0, slipped: 0 } };
}
const saveProfile = (prof) => writeJson(profilePath(), prof);

const sid = (id) => String(id || "default").replace(/[^\w.-]/g, "_");
const statePath = (id) => path.join(HOME, "state", `${sid(id)}.json`);
const sessionState = (id) => { const j = readJson(statePath(id)); return j && !j.__invalid ? j : {}; };
const setSessionState = (id, patch) => writeJson(statePath(id), { ...sessionState(id), ...patch });
const modActive = (id) => fs.existsSync(path.join(HOME, "state", `${sid(id)}.mod`));

// ---------- language / role resolution ----------

function listLanguages() {
  try { return fs.readdirSync(path.join(ROOT, "languages")).filter((f) => f.endsWith(".md") && !f.startsWith("_")).map((f) => f.slice(0, -3)); }
  catch { return ["english"]; }
}

function loadLanguage(name, notes) {
  const safe = String(name || "english").toLowerCase().replace(/[^a-z0-9_-]/g, "");
  const text = safe.startsWith("_") ? null : readText(path.join(ROOT, "languages", `${safe}.md`));
  if (!text) {
    notes.push(`language "${name}" not found, using English (available: ${listLanguages().join(", ")})`);
    return { id: "english", ...parseDoc(readText(path.join(ROOT, "languages", "english.md"))) };
  }
  return { id: safe, ...parseDoc(text) };
}

function pickScript(lang, wanted, notes, what) {
  const scripts = [].concat(lang.meta.scripts || "native");
  const def = lang.meta.default_script || scripts[0];
  if (!wanted || wanted === "default") return def;
  if (scripts.includes(wanted)) return wanted;
  notes.push(`${what} "${wanted}" is not available for ${lang.id} (has: ${scripts.join(", ")}), using "${def}"`);
  return def;
}

function scriptInfo(lang, script) {
  const m = lang.meta;
  return {
    label: m[`label.${script}`] || lang.id,
    rtl: m[`rtl.${script}`] === true,
    latin: script === "roman" || m[`latin.${script}`] === true,
    moreDetail: m[`more_detail.${script}`] || "Want more detail?",
    hint: m[`hint.${script}`] || '▸ {other}: type "{key}"',
    key: [].concat(m.scripts || "native").length > 1 ? `${lang.id}:${script}` : lang.id,
  };
}

const guideOf = (lang, script) => [lang.sections.common, lang.sections[script]].filter(Boolean).join("\n\n");

function loadRoles(roles, notes) {
  const out = [];
  for (const r of roles || []) {
    const safe = String(r).toLowerCase().replace(/[^a-z0-9_-]/g, "");
    const t = readText(path.join(ROOT, "roles", `${safe}.md`));
    if (!t) { notes.push(`role "${r}" not found, skipping it`); continue; }
    out.push({ id: safe, ...parseDoc(t) });
  }
  if (!out.length) out.push({ id: "dev", ...parseDoc(readText(path.join(ROOT, "roles", "dev.md")) || "") });
  return out;
}

// Everything the handlers need, resolved once.
function resolve(cwd) {
  const { settings: s, notes, found, paths } = loadSettings(cwd);
  const lang = loadLanguage(s.language, notes);
  const script = pickScript(lang, s.script, notes, "script");
  const ghScript = pickScript(lang, !s.github_script || s.github_script === "default" ? script : s.github_script, notes, "github_script");
  const roles = loadRoles(s.roles, notes);
  const en = loadLanguage("english", []);
  const bilingual = lang.id !== "english";
  const english = scriptInfo(en, "native");
  const mine = scriptInfo(lang, script);
  const mineGh = scriptInfo(lang, ghScript);
  const cliEnglish = !bilingual || s.cli_open === "english";
  const open = cliEnglish ? english : mine;
  const other = cliEnglish ? mine : english;
  const otherKey = cliEnglish ? "tr" : "en";
  const hint = bilingual ? open.hint.replace("{other}", other.label).replace("{key}", otherKey) : null;
  const openLang = cliEnglish ? en : lang;
  const openScript = cliEnglish ? "native" : script;
  return {
    s, notes, found, paths, lang, script, ghScript, roles, bilingual, english, mine, mineGh,
    open, other, otherKey, hint, cliEnglish, openLang, openScript, profile: loadProfile(),
    otherGuide: cliEnglish ? guideOf(lang, script) : guideOf(en, "native"),
  };
}

const roleNames = (r) => r.roles.map((x) => x.meta.label || x.id).join(" + ");
const primaryRole = (r) => r.roles[0].meta.label || r.roles[0].id;
const extraRoles = (r) => r.roles.slice(1).map((x) => x.meta.label || x.id).join(", ");
const isOff = (r, id) => r.s.enabled === false || sessionState(id).off;
// glossary_hover is the 0.2.0 name of term_hints; either set to "off" turns the hints off.
const termHints = (s) => s.term_hints !== "off" && s.glossary_hover !== "off";
const offer = (r, label, key) => r.open.hint.replace("{other}", label).replace("{key}", key);
// Which layer leads: "story" (technical folded), "technical" (story folded) or "technical-only".
const leadOf = (s) => (["technical", "technical-only"].includes(s.layers) ? s.layers : "story");

// Layout names by lead: with the display mod, then without (core/layers.md, "Layout").
const LAYOUTS = {
  story: ["story + technical folded", "story only"],
  technical: ["technical + story folded", "technical, story on request"],
  "technical-only": ["technical only", "technical only"],
};

// The layout line of the per-prompt reminder.
function layout(r, id) {
  const mod = modActive(id);
  return ` Layout: ${LAYOUTS[leadOf(r.s)][mod ? 0 : 1]}${mod && termHints(r.s) ? ", term hints on" : ""}.`;
}

// core/layers.md with only the layouts this user's lead can get (a bullet names its layouts in backticks).
function layersDoc(r) {
  const names = LAYOUTS[leadOf(r.s)];
  const [head, list = ""] = (readText(path.join(ROOT, "core", "layers.md")) || "").split(/(?=^## Layout)/m);
  const kept = list.split(/^(?=- )/m).filter((b) => !b.startsWith("- ") || names.some((n) => b.split("\n")[0].includes(`\`${n}\``)));
  return (head + kept.join(""))
    .replace("{TECH_HINT}", offer(r, "Technical", "tech")).replace("{STORY_HINT}", offer(r, "Story", "story"));
}
const commandFloor = (s) => (s.explain_commands === "off" ? null : s.explain_commands === "caution" ? "caution" : "danger");

// Settings the display mod reads (it has no Node; it reads this file).
function writeModState(r, id) {
  const st = {
    language: r.lang.id, script: r.script, langKey: r.open.key, mineKey: r.mine.key,
    bilingual: r.bilingual, cliEnglish: r.cliEnglish,
    openLabel: r.open.label, otherLabel: r.other.label, otherKey: r.otherKey,
    otherRtl: r.other.rtl, otherGuide: r.otherGuide,
    roles: r.roles.map((x) => x.id), primaryRole: primaryRole(r),
    explainCommands: r.s.explain_commands !== "off",
    termHints: termHints(r.s),
    lead: leadOf(r.s),
    knownTerms: r.profile.known_terms,
    enabled: r.s.enabled !== false,
  };
  writeJson(path.join(HOME, "state", "latest.json"), st);
  setSessionState(id, { resolved: st });
}

// Who the user is, from local git and gh config (no network), so Claude can tell their own
// code (author, blame, PR) from code that is new to them. Only the gh login is read.
function whoIsUser(cwd) {
  const git = (key) => {
    try {
      return execFileSync("git", ["config", "--get", key], { cwd: cwd || process.cwd(), encoding: "utf8", timeout: 1500, stdio: ["ignore", "pipe", "ignore"] }).trim();
    } catch { return ""; }
  };
  const name = git("user.name"), email = git("user.email");
  const hosts = readText(path.join(process.env.GH_CONFIG_DIR || path.join(os.homedir(), ".config", "gh"), "hosts.yml")) || "";
  const login = (hosts.match(/^github\.com:\s*\n(?:[ \t]+.*\n)*?[ \t]+user:[ \t]*(\S+)/m) || [])[1] || "";
  return [name && email ? `${name} <${email}>` : name || email, login && `GitHub ${login}`].filter(Boolean).join(", ");
}

// ---------- SessionStart ----------

function sessionStart(input) {
  const r = resolve(input.cwd);
  const { s } = r;
  writeModState(r, input.session_id);
  if (isOff(r, input.session_id)) return;

  const parts = [];
  parts.push(`<shoga-speaks>\nThe user has the Shoga-Speaks plugin on. Follow these rules for every reply in this session, including output from other skills, commands and agents. They change how you explain things, never what you do.`);
  parts.push(readText(path.join(ROOT, "core", "rules.md")) || "");
  parts.push(layersDoc(r));

  const langLine = r.cliEnglish
    ? `Write chat replies in simple English${r.bilingual ? ` (the user's own language, ${r.mine.label}, is available on request)` : ""}.`
    : `Write chat replies in ${r.mine.label} (language: ${r.lang.id}, script: ${r.script}${r.mine.rtl ? ", right-to-left" : ""}).`;
  const level = LEVELS[String(r.profile.level)];
  const who = whoIsUser(input.cwd);
  parts.push(`# This user's settings
- ${langLine}
- Keep English technical terms: ${s.keep_english_terms !== false ? "yes" : "no, translate them when a common word exists"}.
${who ? `- The user: ${who}. Code by this author (git log, blame, a PR) is theirs; code you write in this session is new to them.
` : ""}- Length: ${LENGTH_GUIDE[s.length] || LENGTH_GUIDE.short}. When you stop early, end with: "${r.open.moreDetail}"
- Primary role: ${primaryRole(r)}. Write the whole answer for this role: what it cares about, what it leaves out, how it ends.${extraRoles(r) ? `
- Other roles: ${extraRoles(r)}. Each gets at most one short line, labelled with the role name. No code blocks for them unless the user asks.` : ""}${level ? `
- Level: ${level}` : ""}${r.profile.known_terms.length ? `
- Terms the user already knows (do not explain them): ${r.profile.known_terms.slice(0, 60).join(", ")}.` : ""}`);

  if (r.bilingual) {
    parts.push(`# The other language
Write only the open language. When a reply explains something (not for one-line confirmations), end it with this exact line:
${r.hint}
If the user then types "${r.otherKey}", repeat your previous explanation in ${r.other.label}: same content, same length, no new work and no tool calls.`);
  }

  parts.push(`# Language guide: ${r.open.label}\n${guideOf(r.openLang, r.openScript)}`);
  parts.push(`# Roles\n${r.roles.map((x) => `## ${x.meta.label || x.id}\n${x.body}`).join("\n\n")}`);

  const glossary = readText(r.paths.glossary);
  if (glossary) {
    const g = glossary.length > GLOSSARY_LIMIT ? glossary.slice(0, GLOSSARY_LIMIT) + `\n… (truncated, full file: ${r.paths.glossary})` : glossary;
    parts.push(`# Project glossary\nKeep these terms as written. Use the simple explanation when the reader's role may not know them.\n${g.trim()}`);
  }

  if (s.apply_to?.pr_comments !== false && r.bilingual) {
    const pr = (readText(path.join(ROOT, "core", "pr-comments.md")) || "").replace(/^# .*\n/, "");
    const ghOpen = s.github_open === "translated" ? r.mineGh.label : "English";
    const ghOther = s.github_open === "translated" ? "English" : r.mineGh.label;
    parts.push(`# GitHub comments\nOpen language: ${ghOpen}. Collapsed: ${ghOther} (language ${r.lang.id}, script ${r.ghScript}).\n${pr.trim()}`);
    if (r.ghScript !== r.script && r.lang.sections[r.ghScript]) {
      parts.push(`# Language guide for GitHub: ${r.mineGh.label}\n${r.lang.sections[r.ghScript]}`);
    }
  }

  if (s.apply_to?.artifacts !== false) {
    const sw = (s.artifacts?.switch_languages || ["mine", "english"]).map((x) => (x === "mine" ? `${r.lang.id}:${r.script}` : x));
    parts.push(`# Artifacts and pages
Before creating any artifact, HTML page or shareable document, read ${path.join(ROOT, "core", "artifacts.md")} and follow it.
Language switch: ${sw.join(", ")}. Role switch: ${s.artifacts?.role_switch ? `yes (${s.roles.join(", ")})` : "no"}.`);
  }

  const keep = [];
  if (!s.apply_to?.commit_messages) keep.push("commit messages");
  if (!s.apply_to?.code_comments) keep.push("code comments written into files");
  if (keep.length) parts.push(`# Stays English\n${keep.join(" and ")} stay in plain English.`);
  if (s.apply_to?.chat === false) parts.push(`# Chat\nChat replies are not changed by this plugin; only the areas above are.`);
  parts.push("</shoga-speaks>");

  const out = { hookSpecificOutput: { hookEventName: "SessionStart", additionalContext: parts.filter(Boolean).join("\n\n") } };
  const msg = [];
  if (input.source === "startup" || input.source === undefined) {
    msg.push(`🦜 Shoga-Speaks: ${r.open.label} · ${roleNames(r)} · ${s.length || "short"}`);
    if (!r.found) msg.push("Run /shoga-speaks:setup to choose your language and roles.");
  }
  if (r.notes.length) msg.push(`Shoga-Speaks: ${r.notes.join("; ")}`);
  if (msg.length) out.systemMessage = msg.join("\n");
  emit(out);
}

// ---------- UserPromptSubmit ----------

const block = (reason) => emit({ decision: "block", reason, suppressOriginalPrompt: true });
const splitTerms = (t) => t.split(/[,\n]/).map((x) => x.trim().toLowerCase()).filter(Boolean);

function prompt(input) {
  const raw = String(input.prompt || "").trim();
  const cmd = raw.toLowerCase().replace(/\s+/g, " ");
  const id = input.session_id;

  if (cmd === "shoga off" || cmd === "shoga on") {
    const off = cmd === "shoga off";
    setSessionState(id, { off });
    return block(off ? "🦜 Shoga-Speaks is off for this session. Type \"shoga on\" to turn it back on." : "🦜 Shoga-Speaks is on again for this session.");
  }

  const prof = loadProfile();
  if (cmd === "shoga simpler" || cmd === "shoga deeper") {
    prof.level = Math.max(-2, Math.min(2, prof.level + (cmd.endsWith("simpler") ? -1 : 1)));
    saveProfile(prof);
    return block(`🦜 Level is now ${prof.level} (-2 simplest … +2 expert). ${LEVELS[String(prof.level)] || "Default explanations."}`);
  }
  let m = raw.match(/^shoga\s+(know|forget)\s+(.+)$/i);
  if (m) {
    const terms = splitTerms(m[2]);
    const set = new Set(prof.known_terms);
    for (const t of terms) (m[1].toLowerCase() === "know" ? set.add(t) : set.delete(t));
    prof.known_terms = [...set].sort();
    saveProfile(prof);
    return block(`🦜 Known terms (${prof.known_terms.length}): ${prof.known_terms.join(", ") || "none"}`);
  }
  if (cmd === "shoga terms") return block(`🦜 Known terms (${prof.known_terms.length}): ${prof.known_terms.join(", ") || "none"}. Add with "shoga know term1, term2".`);

  const r = resolve(input.cwd);
  const { s } = r;
  const state = sessionState(id);

  if (cmd === "shoga status" || cmd === "shoga") {
    const { checked = 0, slipped = 0 } = prof.stats;
    return block([
      `🦜 Shoga-Speaks is ${isOff(r, id) ? "OFF" : "ON"}${modActive(id) ? " · display mod active" : ""}`,
      `Language: ${r.lang.id} (${r.mine.label}, script: ${r.script}) · CLI shows: ${r.open.label}`,
      `GitHub: ${s.github_open === "translated" ? r.mineGh.label : "English"} open, ${s.github_open === "translated" ? "English" : r.mineGh.label} collapsed`,
      `Roles: ${roleNames(r)} · Length: ${s.length || "short"} · Level: ${prof.level}`,
      `Known terms: ${prof.known_terms.length} · Replies checked: ${checked}, with slips: ${slipped}`,
      r.found ? `Settings: ${[r.paths.team, r.paths.user, r.paths.local].filter((f) => fs.existsSync(f)).join(", ")}` : "Settings: plugin defaults (run /shoga-speaks:setup)",
      ...r.notes.map((n) => `Note: ${n}`),
      `Shortcuts: "${r.bilingual ? r.otherKey : "en"}" other language · "tech" / "story" the other layer · "huh" simpler · "shoga simpler|deeper" · "shoga know <terms>" · "shoga off|on"`,
    ].join("\n"));
  }

  if (isOff(r, id)) return;

  let ctx;
  // "huh" is the one to type: a "?" in an empty prompt opens Claude Code's shortcut help.
  if (cmd === "??" || cmd === "huh" || cmd === "huh?" || cmd === "shoga ??") {
    if (prof.level > -2) { prof.level -= 1; saveProfile(prof); }
    ctx = `Shoga-Speaks: the user did not understand your previous reply. Explain the same thing again, simpler: shorter sentences, no jargon, one everyday example. Same language (${r.open.label}) and layout. No new work, no tool calls. From now on: ${LEVELS[String(prof.level)] || "use simple words"}`;
  } else if (cmd === "tech" || cmd === "story") {
    const part = cmd === "tech" ? "technical part" : "story";
    ctx = `Shoga-Speaks: the user typed "${cmd}". Give the ${part} of your previous explanation, as "The ${part}" describes it, in ${r.open.label}. No new work, no tool calls.`;
  } else if (r.bilingual && (cmd === "en" || cmd === "tr")) {
    const target = cmd === "en" ? r.english.label : r.mine.label;
    ctx = `Shoga-Speaks: the user typed "${raw}". Repeat your previous explanation in ${target}. Same content and length, simple words, no new work, no tool calls, no hint line at the end.`;
  } else {
    const lang = r.cliEnglish ? "simple English" : `${r.mine.label} (${r.lang.id}, ${r.script} script)`;
    ctx = `Shoga-Speaks reminder: reply in ${lang}; write for ${primaryRole(r)}${extraRoles(r) ? ` (${extraRoles(r)}: one line each at most)` : ""}; length ${s.length || "short"}. Point first, one idea per line, simple everyday words. Code, paths, commands and errors stay as-is.${r.hint ? ` If the reply explains something, end with: ${r.hint}` : ""}`;
    ctx += layout(r, id);
    if (state.last_issues) ctx += ` Your last reply ${state.last_issues}. Avoid that.`;
  }
  if (state.last_issues) setSessionState(id, { last_issues: null });
  emit({ hookSpecificOutput: { hookEventName: "UserPromptSubmit", additionalContext: ctx } });
}

// ---------- Stop: quality check ----------

function lastAssistantText(input) {
  if (typeof input.last_assistant_message === "string") return input.last_assistant_message;
  const t = input.transcript_path && readText(input.transcript_path);
  if (!t) return "";
  const lines = t.trim().split("\n");
  for (let i = lines.length - 1; i >= 0; i--) {
    try {
      const row = JSON.parse(lines[i]);
      const msg = row.message || row;
      if ((row.type || msg.role) !== "assistant") continue;
      const c = msg.content;
      const text = typeof c === "string" ? c : (c || []).filter((b) => b.type === "text").map((b) => b.text).join("\n");
      if (text.trim()) return text;
    } catch {}
  }
  return "";
}

// Words and script are checked in the whole reply; the length only in the part shown.
export function checkFor(r, text, shown) {
  return checkReply(unmark(text), {
    shown,
    avoid: avoidList(r.openLang.sections[r.openScript]),
    latinOnly: r.open.latin || r.openLang.id === "english",
    budget: WORD_BUDGET[r.s.length || "short"] ?? 250,
    noCode: NON_CODE_ROLES.has(r.roles[0].id),
  });
}

function stop(input) {
  if (input.stop_hook_active) return;
  const r = resolve(input.cwd);
  const mode = r.s.quality_guard || "remind";
  if (mode === "off" || isOff(r, input.session_id) || r.s.apply_to?.chat === false) return;
  const text = lastAssistantText(input);
  if (!text) return;

  const { issues } = checkFor(r, text, shownOf(text, leadOf(r.s)));
  const prof = loadProfile();
  prof.stats = { checked: (prof.stats.checked || 0) + 1, slipped: (prof.stats.slipped || 0) + (issues.length ? 1 : 0) };
  saveProfile(prof);
  if (!issues.length) return;

  const summary = describeIssues(issues);
  if (mode === "fix" && isSevere(issues)) {
    return emit({ decision: "block", reason: `Shoga-Speaks check: your reply ${summary}. Write it again with only those fixed: same content, same language (${r.open.label}), simple words. No tool calls.` });
  }
  setSessionState(input.session_id, { last_issues: summary });
}

// ---------- PreToolUse: explain risky commands ----------

const loadCommands = () => COMMANDS;

function preTool(input) {
  if (input.tool_name !== "Bash") return;
  const r = resolve(input.cwd);
  const floor = commandFloor(r.s);
  if (!floor || isOff(r, input.session_id) || modActive(input.session_id)) return;
  const entry = matchCommand(input.tool_input?.command, loadCommands());
  if (!entry || !riskAtLeast(entry.risk, floor)) return;
  emit({ hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "ask", permissionDecisionReason: `🦜 ${entryText(entry, r.open.key)}` } });
}

// ---------- PostToolUseFailure: explain failures ----------

function toolFailure(input) {
  if (input.tool_name !== "Bash" || input.is_interrupt) return;
  const r = resolve(input.cwd);
  if (r.s.explain_failures === false || isOff(r, input.session_id)) return;
  const command = String(input.tool_input?.command || "");
  if (!FAILURE_WORTHY.test(command)) return;
  emit({ hookSpecificOutput: { hookEventName: "PostToolUseFailure", additionalContext:
    `Shoga-Speaks: \`${command.slice(0, 200)}\` failed. When you next write to the user, start with one or two plain lines for a ${primaryRole(r)}, in ${r.open.label}: what failed and what it means for them. Then continue as normal.` } });
}

// ---------- resolve (for skills) ----------

function printResolved() {
  const r = resolve(process.cwd());
  const languages = Object.fromEntries(listLanguages().map((id) => {
    const l = loadLanguage(id, []);
    const scripts = [].concat(l.meta.scripts || "native");
    return [id, { scripts, default_script: l.meta.default_script || scripts[0], labels: Object.fromEntries(scripts.map((sc) => [sc, scriptInfo(l, sc).label])) }];
  }));
  let roles = [];
  try { roles = fs.readdirSync(path.join(ROOT, "roles")).filter((f) => f.endsWith(".md")).map((f) => f.slice(0, -3)); } catch {}
  process.stdout.write(JSON.stringify({
    settings: r.s,
    resolved: { language: r.lang.id, script: r.script, github_script: r.ghScript, label: r.mine.label, rtl: r.mine.rtl, cli_shows: r.open.label, roles: r.roles.map((x) => x.id) },
    profile: r.profile,
    notes: r.notes,
    settings_files: { user: r.paths.user, team: r.paths.team, local: r.paths.local, glossary: r.paths.glossary },
    available: { languages, roles },
    plugin_root: ROOT,
  }, null, 2) + "\n");
}

// ---------- main ----------

const HANDLERS = { "session-start": sessionStart, prompt, stop, "pre-tool": preTool, "tool-failure": toolFailure };

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  try {
    const mode = process.argv[2];
    if (mode === "resolve") printResolved();
    else if (HANDLERS[mode]) HANDLERS[mode](readStdin());
  } catch (e) {
    if (process.env.SHOGA_DEBUG) process.stderr.write(String(e?.stack || e));
  }
  process.exit(0);
}

export { resolve };
