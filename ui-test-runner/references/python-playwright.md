# Python Playwright regression workflow

## Prepare the target project

Inspect existing test infrastructure, dependency management, ignore rules, and application startup instructions. Preserve existing tests and configuration. Use Python, `pytest`, `pytest-playwright`, and Playwright's synchronous API; generate synchronous tests with the required `browser, base_url` signature, adapting existing infrastructure as needed. A JavaScript suite may supply fixtures and selectors but does not replace the requested Python deliverable.

Read Markdown source cases only from `agent-tests/`. Save generated Python tests under `tests/`, preserving existing tests and using subfolders when needed. For example, `agent-tests/accounts/test_login.md` can map to `tests/accounts/test_login.py`.

When no Python UI suite exists, create in the target application:

- `tests/test_*.py`: collected regression tests.
- `tests/conftest.py`: shared setup and cleanup, only when needed.
- `tests/requirements.txt`: required packages and versions validated in that project, unless its dependency manager already records them.
- `tests/README.md`: application startup, installation, required environment variables, test data/reset procedure, full-suite and single-case commands, and artifact locations. Include limitations and any manual prerequisites.
- `outputs/ui-test-<timestamp>/steps/`: per-case recordings from the current run.

Add every required environment variable to the target application root `.env`, preserving existing entries. Use empty values with setup comments for unknown values. Load `.env` without overriding existing environment variables (for example, with `python-dotenv` in `tests/conftest.py`, recording the dependency). Keep `.env` ignored by version control and document how to supply missing values. Ensure the documented command loads `.env` before expanding shell variables such as `UI_TEST_BASE_URL`; alternatively let a fixture read the loaded value.

Keep Python setup and run instructions in `tests/README.md`. Markdown case discovery scans only `agent-tests/`; it does not scan `tests/`. Map each source case to a stable Python module/function, using its project-relative path to avoid collisions between similarly named cases. Include the source path in a docstring or comment. Reuse that mapping on subsequent runs and review edits rather than appending duplicate tests or replacing maintained suites. Persist the mapping in the recordings and run instructions.

Install missing test tools in the project's managed environment or a dedicated `.venv-ui`; install the chosen Playwright browser. Record tested versions in the project's dependency file/lock. Do not upgrade unrelated dependencies. If setup is blocked, retain the recordings and code and mark replay unverified.

For a standalone suite, these are the setup and regression command shapes (adapt the interpreter, paths, browser, and startup to the target project):

```sh
python3 -m venv .venv-ui
.venv-ui/bin/python -m pip install -r tests/requirements.txt
.venv-ui/bin/python -m playwright install chromium
# Start the application using its documented project command first.
# Add UI_TEST_BASE_URL to the root .env and export it before this command.
# The shell must have this value before expanding the --base-url argument.
.venv-ui/bin/python -m pytest tests \
  --base-url "${UI_TEST_BASE_URL:?Set UI_TEST_BASE_URL}" \
  --browser chromium --tracing retain-on-failure --screenshot only-on-failure \
  --output outputs/ui-test-<timestamp>/playwright/replay-<invocation-id> \
  --junitxml outputs/ui-test-<timestamp>/junit-<invocation-id>.xml
```

Replace `<timestamp>` with the exact timestamp in `reports/ui-test-report-<timestamp>.md` and `<invocation-id>` with a unique replay identifier before publishing an exact command. Create the output folder first. Use a distinct Playwright child directory per replay because subsequent Playwright runs may clear their output directory. Later standalone regression runs choose a new timestamp and create a new `outputs/ui-test-<timestamp>/` folder. Save all run artifacts there, including logs, evidence, videos, downloads, exports, and JUnit XML; only the Markdown test report belongs in `reports/`. Python regression scripts and reusable suite support files remain in `tests/`. If `tests/` also contains unrelated tests, scope the UI regression command to the generated modules or subfolders rather than running unrelated suites. Also document a single-case command using the saved module/function node ID and the same base URL and artifact options. The regression run uses only Python and the browser; it must not call AI, browser-agent tools, or ticket systems. Pytest provides a nonzero exit for failing tests and JUnit results for CI. JUnit does not automatically produce the skill's Markdown report or bug tickets.

