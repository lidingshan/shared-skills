# Python Playwright regression workflow

## Prepare the target project

Inspect existing test infrastructure, dependency management, ignore rules, and application startup instructions. Preserve existing tests and configuration. Use Python, `pytest`, `pytest-playwright`, and Playwright's synchronous API; generate synchronous tests with the required `browser, base_url` signature, adapting existing infrastructure as needed. A JavaScript suite may supply fixtures and selectors but does not replace the requested Python deliverable.

Read Markdown source cases only from `agent-tests/`. Save generated Python tests under `tests/`, preserving existing tests and using subfolders when needed. For example, `agent-tests/accounts/test_login.md` can map to `tests/accounts/test_login.py`.

When no Python UI suite exists, create in the target application:

- `tests/test_*.py`: collected regression tests, written in the domain language of the support layer.
- `tests/support/`: the reusable page objects, components, flows, test data, and helpers described in [Design the suite for maintainability](#design-the-suite-for-maintainability).
- `tests/conftest.py`: project environment and base URL fixtures, plus shared suite hooks when needed.
- `tests/requirements.txt`: required packages and versions validated in that project, unless its dependency manager already records them.
- `tests/README.md`: application startup, installation, required environment variables, test data/reset procedure, full-suite and single-case commands, and artifact locations. Include limitations and any manual prerequisites.
- `outputs/ui-test-<timestamp>/steps/`: per-case recordings from the current run.

Add every required environment variable to the target application root `.env`, preserving existing entries. Use empty values with setup comments for unknown values. Use the bundled [conftest.py](../tests/conftest.py) to load the root `.env` without overriding exported variables. The fixture preserves pytest’s configured base URL and falls back to `UI_TEST_BASE_URL`. Keep `.env` ignored by version control and document required values. Merge with any existing fixture or dotenv loader so the suite loads the file once. If a generated case needs a base URL and none is configured, report the missing prerequisite explicitly.

Keep Python setup and run instructions in `tests/README.md`. Markdown case discovery scans only `agent-tests/`; it does not scan `tests/`. Map each source case to a stable Python module/function, using its project-relative path to avoid collisions between similarly named cases. Include the source path in a docstring or comment. Reuse that mapping on subsequent runs and review edits rather than appending duplicate tests or replacing maintained suites. Persist the mapping in the recordings and run instructions.

Install missing test tools in the project's managed environment or a dedicated `.venv-ui`; install the chosen Playwright browser. Record tested versions in the project's dependency file/lock. Do not upgrade unrelated dependencies. If setup is blocked, retain the recordings and code and mark replay unverified.

For a standalone suite, these are the setup and regression command shapes (adapt the interpreter, paths, browser, and startup to the target project):

```sh
python3 -m venv .venv-ui
.venv-ui/bin/python -m pip install -r tests/requirements.txt
.venv-ui/bin/python -m playwright install chromium
# Start the application using its documented project command first.
# Add UI_TEST_BASE_URL to the root .env.
.venv-ui/bin/python -m pytest tests \
  --browser chromium --tracing off --screenshot only-on-failure \
  --output outputs/ui-test-<timestamp>/playwright/replay-<invocation-id> \
  --junitxml outputs/ui-test-<timestamp>/junit-<invocation-id>.xml
```

Keep `--tracing off` in documented commands: a Playwright trace stores the values passed to `fill` and `type`, including passwords. When a trace is needed for debugging, start it inside the test only after sign-in and any other secret entry have finished, and save it under the run's output folder:

```python
context.tracing.start(screenshots=True, snapshots=True)  # after sign-in completes
...
context.tracing.stop(path=trace_path)
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

## Design the suite for maintainability

Generated tests must stay cheap to change when the UI changes. Separate *what* a case verifies from *how* the UI is driven: test modules speak the application's domain language, and a support layer owns every locator and interaction detail. A UI change should then be fixed in one place, not in every test that touches that screen.

### Layers

Organize reusable code under `tests/support/` (adapt to an existing project convention such as `tests/pages/` when one exists):

```
tests/
├── conftest.py
├── support/
│   ├── __init__.py
│   ├── config.py           # Typed access to required environment variables
│   ├── data.py             # Test data builders and unique-value helpers
│   ├── waits.py            # visibility_status and other bounded-wait helpers
│   ├── components/         # Reusable UI fragments: header, dialog, table, date picker
│   ├── pages/              # One page object per screen or route
│   └── flows.py            # Multi-page domain tasks: sign in, create an order
└── shop/
    └── test_add_to_cart.py # Test cases composed from flows and page objects
```

| Layer | Owns | Must not |
|---|---|---|
| Test module | Case intent, test data choice, final `expect` assertions, cleanup orchestration | Contain raw locators, selectors, URLs, or credential lookups |
| Flow | A reusable business task spanning pages (for example `sign_in_as_test_user`) | Assert expected outcomes of the case |
| Page object | Locators and user-intent actions for one screen; navigation to the next page object | Assert final expectations or reach into another page's locators |
| Component | Locators and actions scoped to a root `Locator`, reused across pages | Depend on a specific page or use unscoped `page` locators |
| Support helpers | Configuration, data builders, bounded waits | Hold UI-specific locators |

### Object-oriented design rules

- **Single source of truth for locators.** Define each locator once, as an attribute or property of the page object or component that owns that UI. Use observed role/name, label, or test-ID locators per the locator rules below. When a second test needs the same control, reuse the owner; never copy the locator into another module.
- **Intent-revealing methods.** Name methods after the user's goal (`add_to_cart`, `choose_first_available_colour`, `sign_in`), not the mechanics (`click_button`, `fill_field_2`). A test should read like the Markdown case's `Steps`.
- **Return the next page object.** A method that navigates returns the page object the user lands on, so tests chain naturally and type checkers catch misuse. Methods that stay on the same page may return `self` or a captured runtime value (such as the option chosen by a selection rule).
- **Composition over inheritance.** Use a single shallow `BasePage` for behavior shared by every page (page handle, route opening, bounded visibility checks). Model repeated fragments (navigation bar, modal dialog, data table row) as components that pages *contain*, scoped to a root locator. Avoid inheritance chains deeper than `BasePage → ConcretePage`.
- **Parameterize instead of duplicating.** When two pages or components differ only by a name, label, or route, take it as a constructor or method argument (for example `table.row(name)`), rather than generating near-identical classes or methods.
- **Encode selection rules once.** Implement recorded rules such as "first available option" as a page-object method that resolves the value at replay time and returns it. Tests then assert on the returned value; no test hardcodes a value observed during recording.
- **Keep assertions in tests.** Page objects expose locators (or small read-only accessors) that tests pass to `expect`. A page object may wait for readiness with Playwright's auto-waiting or `locator.wait_for()`, and may raise a clear `AssertionError` when a recorded rule cannot be satisfied (such as no eligible option), but it never verifies the case's expected results. This keeps every final expectation visible in the test body.
- **Centralize configuration and data.** Read environment variables only through `support/config.py`, which raises an explicit error naming the missing variable. Generate unique test data (names, emails) through `support/data.py` builders so repeated runs do not collide. Keep credentials out of page objects' defaults.
- **Cleanup through the same abstractions.** Teardown actions use page-object methods (for example `cart.empty()`), still without verifying their result.
- **Keep tests DAMP.** Remove duplication of *mechanics*, not of *meaning*: each test should still show its key data and every final expectation without the reader opening helpers. Do not hide a whole case behind one generic helper or build data-driven mega-tests that obscure which source case failed.

### Reuse and evolve the support layer

- Before generating a case, inventory existing page objects, components, and flows in `tests/support/` (or the project's equivalent). Extend an existing class with a new method or locator before creating a new one.
- When generation reveals duplicated locators or interaction sequences in existing generated tests, move them into the owning page object or flow and update the affected generated tests in the same change. Keep such refactors within the generated UI suite and the requested scope; do not rewrite unrelated maintained tests.
- Keep support modules out of test collection: no `test_` filename prefix and no `test_`-prefixed functions or `Test`-prefixed classes in `tests/support/`. Make `tests/` and its subfolders importable packages (add `__init__.py`) and import as `from tests.support.pages.product_page import ProductPage`, unless the project already configures another import root (for example `pythonpath` in pytest configuration). Confirm imports with a collection run.
- Add type hints to public page-object and flow methods; they act as living documentation of the domain language.
- In each step recording, note the page-object or flow member that implements the step so future regeneration updates the same member instead of adding a duplicate.

### Reference implementation

Adapt names, routes, and locators to what was actually observed; do not copy example locators into a real suite.

```python
# tests/support/waits.py
from time import monotonic

from playwright.sync_api import Locator


def visibility_status(locator: Locator, *, hidden: bool = False, timeout_ms: int = 5000) -> bool:
    """Return whether the locator becomes visible (or hidden) within the budget, without asserting."""
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

```python
# tests/support/config.py
import os

import pytest


def require_env(name: str) -> str:
    """Return a required setting from the environment or fail with an explicit setup error."""
    value = os.getenv(name)
    if not value:
        pytest.fail(f"Set {name} in the project root .env (see tests/README.md).", pytrace=False)
    return value
```

```python
# tests/support/pages/base_page.py
from typing import Optional

from playwright.sync_api import Locator, Page

from tests.support.waits import visibility_status


class BasePage:
    """Behavior shared by every page object. Subclasses define PATH and their own locators."""

    PATH = "/"

    def __init__(self, page: Page, path: Optional[str] = None) -> None:
        self.page = page
        self.path = path or self.PATH

    def open(self):
        self.page.goto(self.path)
        return self

    def is_shown(self, locator: Locator, *, timeout_ms: int = 5000) -> bool:
        return visibility_status(locator, timeout_ms=timeout_ms)
```

```python
# tests/support/components/header.py
from playwright.sync_api import Locator


class Header:
    """Site header, scoped to its own root so it works on every page that contains it."""

    def __init__(self, root: Locator) -> None:
        self.root = root
        self.cart_link = root.get_by_role("link", name="Cart")
        self.cart_count = root.get_by_test_id("cart-count")

    def go_to_cart(self) -> None:
        self.cart_link.click()
```

```python
# tests/support/pages/product_page.py
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from tests.support.components.header import Header
from tests.support.pages.base_page import BasePage
from tests.support.pages.cart_page import CartPage


class ProductPage(BasePage):
    def __init__(self, page: Page, path: str) -> None:
        super().__init__(page, path)
        self.header = Header(page.get_by_role("banner"))
        self.title = page.get_by_role("heading", level=1)
        self.colour = page.get_by_label("Colour")
        self.add_to_cart_button = page.get_by_role("button", name="Add to cart")
        self.promo_dismiss = page.get_by_role("button", name="No thanks")

    def dismiss_promo_if_shown(self) -> "ProductPage":
        if self.is_shown(self.promo_dismiss):
            self.promo_dismiss.click()
        return self

    def choose_first_available_colour(self) -> str:
        """Recorded rule: select the first enabled, non-placeholder colour; return its label."""
        option = self.colour.locator("option:not([disabled]):not([value=''])").first
        try:
            option.wait_for(state="attached")
        except PlaywrightTimeoutError:
            raise AssertionError("No available colour option to select") from None
        label = option.inner_text().strip()
        self.colour.select_option(label=label)
        return label

    def add_to_cart(self) -> CartPage:
        self.add_to_cart_button.click()
        self.header.go_to_cart()
        return CartPage(self.page)
```

```python
# tests/support/pages/cart_page.py
from playwright.sync_api import Locator

from tests.support.pages.base_page import BasePage


class CartPage(BasePage):
    PATH = "/cart"

    def __init__(self, page) -> None:
        super().__init__(page)
        self.items = page.get_by_test_id("cart-item")

    def item(self, product_name: str) -> Locator:
        return self.items.filter(has_text=product_name)

    def empty(self, max_items: int = 50) -> None:
        """Cleanup action: remove every item. Callers must not verify the result."""
        remove_button = self.page.get_by_role("button", name="Remove").first
        for _ in range(max_items):
            if not self.is_shown(remove_button, timeout_ms=1000):
                break
            remove_button.click()
```

```python
# tests/support/pages/login_page.py
from playwright.sync_api import Page

from tests.support.pages.base_page import BasePage


class LoginPage(BasePage):
    PATH = "/login"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.username = page.get_by_label("Username")
        self.password = page.get_by_label("Password")
        self.submit = page.get_by_role("button", name="Sign in")

    def sign_in(self, username: str, password: str) -> BasePage:
        self.username.fill(username)
        self.password.fill(password)
        self.submit.click()
        return BasePage(self.page)  # Return the observed landing page object in a real suite.
```

```python
# tests/support/flows.py
from playwright.sync_api import Page

from tests.support.config import require_env
from tests.support.pages.login_page import LoginPage


def sign_in_as_test_user(page: Page):
    """Sign in through the UI in the current fresh context; returns the landing page object."""
    return LoginPage(page).open().sign_in(
        require_env("UI_TEST_USERNAME"), require_env("UI_TEST_PASSWORD")
    )
```

```python
# tests/shop/test_add_to_cart.py
"""Regression test generated from agent-tests/shop/test_add_to_cart.md."""
from playwright.sync_api import expect

from tests.support.config import require_env
from tests.support.flows import sign_in_as_test_user
from tests.support.pages.cart_page import CartPage
from tests.support.pages.product_page import ProductPage


def test_add_first_available_colour_to_cart(browser, base_url):
    """Source: agent-tests/shop/test_add_to_cart.md"""
    context = browser.new_context(base_url=base_url)
    page = None
    try:
        page = context.new_page()
        sign_in_as_test_user(page)

        product = ProductPage(page, require_env("UI_TEST_PRODUCT_PATH")).open().dismiss_promo_if_shown()
        product_name = product.title.inner_text()
        colour = product.choose_first_available_colour()
        cart = product.add_to_cart()

        expect(cart.item(product_name)).to_contain_text(colour)
    finally:
        try:
            if page is not None:
                CartPage(page).open().empty()
        finally:
            context.close()
```

The nested `finally` guarantees the context closes even if a cleanup action raises, and cleanup runs even when an assertion fails.

## Turn recordings into tests

Write pytest functions with the following template, composing page objects and flows from `tests/support/` and using `playwright.sync_api.expect` for final expectation verification:

```python
def test_case_name(browser, base_url):
    context = browser.new_context(base_url=base_url)
    page = None
    try:
        page = context.new_page()
        # Recorded setup and actions via flows/page objects, then final expect assertions.
    finally:
        try:
            ...  # Case-specific cleanup via page-object methods, without verification.
        finally:
            context.close()
```

Keep the `browser, base_url` parameters for every generated case, including skipped placeholders. Keep the explicit `browser.new_context()` and `try`/`finally` in each test body so isolation stays visible; share everything else through the support layer. Each final expectation needs a corresponding assertion in the test body; clicks alone do not establish success. Use the visibility and teardown rules below for other steps.

For a locator visibility step outside final expectation verification, use `is_visible` or `is_hidden` with a five-second timeout budget and use the returned Boolean for control flow. Do not wrap it in `expect`, `assert`, or another validation that fails the test. Playwright ignores the `timeout` parameter on these methods, so use bounded polling rather than assuming `is_visible(timeout=5000)` waits. Define `visibility_status` once in `tests/support/waits.py` (see the reference implementation above) and call it through `BasePage.is_shown` or directly; never copy it into individual test modules.

Use `if page_object.is_shown(locator): ...` or `if visibility_status(locator, hidden=True): ...` for the corresponding recorded action, and prefer wrapping the pattern in an intent-named page-object method such as `dismiss_promo_if_shown()`. A timeout returns `False` without asserting. Reserve visibility `expect` assertions for final expectation verification. This bounded polling is the exception to the general guidance against fixed sleeps. See the official [visibility API](https://playwright.dev/python/docs/api/class-locator#locator-is-visible) for timeout semantics.

- Prefer observed role/name, label, or stable test-ID locators. Scope ambiguous targets; use frame locators and popup pages where observed. Avoid coordinates, generated CSS classes, positional selectors, and XPath unless evidence shows a stable alternative is unavailable. Positional selection is appropriate when it expresses the user's explicit rule, such as the first available option in a scoped list.
- Preserve requested input and selection rules instead of freezing values observed during recording. Use literal test data only when the user explicitly supplied it; stable control labels and test IDs may still identify controls. Resolve derived values from the current UI, configuration, or fixtures according to the recorded rule at replay time. For “select the first available option”, locate the scoped list, wait for eligible options, exclude disabled options and placeholders as required, and select the first eligible option. Do not hardcode “black” in an option locator, input, fixture default, or assertion merely because it was selected during recording. Capture the runtime-selected value when needed and assert that subsequent UI reflects it. If no eligible option exists, fail with a clear assertion; do not silently substitute another rule. Unclear selection intent is a generation blocker, not permission to guess.
- Use Playwright action waiting and retrying `expect` assertions for final expected outcomes. Avoid other fixed sleeps. Use event expectations around downloads, popups, or dialogs when relevant.
- Use configurable base URLs and routes; keep credentials out of source. Make missing required configuration an explicit error or documented skip. Never let missing setup silently pass.
- Give each test independent setup and cleanup. Always create a new context with `browser.new_context()` and close it in `finally`; do not use saved `storage_state`, persistent profiles, or previously authenticated contexts. Authenticate through recorded setup in that new context when needed. A fresh browser context isolates session state but does not reset server data. Use approved fixtures/reset helpers, unique test data, and cleanup to make repeat runs possible. Do not depend on the preceding case or an already logged-in AI browser session.
- Generate cleanup actions in teardown (such as a fixture finalizer or `finally` block) so they execute even when a test assertion fails. Execute the cleanup without verifying its result: do not add `assert`, `expect`, response-status checks, polling, or follow-up UI/API queries to confirm deletion or reset. Playwright's normal action waiting and interactions needed to perform cleanup, such as confirming a delete dialog, are still appropriate.
- Express supported explicit skip conditions with `pytest.skip` or skip markers and a reason. Do not catch assertion errors and convert them to skips. A known application defect retains its intended failing assertion; do not add unconditional skips or `xfail` just to make the suite green.
- For a blocked or partially observed case, retain the recorded actions and create a clearly skipped test with its precise generation blocker. Do not put guessed, unobserved steps into executable code. Record the missing automated coverage in the separate recording and suite README.
- Native desktop actions and external manual approvals require documented prerequisites or unsupported coverage. Do not claim Playwright implements desktop automation or unattended MFA/CAPTCHA bypass.

When authoring new fixture/helper logic, follow the target project's TDD instructions. For the regression case itself, define assertions from the original requirements before actions, run to demonstrate meaningful failure when feasible (for example with missing setup), then implement the observed steps and verify. Do not modify application code as part of a test-running request unless authorized.

## Generate suite hooks

Translate the recorded steps from `agent-tests/before-all.md` and `agent-tests/after-all.md` into shared Python setup and teardown helpers. Reference each source path in its helper. Build the helpers from the same page objects and flows as the cases (for example in `tests/support/hooks.py`) rather than duplicating locators or sign-in steps. Wire them into the target project's pytest configuration, normally in `tests/conftest.py`, and merge with existing hooks. Generate only the helpers for files that exist. Keep them out of test collection.

- Scope the lifecycle to invocations with selected generated UI cases from this suite, including single-case runs. Identify them by a registered marker or another explicit mapping. Run setup once before the first matching case and teardown once after the last, even when every matching case is statically skipped. Use a pytest run-level wrapper such as `pytest_runtestloop` with a `finally` block. A fixture alone can be bypassed by static skips. Skip the hooks for runs without matching cases. Document a serial replay command and reject parallel worker execution for the hooked suite unless it already supports a single coordinated lifecycle.
- Make setup failures visible and skip the affected case bodies with the setup reason. Attempt teardown even after partial setup, and surface teardown action errors without masking earlier failures. Keep hooks independent of individual test outcomes and of any per-case browser or authentication state. For UI actions, use dedicated fresh browser contexts and close them reliably. Apply the same teardown rules as for individual cases.
- If a present hook cannot be translated reliably, document the gap and block affected automated replay explicitly instead of silently omitting the hook. Update the suite README with the lifecycle, prerequisites, and replay commands.

Verify hook order and once-per-run behavior with multiple selected cases, a single case, an all-skipped selection, a case failure, and a setup failure. Also verify an unrelated-only selection leaves both hooks idle.

## Verify and hand off

Check imports and collect the generated suite, then run it against the target application from a clean context with repeatable fixture state. Replay only actions within the existing authorization; do not repeat irreversible submissions just to validate generated code. Record blocked verification explicitly.

Fix generation errors such as incorrect locators, missing setup, or invalid Python without weakening original expectations. Preserve application failures. If the initial UI run and replay disagree, investigate the discrepancy and record both outcomes in the separate recording; a changed UI or fixture state can explain it. Keep investigation within the requested scope and stop when further execution needs missing access, fixtures, or authorization.

A `verified` script has passed an actual replay with all expectations asserted. A script that reproduces the intended application failure is labeled `reproduces failure`, with its failing assertion recorded. Syntax checks, collection, missing prerequisites, and unresolved replay errors mean `unverified`. A skipped placeholder provides no regression coverage. Keep these statuses and generation/replay details in the separate recording and suite README. For Markdown cases, the test report retains the initial UI results and includes only `regression test case: [script filename](script test file path)` as additional information in `Details`; it does not include generation or replay results.

Before finishing, confirm every selected Markdown web case has a recording and either a mapped Python case or an explicit unsupported reason; scripts match the current source definitions; generated test modules contain no raw locators and no locator is defined in more than one support module; final expectations remain in test bodies; no secrets are committed; and the README contains the exact commands and prerequisites needed to rerun without AI. Do not claim a real application replay occurred if only this skill package was edited.

Official references for environment-specific options: [installation](https://playwright.dev/python/docs/intro), [pytest fixtures and CLI](https://playwright.dev/python/docs/test-runners), [locators](https://playwright.dev/python/docs/locators), and [assertions](https://playwright.dev/python/docs/test-assertions).
