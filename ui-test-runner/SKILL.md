---
name: ui-test-runner
description: Run Markdown-defined UI tests or record an interactive web task in the built-in browser, then generate Markdown cases and reusable Python Playwright regression tests. Use when asked to validate project UI cases, initialize UI testing, or record user and agent actions for later replay without AI. Manual action capture requires a supported browser recorder; otherwise use guided recording. Create bug tickets in the configured system for failed test runs.
metadata:
  short-description: Run UI tests and save Python Playwright regression tests
---

# UI test runner

Resolve the target application root from the user's project context and repository instructions. For a project-local install at `.agents/skills/ui-test-runner/SKILL.md`, the root is three directories above this file. For a shared/global skill, use the target application checkout, not the skill repository. Resolve `agent-tests/` (Markdown cases), `tests/` (Python scripts), `reports/` (Markdown reports), and `outputs/` (run artifacts) from that root.

For web tests, running a case also means recording its steps and creating or updating a Python Playwright test in the target project. The saved test must run without an AI agent. Read [Python Playwright regression workflow](references/python-playwright.md) before setup or execution. Desktop-only cases still receive normal results; record unsupported Playwright automation in the separate recording.

When generating Python tests, include cleanup actions but do not verify their results. Keep cleanup separate from test expectations; do not generate cleanup assertions or checks that confirm the environment was reset.

## List test cases

List the test markdown files in `agent-tests` folder and python tests in `tests` folder in two different lists.
So the user can select a specific test case to run.

## Generate Markdown test cases

Whenever creating an agent-test Markdown file in `agent-tests/`, read and use [agent-test-template.md](agent-test-template.md) as the starting template. Preserve its `Objective`, `Steps`, `Expect`, and `Cleanup` sections and replace the example guidance with case-specific content. Include the goal, starting route, and prerequisites/test data in `Objective`; ordered actions in `Steps`; success criteria in `Expect`; and environment reset or teardown in `Cleanup`. If no cleanup is needed, state that explicitly. Use environment-variable or fixture references for sensitive inputs. Add supporting links or coverage notes as needed without replacing the template structure.

## Record an interactive task

When asked to record a new task, read [Interactive recording workflow](references/recording.md) and the Python Playwright reference. Open the target web app in a visible built-in browser and maintain one durable session across user actions and requested agent actions. Check whether the browser actually exposes manual action capture; snapshots and agent tool calls alone do not record the user's clicks or typing. Disclose unsupported capture and offer guided recording rather than claiming automatic recording.

Preserve the user's requested input and selection rules in both Markdown steps and Python scripts. Hardcode test data values only when the user explicitly supplies them; values merely observed on the page must not become fixed inputs, option locators, or expected results. For example, record “select the first available option” and implement that rule at replay time, even if the selected option during recording was “black”. See the recording reference for intent capture and the Python reference for replay rules.

Keep the session open until the user explicitly says the whole task is completed. Then create a new `agent-tests/test_<task>.md` using the template workflow above and matching `tests/test_<task>.py` from the complete ordered session, with prerequisites and expected-result assertions. Save incomplete coverage and replay limitations explicitly. Recording creates new source cases; the rule against editing source cases applies when running existing tests. Use the normal report and ticket workflow only for a requested test run, not merely because a recording was finalized.

## Initialize project
- Check if the required folder `agent-tests/` is existing in project root, if not, create it and then create a `README.md` with content of:
  ```markdown
  This folder contains Markdown UI test cases for the agent. Test filenames must start with "test" or "Test" and end with ".md". Cases can be in subfolders. Python regression scripts belong in tests/.
  ```
- Always ensure `tests/` exists in the project root during initialization, creating it if missing. This folder contains Python test scripts, including generated Playwright regression tests. Preserve existing files. If `tests/README.md` is missing, create it with:
  ```markdown
  This folder contains Python test scripts. Test filenames must start with "test_" and end with ".py". Tests can be in subfolders. Markdown UI test cases belong in agent-tests/.
  ```
- Check if the required folder `reports/` is existing in project root, if not, create it and then create a `README.md` with content of:
  ```markdown
  This folder contains the report files that is generated automatically.
  ```
- Ensure `outputs/` exists in the project root, creating it if missing and then create a `.keep` with empty content
- Check if the required config file `config.json` is existing in the project root, if not, copy `config.json.example` to project root and change the name to be `config.json`

- For web projects, prepare the Python regression suite, dependency environment, and run instructions described in the reference. Save Python regression scripts in `tests/` and extend its README with setup and run instructions. Reuse existing Python Playwright infrastructure within `tests/` when available; subfolders are allowed. Keep Markdown source cases in `agent-tests/`.

## Run tests

