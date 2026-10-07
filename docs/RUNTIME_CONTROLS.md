# Runtime controls and tenant access

Implemented locally on 3 October 2026. These opt-in controls extend the
[router redesign](ROUTER_REDESIGN.md); the default remains an offline alpha.
They do not establish measured accuracy, provider billing guarantees or a hosted
service. The existing repository and its 12 role contracts remain the project.

## Configure and run

```bash
PYTHONPATH=src python examples/runtime_controls.py
```

The executable example uses a fake bounded caller and a temporary SQLite file.
All prices and results are synthetic. For an application, inject an explicit
caller, a server-owned `ExecutionPolicy` and optionally `CircuitBreaker` into
`build_container`. Controls without an explicit caller are rejected.

```python
from ai_gateway import CircuitBreaker, ExecutionPolicy, SQLiteBudgetLedger, build_container

# Operator-owned file outside the repository; parent directory must exist.
ledger = SQLiteBudgetLedger("/var/lib/my-gateway/budget.sqlite")
ledger.configure_account("tenant-a", 1_000_000)  # cumulative account limit: $1
policy = ExecutionPolicy(
    ledger=ledger,
    account="tenant-a",
    # Supply verified upper charges in integer micro-USD for every catalog
    # deployment that can participate, including fallback and synthesis.
    charge_limits=operator_charge_ceilings,
    max_prompt_bytes=32_000,
    max_output_tokens=1_000,
    timeout_ms=10_000,
    max_model_calls=3,
    max_concurrent_calls=8,  # shared provider-call slots in this container/process
)
container = build_container(
    model_caller=caller, model_catalog=catalog,
    execution_policy=policy, circuit_breaker=CircuitBreaker(),
)
```

`caller`, `catalog` and `operator_charge_ceilings` are application configuration,
not bundled live values. A catalog average cannot establish a charge ceiling.
Include maximum input/output/reasoning usage, provider fees and any adapter
retries when establishing that ceiling. Keep hidden retries disabled. The policy
requires prompt and output caps whenever a ledger is supplied, and checks every
planned deployment has a ceiling before contacting a provider.

## Cost admission and reconciliation

`budget.py` uses SQLite `BEGIN IMMEDIATE` transactions across connections to one
local database. Amounts are integer micro-USD. Admission reserves the declared
ceiling before each provider attempt; confirmed charges replace reservations.
The account admission test is `spent + pending ceilings + new ceiling <= limit`.
Parallel samples share the same account and request accounting. Request
`max_cost_usd` adds a runtime admission ceiling when a ledger is configured;
otherwise it remains an estimated planning filter. The existing conservative
council prohibition with request cost caps is unchanged.

This is cumulative accounting, with no automatic monthly reset. Limit updates
cannot fall below outstanding exposure. Actual fractional microdollars round
up; request ceilings round down. Each attempt has a fresh ID; a reservation ID
cannot authorize repeated execution. This is not whole-request idempotency:
repeating an HTTP request can make new, separately charged calls.

Unknown billing, transport failures and crashes after reservation leave the full
ceiling held across restart. There is no timeout refund: a timed-out provider may
still bill. Successful calls from the bundled OpenAI-compatible adapter report
tokens but no dollar price, so their reservations also remain pending. Operators
must reconcile against authoritative invoices or provide a trusted adapter that
reports actual cost. Inspect `ledger.pending(account)` for prompt-free request,
attempt and ceiling IDs, then call `ledger.settle(account, attempt_id, actual)`.
Use zero only with evidence that no charge occurred. Same-amount settlement is
idempotent; changing an already settled amount is rejected. Failure responses
include a request ID so pending reservations can be found.

An actual charge above its declared ceiling is preserved, and the account is
frozen for future admission. Raising the limit does not unfreeze it. There is no
automatic correction/unfreeze API: breach recovery requires a reviewed operator
procedure before resuming service. Already admitted concurrent calls cannot be
recalled, and overbilling cannot be undone. `hard_budget_respected` consequently
remains false; response metadata describes reservation semantics instead.

SQLite is a single-host starting point, not a distributed billing service. The
operator owns filesystem permissions, encryption, backups, reconciliation,
retention and growth management. Records contain identifiers and amounts, no
prompt/output content. Telemetry remains a separate bounded in-memory store.

## Shared execution limits and provider health

`controls.py` wraps single, cascade, sampling and council calls. The lower of
server/request limits applies; clients cannot relax the server policy. The full
planned call count is checked before execution, and concurrent admissions count
against that bound. Expanded prompts, including council context, must fit the
byte cap. With controls active, custom tool execution is rejected because these
limits do not cover arbitrary tool effects.