## Record during UI execution

Maintain one structured JSON recording per source case under `outputs/ui-test-<timestamp>/steps/`, updating it after each meaningful action. Record:

- Source Markdown path and content hash, generated Python module/function, run time, and original case outcome.
- Setup, required environment variable names, fixture/reset procedure, and starting route.
- Ordered steps: action, observed locator and frame/page context, requested input/selection rule and value source, non-sensitive input or environment/fixture reference, expected result, actual observation, and evidence path when available.
- Cleanup, any unexecuted steps, generation limitations, replay command, and separate automation status/result.

This is a durable semantic record, not a mouse-coordinate transcript. Discover locators from actual DOM/accessibility evidence; never invent selectors from screenshots. When the UI tool cannot expose enough DOM evidence, inspect it using available authorized browser tooling. If that remains unavailable, record the gap and save an incomplete skipped test rather than pretending to have verified selectors. Tool-call recording and Playwright codegen can help capture actions, but neither supplies all expected-result assertions or fixture setup automatically.

Record locators and observations while they are available, rather than reconstructing everything at the end. Redact secrets and personal data from recordings, URLs, evidence, and code. Credentials come from environment variables or the project's existing secret mechanism. Keep authentication state, local environment files, and sensitive artifacts out of version control using the project's ignore conventions; document necessary local state regeneration.

## Turn recordings into tests

Write pytest functions with the following template, using `playwright.sync_api.expect` for final expectation verification:

```python
def test_case_name(browser, base_url):
    context = browser.new_context(base_url=base_url)
    try:
        page = context.new_page()
        # Recorded setup, actions, and final expected-result assertions.
    finally:
        # Perform any case-specific cleanup without verifying its results.
        context.close()
```

Keep the `browser, base_url` parameters for every generated case, including skipped placeholders. Each final expectation needs a corresponding assertion; clicks alone do not establish success. Intermediate locator visibility checks and cleanup results are excluded from these assertions.

For a locator visibility step outside final expectation verification, use `is_visible` or `is_hidden` with a five-second timeout budget and use the returned Boolean for control flow. Do not wrap it in `expect`, `assert`, or another validation that fails the test. Playwright ignores the `timeout` parameter on these methods, so use bounded polling rather than assuming `is_visible(timeout=5000)` waits:

```python
from time import monotonic


def visibility_status(locator, *, hidden=False, timeout_ms=5000):
    deadline = monotonic() + timeout_ms / 1000
    check = locator.is_hidden if hidden else locator.is_visible
    while True:
        if check():
            return True
        remaining_ms = (deadline - monotonic()) * 1000
        if remaining_ms <= 0:
            return False
        locator.page.wait_for_timeout(min(100, remaining_ms))
```

