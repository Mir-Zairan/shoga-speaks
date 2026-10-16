import { test, beforeEach } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";

const SCRIPT = new URL("../../scripts/shoga.mjs", import.meta.url).pathname;
let home, shoga;

function run(mode, input) {
  const r = spawnSync(process.execPath, [SCRIPT, mode], {
    input: JSON.stringify({ session_id: "s1", cwd: home, ...input }),
    env: { ...process.env, HOME: home, USERPROFILE: home, SHOGA_HOME: shoga, CLAUDE_PROJECT_DIR: home, CLAUDE_PLUGIN_ROOT: "" },
    encoding: "utf8",
  });
  assert.equal(r.status, 0, r.stderr);
  return r.stdout ? JSON.parse(r.stdout) : null;
}
const settings = (s) => { fs.mkdirSync(path.join(home, ".claude"), { recursive: true }); fs.writeFileSync(path.join(home, ".claude", "shoga-speaks.json"), JSON.stringify(s)); };
const URDU_QA = { language: "urdu", script: "roman", github_script: "native", roles: ["qa", "dev"] };

beforeEach(() => {
  home = fs.mkdtempSync(path.join(os.tmpdir(), "shoga-home-"));
  shoga = path.join(home, ".claude", "shoga-speaks");
});

test("session start: context, status line and state for the mod", () => {
  settings(URDU_QA);
  const out = run("session-start", { source: "startup" });
  assert.match(out.systemMessage, /Roman-Urdu · QA \/ Tester \+ Developer/);
  const ctx = out.hookSpecificOutput.additionalContext;
  assert.ok(ctx.length < 10000, `context is ${ctx.length} chars`);
  assert.match(ctx, /Primary role: QA \/ Tester/);
  assert.match(ctx, /▸ English: "en" likhein/);
  const st = JSON.parse(fs.readFileSync(path.join(shoga, "state", "latest.json"), "utf8"));
  assert.equal(st.otherLabel, "English");
  assert.equal(st.langKey, "urdu:roman");
  assert.equal(st.glossaryHover, true);
});

test("?? lowers the level and asks for a simpler re-explanation", () => {
  settings(URDU_QA);
  const out = run("prompt", { prompt: "??" });
  assert.match(out.hookSpecificOutput.additionalContext, /did not understand/);
  assert.equal(JSON.parse(fs.readFileSync(path.join(shoga, "profile.json"), "utf8")).level, -1);
  const ctx = run("session-start", { source: "clear" }).hookSpecificOutput.additionalContext;
  assert.match(ctx, /Explain every technical term/);
});

test("shoga know / forget / simpler / deeper work without a Claude turn", () => {
  let out = run("prompt", { prompt: "shoga know N+1, Migration" });
  assert.equal(out.decision, "block");
  assert.match(out.reason, /migration, n\+1/);
  out = run("prompt", { prompt: "shoga forget n+1" });
  assert.match(out.reason, /\(1\): migration/);
  assert.match(run("prompt", { prompt: "shoga deeper" }).reason, /Level is now 1/);
  assert.match(run("session-start", { source: "startup" }).hookSpecificOutput.additionalContext, /already knows.*migration/);
});

test("stop: remind mode stores slips and the next prompt mentions them once", () => {
  settings(URDU_QA);
  const reply = "Yeh bara masla hai, aur behtar hai ke pehle test karein. " + "Phir sab theek ho jayega aur release ho sakti hai. ".repeat(3);
  assert.equal(run("stop", { last_assistant_message: reply }), null);
  let ctx = run("prompt", { prompt: "next" }).hookSpecificOutput.additionalContext;
  assert.match(ctx, /Your last reply used hard words \(masla, behtar\)/);
  ctx = run("prompt", { prompt: "next" }).hookSpecificOutput.additionalContext;
  assert.doesNotMatch(ctx, /Your last reply/);
  const prof = JSON.parse(fs.readFileSync(path.join(shoga, "profile.json"), "utf8"));
  assert.deepEqual(prof.stats, { checked: 1, slipped: 1 });
});

test("stop: fix mode blocks a severe slip once, never loops", () => {
  settings({ ...URDU_QA, quality_guard: "fix" });
  const reply = "Is se data chura ya bigaड़ sakta hai. Yeh bara masla hai aur behtar hoga ke abhi fix karein, phir test karein aur release karein.";
  const out = run("stop", { last_assistant_message: reply });
  assert.equal(out.decision, "block");
  assert.match(out.reason, /mixed in characters/);
  assert.equal(run("stop", { last_assistant_message: reply, stop_hook_active: true }), null);
});

test("pre-tool: asks with a plain explanation for dangerous commands only", () => {
  settings(URDU_QA);
  const out = run("pre-tool", { tool_name: "Bash", tool_input: { command: "git push --force origin main" } });
  assert.equal(out.hookSpecificOutput.permissionDecision, "ask");
  assert.match(out.hookSpecificOutput.permissionDecisionReason, /overwrite karega/);
  assert.equal(run("pre-tool", { tool_name: "Bash", tool_input: { command: "git push origin main" } }), null);
  assert.equal(run("pre-tool", { tool_name: "Bash", tool_input: { command: "ls" } }), null);
});

test("pre-tool: stays quiet when the display mod is active or the setting is off", () => {
  settings(URDU_QA);
  fs.mkdirSync(path.join(shoga, "state"), { recursive: true });
  fs.writeFileSync(path.join(shoga, "state", "s1.mod"), "");
  assert.equal(run("pre-tool", { tool_name: "Bash", tool_input: { command: "rm -rf build" } }), null);
  fs.rmSync(path.join(shoga, "state", "s1.mod"));
  settings({ ...URDU_QA, explain_commands: "off" });
  assert.equal(run("pre-tool", { tool_name: "Bash", tool_input: { command: "rm -rf build" } }), null);
});

test("tool-failure: explains failed tests/builds, ignores other failures", () => {
  settings(URDU_QA);
  const out = run("tool-failure", { tool_name: "Bash", tool_input: { command: "npm test" }, error: "Exit code 1" });
  assert.match(out.hookSpecificOutput.additionalContext, /QA \/ Tester, in Roman-Urdu/);
  assert.equal(run("tool-failure", { tool_name: "Bash", tool_input: { command: "grep foo bar.txt" }, error: "Exit code 1" }), null);
});

test("shoga off silences every hook for the session", () => {
  settings(URDU_QA);
  run("prompt", { prompt: "shoga off" });
  assert.equal(run("prompt", { prompt: "hello" }), null);
  assert.equal(run("pre-tool", { tool_name: "Bash", tool_input: { command: "rm -rf /tmp/x" } }), null);
  assert.equal(run("stop", { last_assistant_message: "masla ".repeat(30) }), null);
});
