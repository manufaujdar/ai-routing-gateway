# EquiRoute — company design

Prepared 3 October 2026. **Working name and proposed business; not an incorporated
entity, launched service, or validated performance claim.** Name/domain/trademark
availability has not been checked. This company design builds on AI Gateway;
the existing package name, license, and interfaces remain unchanged.

## The company in one sentence

EquiRoute helps AI application teams choose and continuously verify the least
expensive way to complete a task within their quality, latency, and data policies.

The product is an **evaluation-backed decision layer** over customer-owned model
providers and gateways. Its central output is a decision receipt: what was
eligible, why a route was selected, what it cost, whether it worked, and how
strong the evidence is. A routed result can be a model response, deterministic
operation, verified cache hit, approved tool workflow, or explicit abstention.

There is no universally perfect cost–latency–accuracy balance. We propose a
workload-specific feasible frontier, with business constraints chosen by the
customer and tested on held-out outcomes. The design must earn its overhead.

## Read the design

| Artifact | Decision it supports |
| --- | --- |
| [Evidence review](EVIDENCE.md) | What papers and competitors actually establish |
| [Repository review](REPOSITORY_REVIEW.md) | What to reuse, pin, or build; current local gaps |
| [Architecture](ARCHITECTURE.md) | Interfaces, optimization, controls, backup methods |
| [Evaluation and roadmap](EVALUATION_AND_ROADMAP.md) | How to prove value and sequence delivery |
| [Agent operating model](AGENT_OPERATING_MODEL.md) | Company roles, runtime components, handoffs |
| [Example policy](policy.example.json) | Illustrative configuration, not a supported API |
| [Offline experiment](experiments/tradeoffs.py) | Reproduce the illustrative economics below |
| [Validation record](VALIDATION.md) | Checks actually performed and remaining gaps |

## Initial customer and problem

**Proposed first customer:** a B2B software team running recurring document
extraction or support-assistance tasks with machine-checkable fields, some human
labels, and enough inference volume for savings to exceed integration costs.
Buyer: head of engineering or AI platform lead; daily user: application engineer;
co-owner: finance/operations. These are hypotheses, not customer interview findings.

Start with bounded text tasks. A missing invoice field or invalid structured
response can be checked more credibly than the broad promise of judging every
answer's truth. Sensitive deployments require customer-controlled execution and
an approved data policy. Coding workflows are a second market once execution
sandboxes and representative tests exist.

The first offer is a **routing assessment and controlled pilot**:

1. Import customer-approved labels and aggregate usage into their environment.
2. Measure their current production policy and a small candidate model pool.
3. Show the quality–cost frontier and latency violations, including router overhead.
4. Offer an auditable policy in decision-only shadow mode.
5. Activate only after the agreed evidence gates; retain instant rollback.

Initial product surfaces: Python decision SDK, gateway adapter, replay CLI, and
exportable evidence report. A hosted dashboard is later and justified by operator
needs, not required for the first useful product.

## Why this could become a company

The market already has provider aggregation, learned routing, adaptive routers,
replay, and multi-model orchestration. We cannot claim those as unique. The
[evidence review](EVIDENCE.md) documents especially close overlap with LiteLLM,
Not Diamond, and vLLM Semantic Router.

Our **differentiation hypothesis** is the operational package around customer
outcomes: calibrated quality by workflow, honest savings attribution, budget
reservations across every attempt, deadline-aware escalation, model-change
qualification, and customer-owned evidence. The proposed moat is accumulated
evaluation know-how and integration reliability; it is not a secret weighted sum
or an assumed right to pool private customer data.

Potential demand comes from model churn, growing agent workflow costs, opaque
quality regressions after cost cuts, and difficulty reconciling invoices to
successful work. Demand and willingness to pay remain untested.

## Business model and incentives

Propose an open decision SDK with paid evaluation operations, managed policy
delivery, enterprise support, and private deployment support. Preserve the
existing MIT release; future commercial packaging needs a separate decision.
Prefer subscription plus explicit evaluation usage to a markup on model spend,
which rewards the vendor when customers spend more. Customers keep provider keys
and contracts. Publish any referral economics before they influence procurement.

Do not set a price from competitor marketing. During discovery, test a fixed-fee
pilot, a recurring platform fee, and a private-deployment service tier. A usable
pricing ceiling is the customer's conservatively measured monthly value, after
model charges, evaluation overhead, integration amortization, and operator time.
Contribution margin must subtract our infrastructure, support, and labeling costs.

Illustrative arithmetic only: a $10,000 monthly baseline and 20% gross reduction
produce $2,000 gross savings. Subtract $300 evaluation/operations, $500 subscription,
and $500 monthly integration amortization: customer net value is $700/month.
At $1,000 baseline spend, the same fixed costs overwhelm a 20% reduction. This is
why the initial customer must have meaningful volume or valuable quality gains.

## What “balanced” means in practice

The included synthetic experiment assumes fast, middle, and strong routes plus
two verifier settings. At a 92% quality floor and 2-second deadline, only the
middle route meets both modeled constraints. At a 95% floor and 5-second deadline,
the good-verifier cascade is cheaper than the strong route. A poor verifier saves
tokens but misses the quality floor. These invented inputs demonstrate decisions;
they do not estimate any real model's quality, price, or speed.

## Boundaries and founder decisions

The design and agent contracts are created locally. Production implementation,
customer validation, legal formation, paid experiments, and launch remain future
work. The minimum founder decisions for a pilot are target workflow, recruited
design partners, acceptable quality loss, deadline, approved data boundary, and
experiment budget. No country, funding amount, employees, or legal structure is
assumed.

Success is a repeatable improvement over a customer's actual baseline. If a static
route or existing gateway achieves the same result with lower total ownership
cost, recommend it. That result would narrow EquiRoute toward evaluation and
policy assurance rather than justify building another routing engine.

Implementation follow-through: [router redesign and research decisions](../ROUTER_REDESIGN.md).
The company blueprint remains broader than the implemented alpha routing layers.
