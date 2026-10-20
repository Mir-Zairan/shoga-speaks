// Hard cases for the classic hook script, run as a black box, from an adversarial test pass.
import { test, beforeEach } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";

const SCRIPT = new URL("../../scripts/shoga.mjs", import.meta.url).pathname;
let home, shoga;
function raw(mode, input, env = {}, rawInput) {
  return spawnSync(process.execPath, [SCRIPT, mode], {
    input: rawInput ?? JSON.stringify({ session_id: "s1", cwd: home, ...input }),
    env: { ...process.env, HOME: home, USERPROFILE: home, SHOGA_HOME: shoga, CLAUDE_PROJECT_DIR: home, CLAUDE_PLUGIN_ROOT: "", CLAUDE_CODE_REMOTE: "", GH_CONFIG_DIR: "", GIT_CONFIG_NOSYSTEM: "1", ...env },
    encoding: "utf8",
  });
}
function run(mode, input, env, rawInput) {
  const r = raw(mode, input, env, rawInput);
  assert.equal(r.status, 0, r.stderr);
  return r.stdout ? JSON.parse(r.stdout) : null;
}
const settings = (s, file = "shoga-speaks.json") => { fs.mkdirSync(path.join(home, ".claude"), { recursive: true }); fs.writeFileSync(path.join(home, ".claude", file), typeof s === "string" ? s : JSON.stringify(s)); };
const ctxOf = (o) => o?.hookSpecificOutput?.additionalContext ?? "";
const mod = () => { fs.mkdirSync(path.join(shoga, "state"), { recursive: true }); fs.writeFileSync(path.join(shoga, "state", "s1.mod"), "1"); };
const URDU = { language: "urdu", script: "roman", github_script: "native", roles: ["qa", "dev"] };
beforeEach(() => { home = fs.mkdtempSync(path.join(os.tmpdir(), "shoga-edge-")); shoga = path.join(home, ".claude", "shoga-speaks"); });

// ---------- session start: size ----------
test("context size: every role, bilingual, native GitHub script and a 3000-char glossary stays under 14,000 chars", () => {
  settings({ ...URDU, roles: ["dev", "qa", "devops", "po", "pm", "support"] });
  fs.mkdirSync(path.join(home, ".claude", "shoga-speaks"), { recursive: true });
  fs.writeFileSync(path.join(home, ".claude", "shoga-speaks", "glossary.md"), ("- Term: a project word that means something here.\n").repeat(70));
  const ctx = ctxOf(run("session-start", { source: "startup" }));
  // Measured as with an 80-char install path, wherever the tests run.
  const root = path.resolve(path.dirname(SCRIPT), "..");
  const size = ctx.length - (ctx.split(root).length - 1) * (root.length - 80);
  assert.ok(size < 14000, `context is ${size} chars`);
});

test("context size for two roles does not depend on where the plugin is installed (the 10,000 cap of hooks.test.mjs)", () => {
  settings(URDU);
  const ctx = ctxOf(run("session-start", { source: "startup" }));
  const root = path.resolve(path.dirname(SCRIPT), "..");
  const base = ctx.length - (ctx.split(root).length - 1) * root.length;
  for (const p of ["/home/runner/work/shoga-speaks/shoga-speaks", "/home/someone/.claude/plugins/cache/shoga-speaks/shoga-speaks/0.3.3"]) {
    assert.ok(base + p.length < 10000, `with the plugin at ${p} the context is ${base + p.length} chars`);
  }
});

test("glossary over 3000 chars is cut with a pointer to the file", () => {
  settings(URDU);
  fs.mkdirSync(path.join(home, ".claude", "shoga-speaks"), { recursive: true });
  fs.writeFileSync(path.join(home, ".claude", "shoga-speaks", "glossary.md"), "x".repeat(5000));
  const ctx = ctxOf(run("session-start", { source: "startup" }));
  assert.match(ctx, /truncated, full file/);
});