`max_concurrent_calls` optionally caps simultaneous provider calls across all
requests/strategies on the container. Saturation rejects immediately before budget
reservation; slots are released after success or failure. It is not a queue,
requests-per-minute quota, distributed limiter or cap on HTTP parsing/worker memory.
Separate containers/processes have separate capacity. Configure an ingress limit
and coordinate provider-wide capacity across workers before exposing the service.

Request fields `execution_timeout_ms` and `max_output_tokens` are also available
through the API. `max_latency_ms` remains a catalog planning filter; it is not the
execution deadline. The shared deadline starts at execution dispatch, includes
execution verification/aggregation, and is rechecked before and after provider
calls. Queueing, request parsing and routing are outside this deadline. Remaining
time is passed to the adapter. Late results are rejected but their reported
charges remain recorded; exhausted time prevents additional fallback calls.

The adapter must implement
`complete_with_limits(model, prompt, *, timeout_seconds, max_output_tokens)`
when deadline or output limits apply. Unsupported adapters fail before contact.
The bundled adapter sends `timeout` and `max_completion_tokens`, with SDK retries
disabled. Providers must support the completion cap, including reasoning tokens
where applicable. Reported token overruns are rejected after accounting for cost.

Synchronous calls cannot be force-killed. An SDK timeout can apply to individual
transport phases, and an uncooperative provider may ignore a cap. These controls
bound admission and reject late responses; they are not a hard wall-clock SLO.

The optional process-local circuit breaker opens after consecutive failures,
allows one probe after cooldown, and ignores stale completions from an earlier
state. Local circuit denials incur zero provider charge and release only their
own unspent reservation. Ambiguous upstream failures remain reserved. Circuit
state is not shared across workers or retained on restart.

Usage `calls` counts gateway attempts, including denied attempts; successful
responses additionally expose actual provider contacts in
`metadata.execution_controls.provider_calls`. Denials known to occur before
contact have zero usage, while ambiguous failures retain unknown cost.

## Optional tenant API mode

```python
import os
from ai_gateway.api import create_app

# Containers are built separately with reviewed providers and policies.
app = create_app(tenants={
    os.environ["GATEWAY_TENANT_A_TOKEN"]: tenant_a_container,
    os.environ["GATEWAY_TENANT_B_TOKEN"]: tenant_b_container,
})
```

Use strong, distinct secrets supplied outside source control. A bearer token
selects the server-owned container; submitted tenant IDs have no authority.
Every path except `/health`, including docs, assets, telemetry and feedback,
requires authentication. Separate telemetry stores and distinct ledger accounts
are required. Different tenant accounts may share one SQLite file. Canonical
file paths prevent accidental account reuse through symlink aliases.

Tenant clients cannot replace the server provider. In trusted local mode,
runtime provider overrides are also rejected when server execution controls are
configured. Default `create_app()` retains its existing trusted-local behavior
and does not enable authentication. The built-in browser console has no bearer
login flow; use tenant mode through an authenticated API client or an appropriately
configured application. Nothing is deployed by constructing these containers.

This is a static credential-to-container boundary, not complete identity or
authorization infrastructure. Tokens grant all API operations within their
tenant, including feedback; per-user feedback permissions and label provenance
remain application responsibilities. TLS, key rotation/revocation, SSO/RBAC,
rate/concurrency limits, abuse controls, durable tenant telemetry and deployment
security testing remain launch requirements. Avoid shared mutable custom
handlers or other application objects that could leak state between containers.

## Validation and remaining work

Completion checks: 226 tests passed on Python 3.11.16 and 3.14.7; Ruff, diff
whitespace, 12-role validation and the deterministic readiness audit passed.
Source/wheel builds, Twine metadata and an isolated installed-wheel core smoke
passed. Python 3.12/3.13, other operating systems and live provider calls were
not exercised in this pass. The static audit is not production certification.

Offline regression tests cover concurrent admission, restart persistence,
account-scoped reconciliation, uncertain charges, overbilling, parallel samples,
late-result accounting, circuit probes, call/prompt caps, adapter forwarding,
tenant telemetry/feedback isolation and override rejection. The runnable example
is included in the source distribution and executed by the suite. These are
builder checks, not independent certification or live provider contract tests.

The next substantive product step is a representative, authorized dataset with
independent calibration/test splits and reliable quality labels. Use the existing
replay layer to compare cost, latency, coverage and accuracy. Hard cancellation,
distributed quotas, audited billing operations, hosted identity and independent
review remain before commercial guarantees. No synthetic example establishes a
universal balance between cost, latency and accuracy.
