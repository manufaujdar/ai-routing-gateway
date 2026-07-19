---
name: research-ai-routing
description: Research AI routing, gateways, models, councils, agent systems, evaluation methods, and market approaches using primary sources and bounded experiments. Use when a decision depends on current external evidence, competitor or repository analysis, uncertain technical feasibility, benchmarks, or comparing multiple approaches. Do not use for settled implementation mechanics.
---

# Research AI routing

Read project context first so research answers a real decision. Use primary sources for technical
claims and current browsing for unstable information.

## Contract

- Own evidence collection, option comparison, disposable experiments, uncertainty, and recommendation.
- Remain report-only for production code. Put prototypes in an explicit temporary or experimental
  boundary and never silently promote them.
- Distinguish sourced facts, measurements, inference, and opinion.
- Never include provider keys, private prompts, or unredacted traces.

## Workflow

1. Define the decision, hypotheses, evaluation dimensions, and evidence threshold.
2. Inspect existing project work to avoid rediscovery.
3. Gather primary documentation, source repositories, and research papers; record dates and versions.
4. Run the smallest deterministic experiment that can invalidate a key assumption.
5. Compare quality, cost, latency, reliability, safety, integration effort, and lock-in.
6. State uncertainty and what new evidence could change the recommendation.

Council deliberation is eligible only for consequential ambiguity with multiple defensible options;
use project council policy and keep the R&D owner accountable for synthesis.

## Required output

Produce: decision; sources; evidence table; experiment method/results; options and trade-offs;
recommendation; confidence; limitations; and next validation step.

## Stop and escalate

Stop before paid or high-volume experiments, external writes, production data access, or accepting a
vendor claim that cannot be independently checked. Request authority or label the gap.

## Handoff

Send the evidence brief to `planner` for scope decisions or `engineer` for technical design. Include
source links, version/date, raw measurement location, and unresolved uncertainty.
