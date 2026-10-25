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

## Python test generation guidelines

Generate every script test case using this function signature:

```python
def test_case_name(browser, base_url):
    # test scripts
```

Use a descriptive `test_` name while retaining the `browser, base_url` parameters. Create a new browser context for every test with `browser.new_context()` and close it in `finally`. Never load saved browser/storage state or reuse a persistent profile; perform required login in the new context.

For locator visibility steps outside final expectation verification, use `is_visible` or `is_hidden` with a five-second timeout budget. Do not validate these intermediate checks with `expect`, `assert`, or equivalent failure checks. Use the Boolean result to control the recorded action. Because Playwright ignores these methods' `timeout` argument, implement the budget with bounded polling as described in the Python reference. Keep assertions for final expected outcomes and keep cleanup unverified.

When a test requires an environment variable, add it to `.env` in the target application root. Preserve existing entries, use an empty value with a setup comment when a required value is unknown, and never invent credentials. Configure the suite to load that file without overriding existing environment variables, document required values in `tests/README.md`, and keep `.env` out of version control.

## List test cases

ONLY List the test markdown files in `agent-tests` folder and python tests in `tests` folder in two different lists. So the user can select a specific test case to run.
To find the right test cases, refer to `Test case naming convention`
DON'T look for cases from any other folders

### Test case naming convention
- The naming convention of test case markdown file in `agent-tests/` folder is `^[T|t][E|e][S|s][T|t](.)*\.md$`
- The naming convention of script test case in `tests/` folder is `^[T|t][E|e][S|s][T|t]_(.)*\.py$`

### Show the list of found test cases

Present a working multiple-selection checklist, not just Markdown `[ ]` text or separate follow-up links. When the available `visualize` skill supports inline interactive controls and follow-up messages, read it and create the checklist using that workflow. Do not use a single-choice question tool as a substitute for multiple selection.

- Keep Markdown cases (`agent-tests/`) and Python cases (`tests/`) in two separately labeled lists within the same selector. Show an explicit empty state when a list has no matches.
- Give every case an initially unchecked native checkbox, its filename, and a concise scenario summary derived from its contents. Use the project-relative path as its stable identifier so duplicate filenames remain distinguishable. Sort paths within each list.
- List root-level cases directly. Nest subfolder cases under selectable folder groups, preserving the relative folder hierarchy in both lists.
- Selecting a group selects every descendant case; clearing it clears every descendant case. Reflect partial selection with an indeterminate group checkbox. Deduplicate selected paths when groups overlap.
- Add `Run all test cases` and `Run selected test cases` buttons after the lists. Disable the selected-run button when nothing is selected and the all-run button when no cases exist.
- Submit a follow-up message only when the user clicks a run button. With the inline visualization host, use `window.openai.sendFollowUpMessage({ prompt, title })`. Include the target application root and exact project-relative case paths, separated into Markdown and Python cases, in the prompt. The all-run button submits every listed path; the selected-run button submits only checked case paths after expanding groups. Do not rely on widget state alone to communicate the selection.
- Listing cases does not run them. Wait for the submitted run request, then execute only its selected cases. Selecting a folder means running all cases under that folder. Run selected Python scripts as regression tests rather than treating them as Markdown source definitions.

If an interactive checklist or follow-up submission is unavailable, say so briefly and provide two numbered, grouped lists with stable case IDs. Ask the user to reply with multiple IDs, folder names, or `all`. Treat this as a text-selection fallback; do not claim static Markdown checkboxes can submit selections.


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
- Copy [tests/__init__.py](tests/__init__.py) from this skill's directory to `<project-root>/tests/__init__.py`. Preserve an existing project file, merging the required initialization code when needed rather than overwriting it.
- Copy [tests/requirements.txt](tests/requirements.txt) from this skill's directory to `<project-root>/tests/requirements.txt`. If the project file already exists, merge missing dependencies while preserving compatible existing version constraints. Resolve source paths relative to this `SKILL.md`, and destination paths relative to the target application root.
- Create `.env` in the target project root if missing; preserve all existing entries. Add required environment variable names, using empty values and setup comments for unknown values. Keep `.env` out of version control and load it without overriding existing environment variables.
- Install the dependencies defined in the project's `tests/requirements.txt` during initialization. Use the project's managed Python environment, or create a dedicated `.venv-ui` with `python3 -m venv .venv-ui`. From the project root, run `<environment-python> -m pip install -r tests/requirements.txt` (for example, `.venv-ui/bin/python -m pip install -r tests/requirements.txt`). Document the environment and exact command in `tests/README.md`. If installation fails or is blocked, report the reason and do not mark initialization complete.
- Check if the required folder `reports/` is existing in project root, if not, create it and then create a `README.md` with content of:
  ```markdown
  This folder contains the report files that is generated automatically.
  ```
- Ensure `outputs/` exists in the project root, creating it if missing and then create a `.keep` with empty content
- Check if the required config file `config.json` is existing in the project root, if not, copy `config.json.example` to project root and change the name to be `config.json`

- For web projects, prepare the Python regression suite, dependency environment, and run instructions described in the reference. Save Python regression scripts in `tests/` and extend its README with setup and run instructions. Reuse existing Python Playwright infrastructure within `tests/` when available; subfolders are allowed. Keep Markdown source cases in `agent-tests/`.

## Run tests

### Sign in when required

When running an agent test case, handle required sign-in before continuing with steps that depend on authentication:

- If the application accepts a username and password, load `.env` from the target application project root and check for non-empty `UI_TEST_USERNAME` and `UI_TEST_PASSWORD` values. If both are configured, try signing in with them and verify the authenticated UI before continuing. Keep credential values out of messages, recordings, reports, and generated source code; use environment-variable references in generated tests.
- If `.env` is missing, either credential is missing or empty, sign-in uses another method, or the configured credentials do not complete sign-in (including a required MFA step), ask the human to complete sign-in. Wait for their explicit confirmation that they have signed in, then verify the authenticated UI before resuming the case. Do not continue dependent steps while waiting.

### Execution

1. Choose one filesystem-safe timestamp for the run before executing tests. Reserve `reports/ui-test-report-<timestamp>.md` and create `outputs/ui-test-<timestamp>/` using exactly the same timestamp. If either path exists, choose a new timestamp for both; never overwrite an earlier run. Find every regular test case file recursively according to `Test case naming convention` under `agent-tests/` and sort the project-relative paths. Each file is one test. If there are no test files, write a report with zero totals and explain that no tests were found.
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