1. Choose one filesystem-safe timestamp for the run before executing tests. Reserve `reports/ui-test-report-<timestamp>.md` and create `outputs/ui-test-<timestamp>/` using exactly the same timestamp. If either path exists, choose a new timestamp for both; never overwrite an earlier run. Find every regular `[Tt]est*.md` file recursively under `agent-tests/` and sort the project-relative paths. Each file is one test. If there are no test files, write a report with zero totals and explain that no tests were found.
2. Read each complete file. Identify its setup, actions, expected results, and any explicit skip condition. An empty file or one without actionable steps is a failure with its content problem recorded as the actual result.
3. Use the available browser or desktop UI tools to perform the steps in order. For web cases, record each action, observed locator, input reference, expected result, and actual result as you go, following the reference. Observe the UI after state-changing actions. Do not infer success from an action call alone. Reestablish the required starting state between tests when needed.
4. Mark a test `passed` only if every stated expectation is observed. Mark it `failed` for an expectation mismatch, unexpected UI state, or execution error. 
5. In the Markdown report, include expected and actual results for failed tests. The separate step recording retains observations and expectations for every web case.
6. Mark it `skipped` when an explicit skip condition applies or a required app, URL, account, fixture, or permission is unavailable; record the reason. Never count an unrun test as passed.
7. Generate or update each web case's Python test from the recorded steps and original expectations. Retain assertions for application failures; do not change the expected result to make a broken application pass. Save a partial recording and an explicitly skipped Python case when a complete runnable test cannot be produced.
8. Replay generated tests from a fresh context and reset fixture state when authorized and repeatable. Track replay results separately from the initial UI observations. If replay is blocked or unsafe to repeat within the requested scope, label the script unverified and explain why in the separate recording. Do not claim a script is reusable based only on syntax or collection checks.
9. If a test is failed, raise a bug ticket as introduced in `Create a bug ticket`. Do not create a duplicate ticket for the same failure during replay.
10. Close browser contexts or sessions created for the test run when all tests are completed.

Do not edit the source Markdown test definitions while running them. UI actions must stay within the user's requested test scope and existing authorization.

## Run artifacts

Save generated run artifacts under `outputs/ui-test-<timestamp>/`, including step recordings, screenshots, videos, traces, logs, downloads, exported files, and JUnit XML. Use subfolders such as `steps/`, `playwright/`, and `downloads/` to keep cases and artifact types organized. Configure tools to write there, or move temporary output there before linking it. Python regression scripts and their reusable support files stay in `tests/`. Preserve project source files and existing fixtures.

Create this folder even for zero-test runs so the summary link always has a valid target. Replays for the same report use the same run folder, with distinct child directories per invocation to avoid tool cleanup overwriting earlier artifacts. A later standalone regression run gets a new `outputs/ui-test-<timestamp>/` folder.

## Report

- Create `reports/ui-test-report-<timestamp>.md` using the timestamp already chosen for the run and the defined `Report Format`.
- Add an `Outputs` row in the summary table linking to `[ui-test-<timestamp>](../outputs/ui-test-<timestamp>/)`.
- Avoid overwriting an existing report. 
- Include the run time, total discovered tests, totals for passed, failed, and skipped
- Include one detail entry per test with its project-relative file path and final status. The detail entry should follow the template blow,
- For every failure, include `Expect` and `Actual`
- For every skip, include `Reason`. Keep observations specific enough to reproduce or investigate the result.
- When a Python script exists for a case, append `regression test case: [<script filename>](<script test file path>)` to its `Details` cell, including for passed cases. Use a link resolved relative to the report file. Preserve any failure or skip details, separating the regression link with `<br>` when needed. Omit this addition when no script exists; never link a nonexistent file.
- Do not include Python test generation results, replay results, automation status, limitations, step recordings, or regression setup/run instructions in the test report. Retain those details in the separate recordings and suite README.
- Reserve `Outputs` for artifacts produced by the tested application or test case, such as a downloaded file. Use report-relative links into the run output folder for these artifacts. Put the regression script link only in `Details`.


After writing, reread the report. Confirm each discovered test appears exactly once and that `passed + failed + skipped = total`, and that the summary folder link exists and shares the report timestamp. Tell the user the report path, totals, generated suite path, and exact regression command. Keep any user-facing explanation of replay differences outside the test report.

### Report Format

The report format is:

## Summary
| Total | <total number of tests>> |
|---|---|
| 🟢 **Pass** | <total number of passed tests> |
| 🔴 **Failed** | <total number of failed tests> |
| 🟡 **Skipper** | <total number of skipped tests> |
| Outputs | [ui-test-<timestamp>](../outputs/ui-test-<timestamp>/) |

## Results

### <parent folder name>
| Test Case | Status | Details | Outputs | 
|---|---|---|---|
| <test file 1 name> | <status indicator, e.g. 🟢> | <failure or skip details when applicable; regression test case: [script filename](script test file path) when a script exists> | if applicable, the link of generated artefacts by the test, e.g. generated file |
| <test file 2 name> | <status indicator, e.g. 🔴> | <failure or skip details when applicable; regression test case: [script filename](script test file path) when a script exists> | if applicable, the link of generated artefacts by the test, e.g. generated file |

## Create a bug ticket

1. Get the configured bug `ticket_system` from `config.json` file in the project root
2. Get the configuration of the ticket system to get the information required to create a ticket for the bug. For example, if the `ticket_system` is "jira", then get jira configuration from "jira" data entry and create a ticket with configured `type` in the jira project specified with configured `project_key`
3. If there isn't validate ticket system configuration can be found, skip creating bug ticket
