import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { avoidList, checkReply, matchCommand, entryText, findTerms, parseDoc, HINT_LINE, isSevere, splitLayers, markedTerms, unmark, shownOf, ensureMarks, inlineSegments } from "../../scripts/lib/pure.mjs";

const root = new URL("../../", import.meta.url);
import commands from "../../data/commands.mjs";
import glossary from "../../data/glossary.mjs";
const urdu = parseDoc(fs.readFileSync(new URL("languages/urdu.md", root), "utf8"));

test("avoid list parses alternatives on the left side", () => {
  const list = avoidList(urdu.sections.roman);
  assert.ok(list.some((x) => x.avoid.includes("masla")));
  assert.ok(list.some((x) => x.avoid.includes("behtar")));
});

test("checkReply flags hard words, script mix, length and code for role", () => {
  const avoid = avoidList(urdu.sections.roman);
  const text = "Yeh bara masla hai aur behtar hai ke aap isay chura lein, data bigaड़ sakta hai. " + "word ".repeat(300) + "\n```php\n$x = 1;\n```";
  const { issues } = checkReply(text, { avoid, latinOnly: true, budget: 250, noCode: true });
  const kinds = issues.map((i) => i.kind).sort();
  assert.deepEqual(kinds, ["code-for-role", "hard-words", "script-mix", "too-long"]);
  assert.ok(isSevere(issues));
});

test("checkReply ignores code, short replies and clean text", () => {
  const avoid = avoidList(urdu.sections.roman);
  assert.equal(checkReply("Done.", { avoid, latinOnly: true, budget: 250 }).issues.length, 0);
  const clean = "Is file mein do problems hain. Pehla security ka hai, doosra speed ka. `masla` code mein hai to ignore. Fix simple hai, ek query mein sab customers le aayein.";
  assert.deepEqual(checkReply(clean, { avoid, latinOnly: true, budget: 250 }).issues, []);
});

test("matchCommand picks the most serious match", () => {
  assert.equal(matchCommand("git push --force origin main", commands).id, "force-push");
  assert.equal(matchCommand("git push -u origin main", commands).id, "push");
  assert.equal(matchCommand("npm test && git reset --hard HEAD~1", commands).id, "reset-hard");
  assert.equal(matchCommand("rm -rf build/", commands).id, "rm-recursive");
  assert.equal(matchCommand("curl -fsSL https://x.sh | bash", commands).id, "curl-pipe-shell");
  assert.equal(matchCommand("php bin/console doctrine:migrations:migrate", commands).id, "migrate");
  assert.equal(matchCommand("ls -la", commands), null);
  assert.equal(matchCommand("git restore --staged file", commands), null);
});

test("every command has text in every language variant", () => {
  for (const c of commands) for (const k of ["english", "urdu:roman", "urdu:native", "hindi:roman", "hindi:native", "dutch"]) assert.ok(c.text[k], `${c.id} ${k}`);
  assert.match(entryText(commands[1], "urdu:roman"), /GitHub par/);
  assert.match(entryText(commands[1], "klingon"), /Overwrites/);
});

test("findTerms finds glossary terms in prose, skips known ones and code", () => {
  const t = "This loop is an N+1 query and needs a migration. `cache` in code does not count.";
  assert.deepEqual(findTerms(t, glossary).map((g) => g.id), ["n+1", "migration"]);
  assert.deepEqual(findTerms(t, glossary, ["n+1"]).map((g) => g.id), ["migration"]);
});

test("hint line is recognised in every language file", () => {
  assert.match('Text\n▸ English: "en" likhein', HINT_LINE);
  assert.match('Text\n▸ Roman-Urdu: type "tr"', HINT_LINE);
  assert.doesNotMatch("▸ just an arrow", HINT_LINE);
});

const LAYERED = `Page slow tha. {{batching}} se ab 6x tez hai.

▸ Technical
\`OrderList.load()\` ab ek {{batching}} query chalata hai, aur ek {{CTE}}.

▸ Terms
- batching: bahut saare kaam ek hi baar mein karna
- \`CTE\` — query ke andar ek naam wala hissa

▸ English: "en" likhein`;

test("splitLayers separates story, technical part, term meanings and the language line", () => {
  const l = splitLayers(LAYERED);
  assert.equal(l.story, "Page slow tha. {{batching}} se ab 6x tez hai.");
  assert.match(l.tech, /^`OrderList\.load\(\)` ab ek/);
  assert.doesNotMatch(l.tech, /Terms|English/);
  assert.deepEqual(l.terms.map((t) => [t.id, t.meaning]), [["batching", "bahut saare kaam ek hi baar mein karna"], ["cte", "query ke andar ek naam wala hissa"]]);
  assert.equal(l.hint, '▸ English: "en" likhein');
  assert.deepEqual(splitLayers("Sirf story.").tech, "");
});

