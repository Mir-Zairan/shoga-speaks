#!/usr/bin/env node
// Shoga-Speaks hook entry point.
//   node shoga.mjs session-start   -> loads rules, language, roles, glossary into context
//   node shoga.mjs prompt          -> short per-prompt reminder + "en"/"tr"/"shoga ..." shortcuts
// No dependencies. Any failure exits 0 silently so Claude Code is never blocked.

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = process.env.CLAUDE_PLUGIN_ROOT || path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const LENGTH_GUIDE = {
  short: "short: 3-5 lines per point, the whole answer fits on one screen",
  medium: "medium: up to about 15 lines, still structured",
  detailed: "detailed: full explanation allowed, but still point first and structured",
};
const GLOSSARY_LIMIT = 3000;

// ---------- small helpers ----------

const readText = (p) => { try { return fs.readFileSync(p, "utf8"); } catch { return null; } };
const readJson = (p) => {
  const t = readText(p);
  if (t == null) return null;
  try { return JSON.parse(t); } catch { return { __invalid: p }; }
};

function deepMerge(base, over) {
  if (!over || typeof over !== "object" || Array.isArray(over)) return base;
  const out = { ...base };
  for (const [k, v] of Object.entries(over)) {
    out[k] = v && typeof v === "object" && !Array.isArray(v) && base[k] && typeof base[k] === "object"
      ? deepMerge(base[k], v)
      : v;
  }
  return out;
}

