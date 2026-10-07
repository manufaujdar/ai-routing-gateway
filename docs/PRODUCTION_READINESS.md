# Production boundary assessment — 3 October 2026

Verdict: useful for offline routing and controlled internal pilots; **not ready
for an unrestricted public multi-tenant service or guaranteed accuracy, spend
and latency**. This is a builder's source review and local behavioral assessment,
not independent certification. Base revision: `1bb8ba7`.

## Will agents use it automatically?

There are three distinct components:

| Component | What invokes it | What is automatic today |
| --- | --- | --- |
| Routing library / `/v1/route` API | An application or agent submits a request | Classification, selection, configured execution, limits and telemetry for that request |
| Twelve project role skills | A compatible agent runtime selects/reads a role while handling a task | Instructions guide that active task; no resident processes are created |
| Python team planner/executor | Host application calls `TeamPlanner` / `TeamExecutor` and supplies every handler | Deterministic role selection and gate sequencing; handlers perform the actual work |

No scheduler, background calibration job, automatic model-catalog refresh or
global interception of Codex/ChatGPT calls exists in this repository. The
weekly Dependabot configuration checks dependencies; it does not operate the
router. Selection of a coding skill does not redirect the coding assistant's
underlying model traffic. Other projects and external agent installations were
not changed or audited in this assessment.

**One-time setup is required**, rather than a manual decision for each prompt:

1. Choose the consuming agent/application. Install this library there and invoke
   its configured container, or connect that application to the configured HTTP API.
2. Supply server-owned providers, allowed model catalog, versions, capabilities,
   measured prices/latencies, execution policy, budget account and tenant credentials.
   The shipped catalog is a fixture. `/ready` confirms application configuration,
   not provider health or quality. Constructing a container makes no inference call.
3. For quality-constrained use, supply representative calibration evidence and
   submit evidence-mode requests with the required floor. A trusted application
   must enforce this policy: setting `evidence_policy` alone does not prohibit
   clients from choosing weighted mode. Client-supplied allow-lists and quality
   floors are request preferences, not tenant authorization policy.
4. Have the agent inspect abstention, verification, returned model and usage;
   route uncertain or rejected results to its human/task-validation path.
   `verification.kind="form"` is not a correctness label.
5. Assign an operator to reconciliation, credential/catalog updates, dataset
   refresh and alerts. Periodic checks require an explicitly configured scheduler
   and evaluation/spending policy. None was created during this review.

Library integration point (using an already configured container):

```python
from ai_gateway import GatewayRequest

response = container.router.route(GatewayRequest(
    prompt=agent_task,
    selection_mode="evidence",
    min_quality=required_cohort_quality,
    execution_timeout_ms=10_000,
    max_output_tokens=1_000,
))
if response.metadata.get("abstained"):
    # Application-owned escalation; do not silently retry with a weaker policy.
    handle_abstention(response.decision.selection_receipt)
else:
    validate_task_result(response)  # cohort evidence does not certify this answer
```

`container`, `agent_task`, required quality and callbacks belong to the host
application. See [runtime configuration](RUNTIME_CONTROLS.md) and executable
offline examples. The default `ai-gateway` CLI uses mocks even if provider
environment variables are set; use the configured library/API for real inference.

## Reproduced and repaired in this pass

| Priority | Reproduction / risk | Repair and evidence |
| --- | --- | --- |
| P1 | `max_cost` typo was ignored and execution proceeded | API rejects unknown fields on route/provider/feedback payloads; regression confirms zero provider calls |
| P2 | A `10**400` token estimate produced HTTP 500 | Hints over 1,000,000 rejected with a client error before dispatch |
| P2 | Unknown selection mode initialized a runtime provider before validation | Literal schema validation rejects it before provider construction |
| P2 | `available="false"` was truthy; extreme finite prices generated infinite cost | Strict availability boolean and finite computed-cost validation |
| P1 deployment gap | Per-request limits did not constrain simultaneous requests | Optional `ExecutionPolicy(max_concurrent_calls=N)` shares slots across requests and council/sampling; saturation is rejected before charge reservation, with guaranteed slot release on errors |
| P2 | Valid JSON `null` in saved history crashed rendering; storage failure misreported successful routing | Shape-check saved entries, tolerate unavailable/full storage; browser reproduction then passing re-test |
| P2 | Failed request could leave a prior success visible; verification/usage were hidden | Clear stale result on submit, show failure state and execution checks/usage; history restore resets state |
| P2 claim gap | Static readiness `ready=true` could be mistaken for production certification | JSON now explicitly says `production_readiness="not_assessed"`; CLI clarifies scope |