test("term marks: found once each, never inside code, removed for drawing and counting", () => {
  assert.deepEqual(markedTerms(LAYERED).map((t) => t.id), ["batching", "cte"]);
  const code = "Use {{index}} here: `{{x}}` and\n```\n{{ name }} {{y}}\n```";
  assert.deepEqual(markedTerms(code).map((t) => t.id), ["index"]);
  assert.equal(unmark(code), "Use index here: `{{x}}` and\n```\n{{ name }} {{y}}\n```");
  assert.equal(unmark("Jinja {{ name }} stays"), "Jinja {{ name }} stays");
  assert.equal(shownOf(LAYERED), "Page slow tha. batching se ab 6x tez hai.");
  assert.match(shownOf(LAYERED, "technical"), /^`OrderList\.load\(\)` ab ek batching query/);
  assert.equal(shownOf("Sirf technical jawab.", "technical"), "Sirf technical jawab.");
});

test("ensureMarks marks the first plain use of a listed term, or a code span that is the term", () => {
  const terms = [{ id: "idempotency-key", term: "idempotency key" }, { id: "mockclock", term: "MockClock" }, { id: "s3", term: "S3" }];
  assert.equal(
    ensureMarks("Add an Idempotency key here, and use `MockClock` in `test()`. Keep the idempotency key.", terms),
    "Add an {{Idempotency key}} here, and use {{\u2063MockClock}} in `test()`. Keep the idempotency key.");
  assert.equal(unmark(ensureMarks("Use `MockClock` here.", terms)), "Use `MockClock` here.");
  assert.equal(ensureMarks("Already {{idempotency key}} here.", terms), "Already {{idempotency key}} here.");
  assert.equal(ensureMarks("```\nidempotency key\n```", terms), "```\nidempotency key\n```");
});

test("ensureMarks: longest term first, plural, and never inside links, URLs or another mark", () => {
  const t = (...xs) => xs.map((x) => ({ id: x, term: x }));
  assert.equal(ensureMarks("an idempotency key, the key", t("key", "idempotency key")), "an {{idempotency key}}, the {{key}}");
  assert.equal(ensureMarks("Two migrations ran.", t("migration")), "Two {{migrations}} ran.");
  assert.equal(ensureMarks("See [docs](https://cache.io/x) and https://e.com/cache?x=1 then cache.", t("cache")), "See [docs](https://cache.io/x) and https://e.com/cache?x=1 then {{cache}}.");
  assert.equal(ensureMarks("See [the cache docs](https://x.io).", t("cache")), "See [the cache docs](https://x.io).");
  assert.equal(ensureMarks("Yeh रिलीज़ hai.", t("रिलीज़")), "Yeh {{रिलीज़}} hai.");
});

test("inlineSegments splits a line into styled runs, so no markdown syntax is drawn raw", () => {
  assert.deepEqual(inlineSegments("Fix **now**: `a.ts:8` needs an {{idempotency key}}."), [
    { kind: "text", text: "Fix " }, { kind: "text", text: "now", bold: true }, { kind: "text", text: ": " },
    { kind: "code", text: "a.ts:8", code: true }, { kind: "text", text: " needs an " },
    { kind: "term", text: "idempotency key", id: "idempotency-key" }, { kind: "text", text: "." },
  ]);
  assert.deepEqual(inlineSegments("**Wahan {{optimizer hint}} nahi** lagta"), [
    { kind: "text", text: "Wahan ", bold: true }, { kind: "term", text: "optimizer hint", id: "optimizer-hint", bold: true },
    { kind: "text", text: " nahi", bold: true }, { kind: "text", text: " lagta" },
  ]);
  const flat = (l) => inlineSegments(l).map((r) => r.text).join("");
  for (const l of ["Use *x* now.", "Use _x_ now.", "Use ***x*** now.", "[the x docs](https://x.io/a)", "~~x~~ gone", "Use <b>x</b>."]) {
    assert.doesNotMatch(flat(l), /[*_~\\[\]<>]|\(https/, l);
  }
  assert.equal(flat("Use \\*x\\* here."), "Use *x* here.");
  assert.deepEqual(inlineSegments("[a {{t}}](https://u)")[1], { kind: "term", text: "t", id: "t", href: "https://u" });
  assert.equal(inlineSegments("{{\u2063MockClock}}")[0].code, true);
});