// ---------- identity ----------
const gh = (yml) => { fs.mkdirSync(path.join(home, ".config", "gh"), { recursive: true }); fs.writeFileSync(path.join(home, ".config", "gh", "hosts.yml"), yml); };
const who = () => (ctxOf(run("session-start", { source: "startup" })).match(/- The user: (.*?)\. Code by/) || [])[1] || "";
test("identity: no git repo and no gh config gives no identity line", () => {
  settings(URDU);
  assert.doesNotMatch(ctxOf(run("session-start", { source: "startup" })), /The user:/);
});
test("identity: git missing from PATH does not break session start", () => {
  settings(URDU);
  const out = run("session-start", { source: "startup" }, { PATH: "/nonexistent" });
  assert.match(ctxOf(out), /shoga-speaks/);
});
for (const [name, yml, login] of [
  ["classic", "github.com:\n    oauth_token: gho_SECRET1\n    git_protocol: ssh\n    user: alice\n", "alice"],
  ["multi-account", "github.com:\n    users:\n        alice:\n            oauth_token: gho_SECRET2\n        bob:\n            oauth_token: gho_SECRET3\n    git_protocol: https\n    user: alice\n", "alice"],
  ["user first", "github.com:\n    user: alice\n    oauth_token: gho_SECRET4\n", "alice"],
  ["GHE then github.com", "github.example.com:\n    user: corp-alice\n    oauth_token: gho_SECRET5\ngithub.com:\n    user: alice\n    oauth_token: gho_SECRET6\n", "alice"],
  ["GHE only", "github.example.com:\n    user: corp-alice\n    oauth_token: gho_SECRET7\n", "corp-alice"],
  ["CRLF", "github.com:\r\n    oauth_token: gho_SECRET8\r\n    user: alice\r\n", "alice"],
  ["quoted login", "github.com:\n    user: \"alice\"\n    oauth_token: gho_SECRET9\n", "alice"],
  ["empty user, token below", "github.com:\n    user:\n    oauth_token: gho_SECRETA\n", ""],
  ["flow style", "github.com: {oauth_token: gho_SECRETB, user: alice}\n", ""],
  ["tabs", "github.com:\n\toauth_token: gho_SECRETC\n\tuser: alice\n", "alice"],
  ["user named like a token key", "github.com:\n    users:\n        user:\n            oauth_token: gho_SECRETD\n    user: user\n", "user"],
]) {
  test(`identity: hosts.yml ${name} → login "${login}", no token`, () => {
    settings(URDU);
    gh(yml);
    const out = JSON.stringify(run("session-start", { source: "startup" }));
    assert.doesNotMatch(out, /gho_SECRET/);
    const w = who();
    assert.equal((w.match(/GitHub (\S+)/) || [])[1] || "", login, `identity was "${w}"`);
  });
}
test("identity: odd git name and email (unicode, quotes, angle brackets, markdown)", () => {
  settings(URDU);
  spawnSync("git", ["init", "-q"], { cwd: home });
  spawnSync("git", ["config", "user.name", "Zaïran \"Z\" Mír <bot> **x**"], { cwd: home });
  spawnSync("git", ["config", "user.email", "z+tag@ex.co"], { cwd: home });
  assert.equal(who(), "Zaïran \"Z\" Mír <bot> **x** <z+tag@ex.co>");
});
test("identity: GH_CONFIG_DIR is honoured", () => {
  settings(URDU);
  const dir = path.join(home, "ghx"); fs.mkdirSync(dir); fs.writeFileSync(path.join(dir, "hosts.yml"), "github.com:\n    user: carol\n");
  const ctx = ctxOf(run("session-start", { source: "startup" }, { GH_CONFIG_DIR: dir }));
  assert.match(ctx, /GitHub carol/);
});