Unknown API fields now return 422 rather than being ignored: clients relying on
extra payload fields must update. Arbitrary application metadata still belongs
in `context`. SQLite database/journal files are excluded from Git and Docker
contexts; keep operator data outside the checkout as documented.

## Where it survives, refuses, or fails

| Scenario | Observed behavior / evidence | Practical boundary |
| --- | --- | --- |
| Six baseline routes; allow-list/cost/latency filtering | Existing route/selector tests pass | English keyword baseline, no broad language/domain accuracy claim |
| Missing, stale, sparse or mismatched quality records | Evidence mode abstains; provider is not called | Requires credible independent labels and matching versions; no per-answer assurance |
| Broken/empty provider response | Bounded cascade recovers or all-failed execution raises; known charges retained | Custom adapter hidden retries remain outside measured attempt count |
| Partial council / samples | Returns documented degradation or failure; requested sample count defines majority | Correlated agreement and form checks can accept wrong answers |
| Shared budget under concurrency | Four spawned processes attempted 40 reservations of 10 micro-USD against 100; exactly 10 admitted | Local SQLite file only; no network-filesystem/distributed guarantee |
| Restart with unknown billing | Outstanding reservations survive reopen; no automatic refund | Operator reconciliation required, including token-only SDK results |
| Charge or token overrun | Actual cost preserved; token-overrun output rejected; charge breach freezes account | Cannot undo provider billing or recall already admitted calls |
| Concurrent provider saturation | Single and council calls share the configured cap; slots recover after upstream failure | Per-container/process only; no global quota, queue or ingress memory limit |
| Timeout with uncooperative synchronous caller | Late result rejected and charge recorded only after caller returns | **Fails hard wall-clock cancellation**; a hung caller can hold its slot indefinitely |
| Tenant token missing/wrong; cross-tenant feedback | Access denied; stores/accounts isolated in configured tenant mode | Default API is trusted-local; no identity lifecycle, per-user roles or feedback provenance |
| Misspelled safety/cost controls; huge estimate | Rejected before provider contact | Request-body byte/depth limits still belong at ingress; arbitrary context is not size-bounded here |
| Factually wrong but well-shaped answer | Repeated “two plus two equals five” passes form verification in a limitation test | **Fails factual correctness validation**; use a task-specific verifier and held-out evaluation |
| Obfuscated unsafe keyword | `bypass authentication` blocked; `bypass authent1cation` routes to `llm.fast` in a limitation test | **Fails semantic safety coverage**; keyword filter is not a safety firewall |
| Ambiguous task intent | “Explain a Python class diagram” routes to vision due to keyword precedence | Requires task classifier evaluation / application intent controls |
| Specialized search/vision | Mock by default; configured-provider path can require real handlers and fail closed | No bundled search/image processing or tool sandbox; execution controls reject tool dispatch |
| Browser history and storage faults | Corrupt entry ignored; storage quota warning; successful result retained; clear/restore work | Prompts and outputs persist in browser history; local console is unsuitable for sensitive data without retention changes |
| Team release / failed certification | Existing tests deny unauthorized Release and stop after failed gates | Handlers are trusted application code; object-identity checks do not prove real reviewer independence |

The limitation tests intentionally assert the observed weakness. Their passing
status documents a boundary; it does not mean the weakness is repaired.

## Route and feature review matrix

| Surface | Verification |
| --- | --- |
| `llm.fast`, `llm.reasoning`, `llm.code` | Library/API contracts; single/cascade/sample/council tests; failover and usage |
| `tool.web_search`, `tool.vision`, `blocked` | Decision-only, mock, unavailable/custom-handler and policy-rejection tests |
| `/`, `/assets/app.js`, `/assets/styles.css` | API asset tests; actual Playwright desktop/mobile interactions |
| `/health`, `/ready`, `/v1/config`, `/v1/capabilities` | Local and tenant contract tests; credential/override restrictions |
| `/v1/route`, `/v1/feedback`, `/v1/telemetry`, `/v1/policy/proposal` | Strict inputs, isolated observations, unknown feedback, no automatic promotion |
| `/docs`, `/redoc`, `/docs/oauth2-redirect`, `/openapi.json` | Framework documentation routes; tenant middleware covers all non-health paths; all listed documentation surfaces tested with and without tenant authentication |
| CLI / team roles, plan, init, validate | Existing CLI, scaffold/collision/path and gate tests; complete SDK source reviewed |
| SQLite schema and reconciliation | Thread/process admission, restart, account scope, idempotent settlement and breach tests |
| CI / package / deployment files | Pinned workflow actions and release gates inspected; loopback Compose; non-root Docker user. No deployment or remote CI run claimed |
| Background jobs | No routing/evaluation scheduler in the application; only on-request advisor reports |

