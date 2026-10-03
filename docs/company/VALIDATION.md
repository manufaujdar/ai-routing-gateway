# Validation and handoff

Date: 3 October 2026. Scope: company/research/architecture artifacts, 12 role
references and one offline synthetic economics experiment. No production routing
module or public API was changed by this task. No models/providers were called.

## Verification evidence

| Check | Actual result |
| --- | --- |
| Focused pytest: `tests/test_company_tradeoffs.py tests/test_agent_team.py` | 13 passed |
| Full repository pytest | 165 passed in 6.21 seconds on Python 3.14.7 / pytest 9.1.1 |
| `python3 scripts/validate_agent_team.py` | 12 team skills validated |
| Skill Creator `quick_validate.py` | All 12 company-linked skills passed using cached uv/PyYAML after system Python lacked PyYAML |
| Local link and example-policy check | 39 relative links resolved; 12 role references present; example remains decision-only with experimental methods and automatic promotion disabled |
| `ruff check .` | Passed at the recorded check; check-only, no formatting |
| `git diff --check` | Passed at the recorded check |
| Synthetic experiment | Reproduced all figures below without network/model calls |
| Evidence review | 9 paper records, 8 company/project comparisons, 6 pinned public repositories; inspection depth and limitations recorded |

The default Python had no pytest and this project had no usable `.venv`. Tests
used a disposable cached uv environment from the existing declared project extras;
no new repository environment or dependency declaration was added:

```sh
uv run --no-project --with '.[dev,api,openai]' python -m pytest -q
python3 scripts/validate_agent_team.py
ruff check .
git diff --check
python3 docs/company/experiments/tradeoffs.py
```

The project has no lockfile; this environment is a recorded test run, not a claim
that resolving those unpinned extras later reproduces identical dependency versions.
The experiment itself uses only the standard library.

## Synthetic experiment and its limits

All quality values, prices and latencies are invented. Each direct route includes
$0.0001 and 20 ms of illustrative decision overhead. The cheap generation costs
$0.001 and takes 400 ms; its verifier costs $0.0002 and takes 50 ms; an escalated
generation costs $0.01 and takes 2400 ms. In the example, the strong model is
assumed 98% correct **conditional on the cheap answer being rejected**. This is a
separate assumption from its 97% unconditional quality. No fitted uncertainty
intervals or actual quality guarantees are produced by the script.

```text
e = q_fast * false_reject + (1 - q_fast) * (1 - false_accept)
q_cascade = q_fast * (1 - false_reject) + e * q_strong_given_rejection
C_cascade = C_router + C_fast + C_verifier + e * C_strong
```

| Synthetic option | Correct-task probability | Expected USD/request | Modeled p95 completion | Misses 2-second deadline |
| --- | ---: | ---: | ---: | ---: |
| Fast | 85.000% | 0.001100 | 420 ms | 0% |
| Middle | 94.000% | 0.003100 | 920 ms | 0% |
| Strong | 97.000% | 0.010100 | 2420 ms | 100% |
| Cascade: false accept 5%, false reject 10% | 98.795% | 0.003575 | 2870 ms | 22.75% |
| Cascade: false accept 60%, false reject 5% | 90.795% | 0.002325 | 2870 ms | 10.25% |

The script selects middle for a 92% floor / 2-second deadline / 5% miss limit;
cascade for 95% / 5 seconds / 5%; and abstention for 99% / 2 seconds / 5%.
It tests accept-all and reject-all verifier limits, conditional rescue, invalid
probabilities, invalid distributions and how quality/deadline constraints change
the selected route. Its two-point latency distribution is deliberately simple;
it is not a load test or provider-latency forecast.

## Self-review corrections and limits

- Corrected stale competitive framing: adaptive routing, savings accounting,
  explainability, replay and multi-model control already overlap with competitors.
- Distinguished the local heuristic verifier from correctness evaluation and
  absent cost from a true zero cost.
- Made the global call cap include model judges and provider retries; a two-call
  cascade therefore needs a deterministic verifier.
- Defined hard policy constraints before soft optimization, full cost reservation,
  pending-charge handling, OOD fallback and explicit abstention.
- Kept real pilot quality, latency, savings, legal formation and brand clearance
  unverified. Proposed numerical targets are not commitments or measured results.

This was sequential research, architecture and self-review by one assistant.
There was no independent reviewer execution or production certification. Such
gates remain required for later implementation/release where project rules apply.

Concurrent unrelated Spec Kit edits appeared in `AGENTS.md`, `START_HERE.txt`,
`scripts/validate_agent_team.py`, `.specify/` and extra skill folders while work
was in progress. They were preserved; this task does not claim ownership of those
changes. The full-suite result describes the working tree at test time.

## Delivery state

Company design and all 12 company-role contracts are complete locally. The
existing team registry remains authoritative. Entry points link to this package.
No incorporation, Git commit/push, customer contact, deployment, automation or paid
inference occurred. No durable memory decision was inferred from the proposal.

Final active role: Documentation / release preparation for local artifacts.
Next owner: Manu for the proposed first market and pilot constraints, then Planner
and Engineer for the first implementation slice. No approval is needed to read or
use these local deliverables. Spending, customer data access, publication and
deployment require their ordinary explicit authorization when undertaken.