// ---------- web ----------
for (const lead of ["story", "technical", "technical-only"]) for (const hints of ["on", "off"]) {
  test(`web: CLAUDE_CODE_REMOTE=true, lead ${lead}, term hints ${hints} → plain layout`, () => {
    settings({ ...URDU, layers: lead, term_hints: hints });
    mod();
    const c = ctxOf(run("prompt", { prompt: "next" }, { CLAUDE_CODE_REMOTE: "true" }));
    const want = { story: "story only", technical: "technical, story on request", "technical-only": "technical only" }[lead];
    assert.match(c, new RegExp(`Layout: ${want}${hints === "on" ? ", term hints on" : ""}\\.`));
    run("prompt", { prompt: "shoga web on" });
    assert.match(ctxOf(run("prompt", { prompt: "next" })), new RegExp(`Layout: ${want}`));
    run("prompt", { prompt: "shoga web off" });
    const folded = { story: "story \\+ technical folded", technical: "technical \\+ story folded", "technical-only": "technical only" }[lead];
    assert.match(ctxOf(run("prompt", { prompt: "next" })), new RegExp(`Layout: ${folded}`));
  });
}
test("web: the session-start rules on the web keep the layout the reminder names", () => {
  settings(URDU);
  const ctx = ctxOf(run("session-start", { source: "startup" }, { CLAUDE_CODE_REMOTE: "true" }));
  assert.match(ctx, /`story only`/);
});
test("web: the mod state says web mode, so the mod does not swallow \"tech\" / \"en\" typed in a Remote Control session", () => {
  settings(URDU);
  mod();
  run("prompt", { prompt: "shoga web on" });
  run("session-start", { source: "clear" });
  // The mod reads this flag from the session state (hooks/shoga-mod.tsx, settings()).
  const st = JSON.parse(fs.readFileSync(path.join(shoga, "state", "s1.json"), "utf8"));
  assert.equal(st.web, true);
  run("prompt", { prompt: "shoga web off" });
  assert.equal(JSON.parse(fs.readFileSync(path.join(shoga, "state", "s1.json"), "utf8")).web, false);
});