## Validation and performance evidence

- 242 Python tests pass on Python 3.11.16 and 3.14.7 on macOS. Six initial
  boundary tests failed (five defects plus the missing capacity feature), then
  passed after repairs. Four-process admission is exercised by the suite.
- Ruff, `git diff --check`, 12-role validation and local release metadata checks
  pass. The static readiness audit reports no artifact findings and explicitly
  does not assess production readiness.
- Source distribution and wheel build, Twine metadata validation, isolated wheel
  imports/zero mandatory dependencies/concurrency-policy smoke, and installed CLI
  mock routing pass. No container build or remote publishing was performed.
- `scripts/measure_routing.py --requests 1000 --workers 8`: 1,000 synthetic
  decision-only operations, zero provider calls; observed p50 0.0434 ms, p95
  0.0770 ms, 0.061895 s batch time on this machine. This excludes HTTP, provider,
  ledger, real workloads and accuracy. It is not a service capacity promise.
- Browser plugin skill was unavailable; existing Playwright MCP used against
  `http://127.0.0.1:8769`. Desktop 1440×1000 and mobile 390×844. Page identity,
  nonblank content, no framework overlay, screenshots and exercised interactions
  pass. No JavaScript errors after repair; expected failed-request HTTP 400 and
  missing favicon HTTP 404 are distinct from runtime failures.
- Browser flow: load with corrupt history → route → mock execute → inspect
  metadata → impossible budget failure → verify old result hidden → inject
  storage quota error → successful result preserved → reload/restore/clear history.
  A mocked response with failed form verification and unknown dollar cost displays
  both states accurately; this is UI fixture evidence, not a provider quality test.
  Mobile has no horizontal overflow. Other browser engines, screen readers,
  authenticated browser login, live providers and sustained HTTP soak were not tested.

Screenshots are temporary local evidence at `/tmp/ai-gateway-production-desktop.png`, `/tmp/ai-gateway-production-mobile.png` and
`/tmp/ai-gateway-production-verification.png`; they are not distribution assets.
File-review evidence is in [the existing ledger](company/review-coverage.json).
The final ledger records 77/77 eligible files reviewed, 133 excluded and zero
pending, blocked, invalid or stale entries. Review covers application source,
tests, examples and operational configuration. The helper excludes `.env.example`
from hashing by filename; the public template was manually inspected.
Historical company research, installed Spec Kit/vendor instructions and unrelated
governance/design documents are excluded rather than represented as re-reviewed.
Ignored secrets, environments, caches, build outputs and database state are not
source-review targets. No portfolio-wide or independent security audit is claimed.

## Requirements before a public launch

| Owner | Required evidence / implementation |
| --- | --- |
| Product + evaluation owner | Defined workload, quality floor and latency/cost objective; authorized independent dataset; calibrated classifier and task verifier; comparison against cheapest/strongest/static policies with uncertainty and drift monitoring |
| Application/security owner | Enforced tenant route/model/quality policy; identity provisioning/rotation/revocation, TLS, per-user permissions, feedback integrity, ingress body/rate/concurrency limits and reviewed tool execution |
| Runtime/SRE owner | Cancelable execution or worker isolation, distributed quotas/circuit coordination, request idempotency, overload status/retry contract, streaming/disconnect handling if needed, provider-specific contract tests and sustained load/chaos tests |
| Billing/operator owner | Verified per-deployment charge ceilings, provider invoices, automated audited reconciliation, breach recovery, retention/backup/restore and database growth/locking strategy |
| Maintainer + independent reviewer | Locked deployment dependencies/image, vulnerability review, integration/rollback evidence, Linux/Python matrix CI on the final revision and independent release gates |

Current request failures largely share HTTP 400; clients should not blindly retry
all failures. Requests can charge again if resubmitted: whole-request idempotency
is not implemented. Circuit state, telemetry and concurrency slots are local to
each process. SQLite aggregates exposure from retained rows under a write lock;
large ledger history and multi-worker traffic need measured scaling work.

No provider spend, scheduler, integration into other projects, push or deployment
was performed. Current role: Documentation handoff after Builder self-review.
Next owner: maintainer/independent review, then the consuming application's owner
and evaluation owner. Data access, spending and external release need explicit
authorization for those concrete next steps.