Use `if visibility_status(locator): ...` or `if visibility_status(locator, hidden=True): ...` for the corresponding recorded action. A timeout returns `False` without asserting. Reserve visibility `expect` assertions for final expectation verification. This bounded polling is the exception to the general guidance against fixed sleeps. See the official [visibility API](https://playwright.dev/python/docs/api/class-locator#locator-is-visible) for timeout semantics.

- Prefer observed role/name, label, or stable test-ID locators. Scope ambiguous targets; use frame locators and popup pages where observed. Avoid coordinates, generated CSS classes, positional selectors, and XPath unless evidence shows a stable alternative is unavailable. Positional selection is appropriate when it expresses the user's explicit rule, such as the first available option in a scoped list.
- Preserve requested input and selection rules instead of freezing values observed during recording. Use literal test data only when the user explicitly supplied it; stable control labels and test IDs may still identify controls. Resolve derived values from the current UI, configuration, or fixtures according to the recorded rule at replay time. For “select the first available option”, locate the scoped list, wait for eligible options, exclude disabled options and placeholders as required, and select the first eligible option. Do not hardcode “black” in an option locator, input, fixture default, or assertion merely because it was selected during recording. Capture the runtime-selected value when needed and assert that subsequent UI reflects it. If no eligible option exists, fail with a clear assertion; do not silently substitute another rule. Unclear selection intent is a generation blocker, not permission to guess.
- Use Playwright action waiting and retrying `expect` assertions for final expected outcomes. For intermediate visibility steps, use the five-second Boolean polling rule above without assertions. Avoid other fixed sleeps. Use event expectations around downloads, popups, or dialogs when relevant.
- Use configurable base URLs and routes; keep credentials out of source. Make missing required configuration an explicit error or documented skip. Never let missing setup silently pass.
- Give each test independent setup and cleanup. Always create a new context with `browser.new_context()` and close it in `finally`; do not use saved `storage_state`, persistent profiles, or previously authenticated contexts. Authenticate through recorded setup in that new context when needed. A fresh browser context isolates session state but does not reset server data. Use approved fixtures/reset helpers, unique test data, and cleanup to make repeat runs possible. Do not depend on the preceding case or an already logged-in AI browser session.
- Generate cleanup actions in teardown (such as a fixture finalizer or `finally` block) so they execute even when a test assertion fails. Execute the cleanup without verifying its result: do not add `assert`, `expect`, response-status checks, polling, or follow-up UI/API queries to confirm deletion or reset. Playwright's normal action waiting and interactions needed to perform cleanup, such as confirming a delete dialog, are still appropriate.
- Express supported explicit skip conditions with `pytest.skip` or skip markers and a reason. Do not catch assertion errors and convert them to skips. A known application defect retains its intended failing assertion; do not add unconditional skips or `xfail` just to make the suite green.
- For a blocked or partially observed case, retain the recorded actions and create a clearly skipped test with its precise generation blocker. Do not put guessed, unobserved steps into executable code. Record the missing automated coverage in the separate recording and suite README.
- Native desktop actions and external manual approvals require documented prerequisites or unsupported coverage. Do not claim Playwright implements desktop automation or unattended MFA/CAPTCHA bypass.

When authoring new fixture/helper logic, follow the target project's TDD instructions. For the regression case itself, define assertions from the original requirements before actions, run to demonstrate meaningful failure when feasible (for example with missing setup), then implement the observed steps and verify. Do not modify application code as part of a test-running request unless authorized.

## Verify and hand off

Check imports and collect the generated suite, then run it against the target application from a clean context with repeatable fixture state. Replay only actions within the existing authorization; do not repeat irreversible submissions just to validate generated code. Record blocked verification explicitly.

Fix generation errors such as incorrect locators, missing setup, or invalid Python without weakening original expectations. Preserve application failures. If the initial UI run and replay disagree, investigate the discrepancy and record both outcomes in the separate recording; a changed UI or fixture state can explain it. Keep investigation within the requested scope and stop when further execution needs missing access, fixtures, or authorization.

A `verified` script has passed an actual replay with all expectations asserted. A script that reproduces the intended application failure is labeled `reproduces failure`, with its failing assertion recorded. Syntax checks, collection, missing prerequisites, and unresolved replay errors mean `unverified`. A skipped placeholder provides no regression coverage. Keep these statuses and generation/replay details in the separate recording and suite README. The Markdown test report retains the initial UI case results and includes only `regression test case: [script filename](script test file path)` as additional information in `Details`; it does not include generation or replay results.

Before finishing, confirm every discovered web case has a recording and either a mapped Python case or an explicit unsupported reason; scripts match the current source definitions; no secrets are committed; and the README contains the exact commands and prerequisites needed to rerun without AI. Do not claim a real application replay occurred if only this skill package was edited.

Official references for environment-specific options: [installation](https://playwright.dev/python/docs/intro), [pytest fixtures and CLI](https://playwright.dev/python/docs/test-runners), [locators](https://playwright.dev/python/docs/locators), and [assertions](https://playwright.dev/python/docs/test-assertions).