// ---------- shortcuts ----------
for (const p of ["huh", "HUH?", "Huh", "??", "shoga ??", " huh ", "huh??"]) {
  test(`shortcut "${p}" asks for a simpler re-explanation`, () => {
    settings(URDU);
    assert.match(ctxOf(run("prompt", { prompt: p })), /did not understand/);
  });
}
test("huh lowers the level only to -2 and stays there", () => {
  settings(URDU);
  for (let i = 0; i < 5; i++) run("prompt", { prompt: "huh" });
  assert.equal(JSON.parse(fs.readFileSync(path.join(shoga, "profile.json"), "utf8")).level, -2);
});
for (const k of ["en", "tr"]) {
  test(`"${k}" for an English (not bilingual) user is answered, not sent to Claude as a bare prompt`, () => {
    settings({ language: "english" });
    const out = run("prompt", { prompt: k });
    assert.ok(out?.decision === "block" || /typed "/.test(ctxOf(out)), `got: ${ctxOf(out).slice(0, 120)}`);
  });
}
test("cli_open english: the hint offers the user's language with tr, and tr repeats in it", () => {
  settings({ ...URDU, cli_open: "english" });
  const ctx = ctxOf(run("session-start", { source: "startup" }));
  assert.match(ctx, /▸ Roman-Urdu: type "tr"/);
  assert.match(ctxOf(run("prompt", { prompt: "tr" })), /Repeat your previous explanation in Roman-Urdu/);
  assert.match(ctxOf(run("prompt", { prompt: "en" })), /Repeat your previous explanation in English/);
});
test("github_open translated: GitHub comments open in the user's language", () => {
  settings({ ...URDU, github_open: "translated" });
  assert.match(ctxOf(run("session-start", { source: "startup" })), /Open language: اردو\. Collapsed: English/);
});

// ---------- settings ----------
test("invalid settings JSON: a note, defaults used, no crash", () => {
  settings("{ language: urdu, ");
  const out = run("session-start", { source: "startup" });
  assert.match(out.systemMessage, /invalid JSON/);
});
test("unknown language and role: notes, English and dev used", () => {
  settings({ language: "klingon", roles: ["wizard"] });
  const out = run("session-start", { source: "startup" });
  assert.match(out.systemMessage, /language "klingon" not found/);
  assert.match(out.systemMessage, /role "wizard" not found/);
  assert.match(ctxOf(out), /Primary role: Developer|Primary role: dev/i);
});
test("path tricks in language and role names stay inside the plugin", () => {
  settings({ language: "../../../../etc/passwd", roles: ["../core/rules"] });
  const out = run("session-start", { source: "startup" });
  assert.doesNotMatch(JSON.stringify(out), /root:x:0/);
});
test("legacy glossary_hover off turns term hints off in the reminder too", () => {
  settings({ ...URDU, glossary_hover: "off" });
  mod();
  assert.match(ctxOf(run("prompt", { prompt: "next" })), /Layout: story \+ technical folded\./);
});
test("a malformed stdin does not crash any mode", () => {
  for (const m of ["session-start", "prompt", "stop", "pre-tool", "tool-failure"]) assert.equal(raw(m, null, {}, "not json{").status, 0);
});
test("roles given as a string, layers given in caps", () => {
  settings({ ...URDU, roles: "po", layers: "Technical" });
  mod();
  const c = ctxOf(run("prompt", { prompt: "next" }));
  assert.match(c, /write for Product Owner/);
  assert.match(c, /Layout: technical \+ story folded/);
});

// ---------- stop ----------
const story = "PR theek hai aur tests pass hain. Fix chhota hai aur safe hai, release kar sakte hain aaj hi.";
const lastIssue = () => (ctxOf(run("prompt", { prompt: "next" })).match(/Your last reply (.*)\. Avoid that\./) || [])[1] || "";
for (const [name, tech, flagged] of [
  ["? inside a code fence", "Query:\n```sql\nSELECT * FROM t WHERE id = ?\n```", false],
  ["? in inline code", "`WHERE id = ?` binding hai, test pass hai.", false],
  ["URL with ?query", "Link https://s3.aws.com/b?X-Amz-Expires=600 expire hota hai.", false],
  ["Urdu ؟ question", "Fix ek line ka hai. Kya main push kar doon؟", true],
  ["quoted question in an error message", "Error tha: \"Is the user logged in? \" jo log mein aaya.", false],
  ["SQL placeholder in prose", "Placeholder id = ? se binding hoti hai.", false],
  ["question mid-line", "Kya main push kar doon? ya pehle review.", true],
  ["question before a bracket", "Push kar doon?(haan ya na)", true],
  ["rephrased offer", "Fix ek line ka hai. Agar chahein to main aur detail de sakta hoon.", true],
  ["English offer", "The fix is one line. Let me know if you want more detail.", true],
]) {
  test(`stop: ${name} in the technical part → ${flagged ? "flagged" : "not flagged"}`, () => {
    settings(URDU);
    run("stop", { last_assistant_message: `${story}\n\n▸ Technical\n${tech}` });
    const issue = lastIssue();
    if (flagged) assert.match(issue, /folded technical part/); else assert.doesNotMatch(issue, /folded technical part/);
  });
}
test("stop: a short reply (<15 words) with a folded question is still flagged", () => {
  settings(URDU);
  run("stop", { last_assistant_message: "Theek hai.\n\n▸ Technical\nPush kar doon?" });
  assert.match(lastIssue(), /folded technical part/);
});
test("stop: terms-missing tolerates case and a plural, flags a different word", () => {
  settings(URDU);
  run("stop", { last_assistant_message: `${story} The Webhook fired. Two migrations ran. We migrate.\n\n▸ Terms\n- webhook: callback\n- migration: db change\n- migrating: moving` });
  const i = lastIssue();
  assert.match(i, /not in the text \(migrating\)/);
});
test("stop: a listed term that only appears inside a URL counts as missing", () => {
  settings(URDU);
  run("stop", { last_assistant_message: `${story} Dekhein https://cache.example.com/x.\n\n▸ Terms\n- cache: data ki copy` });
  assert.match(lastIssue(), /not in the text \(cache\)/);
});
test("stop: the length counts the shown part; hard words count the whole reply", () => {
  settings({ ...URDU, layers: "technical" });
  const long = "Yeh technical line file ka naam aur wajah batati hai, test bhi. ".repeat(30);
  run("stop", { last_assistant_message: `${story} masla\n\n▸ Technical\n${long}` });
  const i = lastIssue();
  assert.match(i, /words, the limit/);
  assert.match(i, /hard words \(masla\)/);
});
test("stop: fix mode blocks once, the retry (stop_hook_active) passes, and terms-missing alone never blocks", () => {
  settings({ ...URDU, quality_guard: "fix" });
  const bad = `${story} Yeh masla behtar hai ریلیز.`;
  assert.equal(run("stop", { last_assistant_message: bad }).decision, "block");
  assert.equal(run("stop", { last_assistant_message: bad, stop_hook_active: true }), null);
  assert.equal(run("stop", { last_assistant_message: `${story}\n\n▸ Terms\n- nothing: x` }), null);
});
test("stop: reads the last assistant text from transcript_path when the message is absent", () => {
  settings(URDU);
  const tp = path.join(home, "t.jsonl");
  fs.writeFileSync(tp, [JSON.stringify({ type: "assistant", message: { role: "assistant", content: [{ type: "text", text: `${story} masla behtar hai.` }] } }), JSON.stringify({ type: "user", message: { role: "user", content: "x" } })].join("\n"));
  run("stop", { transcript_path: tp });
  assert.match(lastIssue(), /hard words/);
});

// ---------- pre-tool ----------
const ask = (cmd, s = URDU) => { settings(s); const o = run("pre-tool", { tool_name: "Bash", tool_input: { command: cmd } }); return o?.hookSpecificOutput?.permissionDecisionReason || ""; };
for (const [cmd, danger] of [
  ["git push --force-with-lease origin main", true],
  ["cd app && git push -f", true],
  ["git push origin +main", true],
  ["git push origin --delete feature", true],
  ["git push origin :feature", true],
  ["rm -rf build", true],
  ["rm -f -r build", true],
  ["rm -v -rf build", true],
  ["/bin/rm -rf build", true],
  ["\\rm -rf build", true],
  ["sudo rm -fr /var/x", true],
  ["find . -name '*.log' -exec rm -rf {} +", true],
  ["git checkout .", true],
  ["git branch -D feature", true],
  ["git stash clear", true],
  ["mysql -e \"DELETE FROM orders\"", true],
  ["echo \"rm -rf /\"", false],
  ["echo 'never run rm -rf / here'", false],
  ["git commit -m \"docs: explain git push --force\"", false],
  ["grep -ri \"drop table\" src/", false],
  ["git log --grep='reset --hard'", false],
  ["npm test", false],
  ["git push origin main", false],
]) {
  test(`pre-tool: ${JSON.stringify(cmd)} → ${danger ? "explained" : "not asked"}`, () => {
    const reason = ask(cmd);
    if (danger) assert.notEqual(reason, "", "no explanation"); else assert.equal(reason, "", `asked with: ${reason}`);
  });
}
test("pre-tool: explanation is in the open language (cli_open english → English)", () => {
  assert.match(ask("git reset --hard", { ...URDU, cli_open: "english" }), /Throws away/);
});
test("tool-failure: a failing 'make' or 'npm run build' is explained, 'grep' is not", () => {
  settings(URDU);
  assert.match(ctxOf(run("tool-failure", { tool_name: "Bash", tool_input: { command: "npm run build" } })), /failed/);
  assert.equal(run("tool-failure", { tool_name: "Bash", tool_input: { command: "grep test file" } }), null);
});
