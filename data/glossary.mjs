// Shared by the hook script and the display mod. Edit freely; keep the shape.
export default [
 {
  "id": "n+1",
  "term": "N+1 query",
  "aliases": [
   "N+1"
  ],
  "meaning": "The code asks the database once per item instead of once for all items, so it gets slow with many items."
 },
 {
  "id": "sql-injection",
  "term": "SQL injection",
  "aliases": [],
  "meaning": "An attacker types database commands into an input and the app runs them."
 },
 {
  "id": "prepared-statement",
  "term": "prepared statement",
  "aliases": [
   "parameterized query"
  ],
  "meaning": "A safe way to send user input to the database, so it is never run as a command."
 },
 {
  "id": "migration",
  "term": "migration",
  "aliases": [
   "migrations"
  ],
  "meaning": "A script that changes the database structure, like adding a column."
 },
 {
  "id": "endpoint",
  "term": "endpoint",
  "aliases": [
   "endpoints"
  ],
  "meaning": "One address of an API that the app can call, like /orders."
 },
 {
  "id": "api",
  "term": "API",
  "aliases": [],
  "meaning": "A way for programs to talk to each other."
 },
 {
  "id": "cache",
  "term": "cache",
  "aliases": [
   "caching",
   "cached"
  ],
  "meaning": "A saved copy of data, kept so it loads faster next time."
 },
 {
  "id": "race-condition",
  "term": "race condition",
  "aliases": [],
  "meaning": "Two things happen at the same time and the result depends on which finishes first."
 },
 {
  "id": "deadlock",
  "term": "deadlock",
  "aliases": [],
  "meaning": "Two processes wait for each other forever, so both get stuck."
 },
 {
  "id": "null",
  "term": "null",
  "aliases": [
   "NULL"
  ],
  "meaning": "An empty value: nothing is there."
 },
 {
  "id": "regression",
  "term": "regression",
  "aliases": [
   "regressions"
  ],
  "meaning": "Something that used to work is now broken."
 },
 {
  "id": "refactor",
  "term": "refactor",
  "aliases": [
   "refactoring",
   "refactored"
  ],
  "meaning": "Cleaning up code without changing what it does."
 },
 {
  "id": "merge-conflict",
  "term": "merge conflict",
  "aliases": [
   "conflict"
  ],
  "meaning": "Two people changed the same lines and git cannot combine them by itself."
 },
 {
  "id": "rebase",
  "term": "rebase",
  "aliases": [
   "rebasing"
  ],
  "meaning": "Moving your commits on top of the latest version of a branch."
 },
 {
  "id": "pull-request",
  "term": "pull request",
  "aliases": [
   "PR"
  ],
  "meaning": "A request to add your changes to the main code, where others can review them."
 },
 {
  "id": "ci",
  "term": "CI",
  "aliases": [
   "continuous integration"
  ],
  "meaning": "Automatic checks (tests, build) that run on every change."
 },
 {
  "id": "pipeline",
  "term": "pipeline",
  "aliases": [],
  "meaning": "The list of automatic steps that test and ship the code."
 },
 {
  "id": "deploy",
  "term": "deploy",
  "aliases": [
   "deployment",
   "deployed"
  ],
  "meaning": "Putting a new version of the app on a server so users get it."
 },
 {
  "id": "rollback",
  "term": "rollback",
  "aliases": [
   "roll back"
  ],
  "meaning": "Going back to the previous version after a problem."
 },
 {
  "id": "staging",
  "term": "staging",
  "aliases": [],
  "meaning": "A test copy of the live system, used to check changes before release."
 },
 {
  "id": "production",
  "term": "production",
  "aliases": [
   "prod"
  ],
  "meaning": "The live system that real customers use."
 },
 {
  "id": "env-var",
  "term": "environment variable",
  "aliases": [
   "env var",
   "env vars"
  ],
  "meaning": "A setting given to the app from outside the code, like a password or URL."
 },
 {
  "id": "dependency",
  "term": "dependency",
  "aliases": [
   "dependencies"
  ],
  "meaning": "Outside code (a package) that the project needs to work."
 },
 {
  "id": "unit-test",
  "term": "unit test",
  "aliases": [
   "unit tests"
  ],
  "meaning": "A small automatic test of one piece of code."
 },
 {
  "id": "integration-test",
  "term": "integration test",
  "aliases": [
   "integration tests"
  ],
  "meaning": "An automatic test that checks several parts working together."
 },
 {
  "id": "edge-case",
  "term": "edge case",
  "aliases": [
   "edge cases"
  ],
  "meaning": "An unusual input or situation at the limits, like an empty list."
 },
 {
  "id": "mock",
  "term": "mock",
  "aliases": [
   "mocks",
   "mocked"
  ],
  "meaning": "A fake version of something, used in tests."
 },
 {
  "id": "payload",
  "term": "payload",
  "aliases": [],
  "meaning": "The data sent in a request or message."
 },
 {
  "id": "schema",
  "term": "schema",
  "aliases": [],
  "meaning": "The planned shape of data: which fields exist and their types."
 },
 {
  "id": "db-index",
  "term": "index",
  "aliases": [
   "database index"
  ],
  "meaning": "A lookup list that makes database searches fast."
 },
 {
  "id": "transaction",
  "term": "transaction",
  "aliases": [
   "transactions"
  ],
  "meaning": "A group of database changes that all happen, or none do."
 },
 {
  "id": "timeout",
  "term": "timeout",
  "aliases": [
   "timed out",
   "time out"
  ],
  "meaning": "Waiting was stopped because it took too long."
 },
 {
  "id": "rate-limit",
  "term": "rate limit",
  "aliases": [
   "rate limiting",
   "throttling"
  ],
  "meaning": "A cap on how many requests are allowed in a time window."
 },
 {
  "id": "webhook",
  "term": "webhook",
  "aliases": [
   "webhooks"
  ],
  "meaning": "A message one system sends to another automatically when something happens."
 },
 {
  "id": "idempotent",
  "term": "idempotent",
  "aliases": [],
  "meaning": "Doing it twice has the same result as doing it once."
 },
 {
  "id": "async",
  "term": "async",
  "aliases": [
   "asynchronous"
  ],
  "meaning": "Work that runs in the background while other things continue."
 },
 {
  "id": "latency",
  "term": "latency",
  "aliases": [],
  "meaning": "The delay before a response comes back."
 },
 {
  "id": "memory-leak",
  "term": "memory leak",
  "aliases": [],
  "meaning": "The app keeps using more memory and never frees it, until it slows down or crashes."
 },
 {
  "id": "feature-flag",
  "term": "feature flag",
  "aliases": [
   "feature flags",
   "feature toggle"
  ],
  "meaning": "A switch that turns a feature on or off without a new release."
 },
 {
  "id": "hotfix",
  "term": "hotfix",
  "aliases": [],
  "meaning": "A quick fix released outside the normal schedule."
 },
 {
  "id": "tech-debt",
  "term": "technical debt",
  "aliases": [
   "tech debt"
  ],
  "meaning": "Shortcuts in code that make future changes slower."
 },
 {
  "id": "orm",
  "term": "ORM",
  "aliases": [],
  "meaning": "A library that lets code use the database through objects instead of SQL."
 },
 {
  "id": "stack-trace",
  "term": "stack trace",
  "aliases": [
   "traceback"
  ],
  "meaning": "The list of code steps that led to an error."
 },
 {
  "id": "linter",
  "term": "linter",
  "aliases": [
   "lint"
  ],
  "meaning": "A tool that checks code for mistakes and style problems."
 }
]