// Minimal frontmatter + "## section" parser for the language/role markdown files.
function parseDoc(text) {
  const meta = {};
  let body = text;
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (m) {
    body = text.slice(m[0].length);
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

function readStdin() {
  try { return JSON.parse(fs.readFileSync(0, "utf8") || "{}"); } catch { return {}; }
}

function emit(obj) { process.stdout.write(JSON.stringify(obj)); }

// ---------- settings ----------

function settingsPaths(cwd) {
  const home = os.homedir();
  const project = process.env.CLAUDE_PROJECT_DIR || cwd || process.cwd();
  return {
    user: path.join(home, ".claude", "shoga-speaks.json"),
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

function sessionStateFile(sessionId) {
  const dir = process.env.CLAUDE_PLUGIN_DATA || path.join(os.tmpdir(), "shoga-speaks");
  return path.join(dir, "sessions", `${String(sessionId || "default").replace(/[^\w.-]/g, "_")}.json`);
}
const sessionState = (id) => readJson(sessionStateFile(id)) || {};
function setSessionState(id, state) {
  const f = sessionStateFile(id);
  try { fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, JSON.stringify(state)); } catch {}
}

// ---------- language / role resolution ----------

function loadLanguage(name, notes) {
  const safe = String(name || "english").toLowerCase().replace(/[^a-z0-9_-]/g, "");
  let text = readText(path.join(ROOT, "languages", `${safe}.md`));
  if (!text || safe.startsWith("_")) {
    const available = listLanguages().join(", ");
    notes.push(`language "${name}" not found, using English (available: ${available})`);
    text = readText(path.join(ROOT, "languages", "english.md"));
    return { id: "english", ...parseDoc(text) };
  }
  return { id: safe, ...parseDoc(text) };
}

function listLanguages() {
  try { return fs.readdirSync(path.join(ROOT, "languages")).filter((f) => f.endsWith(".md") && !f.startsWith("_")).map((f) => f.slice(0, -3)); }
  catch { return ["english"]; }
}

function pickScript(lang, wanted, notes, what) {
  const scripts = Array.isArray(lang.meta.scripts) ? lang.meta.scripts : [lang.meta.scripts || "native"];
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
    moreDetail: m[`more_detail.${script}`] || "Want more detail?",
    hint: m[`hint.${script}`] || '▸ {other}: type "{key}"',
  };
}

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

// Everything the prompts need, resolved once.
function resolve(cwd) {
  const { settings: s, notes, found, paths } = loadSettings(cwd);
  const lang = loadLanguage(s.language, notes);
  const script = pickScript(lang, s.script, notes, "script");
  const ghScript = pickScript(lang, !s.github_script || s.github_script === "default" ? script : s.github_script, notes, "github_script");
  const roles = loadRoles(s.roles, notes);
  const bilingual = lang.id !== "english";
  const english = scriptInfo(loadLanguage("english", []), "native");
  const mine = scriptInfo(lang, script);
  const mineGh = scriptInfo(lang, ghScript);
  const cliEnglish = !bilingual || s.cli_open === "english";
  const open = cliEnglish ? english : mine;
  const other = cliEnglish ? mine : english;
  const otherKey = cliEnglish ? "tr" : "en";
  const hint = bilingual ? open.hint.replace("{other}", other.label).replace("{key}", otherKey) : null;
  return { s, notes, found, paths, lang, script, ghScript, roles, bilingual, english, mine, mineGh, open, other, otherKey, hint, cliEnglish };
}

const roleNames = (r) => r.roles.map((x) => x.meta.label || x.id).join(" + ");
const primaryRole = (r) => r.roles[0].meta.label || r.roles[0].id;
const extraRoles = (r) => r.roles.slice(1).map((x) => x.meta.label || x.id).join(", ");

// ---------- SessionStart ----------

function sessionStart(input) {
  const r = resolve(input.cwd);
  const { s } = r;
  const off = s.enabled === false || sessionState(input.session_id).off;
  if (off) return;

  const parts = [];
  parts.push(`<shoga-speaks>\nThe user has the Shoga-Speaks plugin on. Follow these rules for every reply in this session, including output from other skills, commands and agents. They change how you explain things, never what you do.`);
  parts.push(readText(path.join(ROOT, "core", "rules.md")) || "");

  const langLine = r.cliEnglish
    ? `Write chat replies in simple English${r.bilingual ? ` (the user's own language, ${r.mine.label}, is available on request)` : ""}.`
    : `Write chat replies in ${r.mine.label} (language: ${r.lang.id}, script: ${r.script}${r.mine.rtl ? ", right-to-left" : ""}).`;
  parts.push(`# This user's settings
- ${langLine}
- Keep English technical terms: ${s.keep_english_terms !== false ? "yes" : "no, translate them when a common word exists"}.
- Length: ${LENGTH_GUIDE[s.length] || LENGTH_GUIDE.short}. When you stop early, end with: "${r.open.moreDetail}"
- Primary role: ${primaryRole(r)}. Write the whole answer for this role: what it cares about, what it leaves out, how it ends.${extraRoles(r) ? `
- Other roles: ${extraRoles(r)}. Each gets at most one short line, labelled with the role name. No code blocks for them unless the user asks.` : ""}`);

  if (r.bilingual) {
    parts.push(`# The other language ("collapsed")
The terminal cannot collapse text, so do not write both languages. Write only the open language.
When a reply explains something (not for one-line confirmations), end it with this exact line:
${r.hint}
If the user then types "${r.otherKey}", repeat your previous explanation in ${r.other.label}: same content, same length, no new work and no tool calls.`);
  }

  parts.push(`# ${r.mine.label === r.english.label ? "Language guide" : `Language guide: ${r.mine.label}`}
${[r.lang.sections.common, r.lang.sections[r.script]].filter(Boolean).join("\n\n")}`);
  if (r.cliEnglish && r.bilingual) {
    const en = loadLanguage("english", []);
    parts.push(`# Language guide: English\n${[en.sections.common, en.sections.native].filter(Boolean).join("\n\n")}`);
  }

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
    msg.push(`🦜 Shoga-Speaks: ${r.cliEnglish ? "English" : r.mine.label} · ${roleNames(r)} · ${s.length || "short"}`);
    if (!r.found) msg.push("Run /shoga-speaks:setup to choose your language and roles.");
  }
  if (r.notes.length) msg.push(`Shoga-Speaks: ${r.notes.join("; ")}`);
  if (msg.length) out.systemMessage = msg.join("\n");
  emit(out);
}

// ---------- UserPromptSubmit ----------

function prompt(input) {
  const raw = String(input.prompt || "").trim();
  const cmd = raw.toLowerCase().replace(/\s+/g, " ");
  const state = sessionState(input.session_id);

  if (cmd === "shoga off" || cmd === "shoga on") {
    const off = cmd === "shoga off";
    setSessionState(input.session_id, { ...state, off });
    emit({ decision: "block", reason: off
      ? "🦜 Shoga-Speaks is off for this session. Type \"shoga on\" to turn it back on."
      : "🦜 Shoga-Speaks is on again for this session.", suppressOriginalPrompt: true });
    return;
  }

  const r = resolve(input.cwd);
  const { s } = r;

  if (cmd === "shoga status" || cmd === "shoga") {
    const lines = [
      `🦜 Shoga-Speaks is ${s.enabled === false || state.off ? "OFF" : "ON"}`,
      `Language: ${r.lang.id} (${r.mine.label}, script: ${r.script}) · CLI shows: ${r.cliEnglish ? "English" : r.mine.label}`,
      `GitHub: ${s.github_open === "translated" ? r.mineGh.label : "English"} open, ${s.github_open === "translated" ? "English" : r.mineGh.label} collapsed`,
      `Roles: ${roleNames(r)} · Length: ${s.length || "short"}`,
      r.found ? `Settings: ${[r.paths.team, r.paths.user, r.paths.local].filter((f) => fs.existsSync(f)).join(", ")}` : "Settings: plugin defaults (run /shoga-speaks:setup)",
      ...r.notes.map((n) => `Note: ${n}`),
      `Shortcuts: "${r.bilingual ? r.otherKey : "en"}" other language · "shoga off" / "shoga on" · "shoga status"`,
    ];
    emit({ decision: "block", reason: lines.join("\n"), suppressOriginalPrompt: true });
    return;
  }

  if (s.enabled === false || state.off) return;

  let ctx;
  if (r.bilingual && (cmd === "en" || cmd === "tr")) {
    const target = cmd === "en" ? r.english.label : r.mine.label;
    ctx = `Shoga-Speaks: the user typed "${raw}". Repeat your previous explanation in ${target}. Same content and length, simple words, no new work, no tool calls, no hint line at the end.`;
  } else {
    const lang = r.cliEnglish ? "simple English" : `${r.mine.label} (${r.lang.id}, ${r.script} script)`;
    ctx = `Shoga-Speaks reminder: reply in ${lang}; write for ${primaryRole(r)}${extraRoles(r) ? ` (${extraRoles(r)}: one line each at most)` : ""}; length ${s.length || "short"}. Point first, one idea per line, simple everyday words. Code, paths, commands and errors stay as-is.${r.hint ? ` If the reply explains something, end with: ${r.hint}` : ""}`;
  }
  emit({ hookSpecificOutput: { hookEventName: "UserPromptSubmit", additionalContext: ctx } });
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
    resolved: { language: r.lang.id, script: r.script, github_script: r.ghScript, label: r.mine.label, rtl: r.mine.rtl, cli_shows: r.cliEnglish ? "English" : r.mine.label, roles: r.roles.map((x) => x.id) },
    notes: r.notes,
    settings_files: { user: r.paths.user, team: r.paths.team, local: r.paths.local, glossary: r.paths.glossary },
    available: { languages, roles },
    plugin_root: ROOT,
  }, null, 2) + "\n");
}

// ---------- main ----------

try {
  const mode = process.argv[2];
  const input = mode === "resolve" ? {} : readStdin();
  if (mode === "session-start") sessionStart(input);
  else if (mode === "prompt") prompt(input);
  else if (mode === "resolve") printResolved();
} catch (e) {
  if (process.env.SHOGA_DEBUG) process.stderr.write(String(e?.stack || e));
}
process.exit(0);
