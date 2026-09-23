<a id="sources"></a>
## Sources and adaptation notes
**Documentation checked: 23 September 2026.** Links identify the original technical sources;
this notebook's authored fixture values and fictional examples are not extracted vendor results.
The notebook intentionally avoids presenting historical repository measurements as new findings.

### Official TypeSafe sources
[Documentation index](https://docs.typesafe.ai/llms.txt) ·
[Introduction](https://docs.typesafe.ai/introduction) ·
[State](https://docs.typesafe.ai/concepts/state) ·
[Question types](https://docs.typesafe.ai/primitives) ·
[Choice](https://docs.typesafe.ai/primitives/choice) ·
[Score](https://docs.typesafe.ai/primitives/score) ·
[Noul](https://docs.typesafe.ai/primitives/noul) ·
[Confidence](https://docs.typesafe.ai/confidence) ·
[Models and limits](https://docs.typesafe.ai/models) ·
[HTTP API](https://docs.typesafe.ai/api) ·
[Model limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13) ·
[Python client](https://docs.typesafe.ai/sdk/python/api/clients/sync) ·
[Python SDK changelog](https://docs.typesafe.ai/sdk/python/changelog)

Related vendor cookbooks:
[Pre-parsed value extraction](https://docs.typesafe.ai/cookbooks/pre_parsed_value_extraction_cookbook),
[Entity alignment](https://docs.typesafe.ai/cookbooks/entity_alignment),
[RAG passage classification](https://docs.typesafe.ai/cookbooks/classifying_rag_passages),
[Citation checking](https://docs.typesafe.ai/cookbooks/citation_check),
[Hierarchical classification](https://docs.typesafe.ai/cookbooks/hierarchical_classification), and
[Speculative fan-out](https://docs.typesafe.ai/patterns/fan-out).

### Prior projects used to establish context, not copied wholesale
| Project | What this course revisits | Scope boundary |
|---|---|---|
| [jev-harness](https://github.com/CompleteDotTech/jev-harness) | Narrow proposal review, evidence-only decisions, routing, bound receipts | Independent community work; no host execution implemented here |
| [jev-factorio-agent](https://github.com/CompleteDotTech/jev-factorio-agent) | Macro skills, stable goals, candidate filtering, observations, verification | Original toy simulations; no RCON, native save, or verified rocket launch |
| [paper-package](https://github.com/CompleteDotTech/paper-package) | Entity/relation judgments, question comparison, reproducible evidence | Does not rerun or restate its empirical datasets and results |
| [DSPy](https://github.com/stanfordnlp/dspy) | Candidate-question proposal using a separate generative model | Optional API recipe; not installed or live-tested during packaging |

**Prior user artifacts consulted:** `jev-plc-conveyor.json` (snapshot and latch/reset semantics),
`jev_manipulation_classifier.py` (language signals and missing-context boundaries),
`jev-2048-README.md` (separate boards and matched randomness), `README(9).md` (Checkers),
and `README(10).md` (Dots & Boxes). Earlier discussions supplied the intent for Tic-Tac-Toe,
Connect Four, encoded state, the 311-style heatmap, code-review memory, and cross-game agents.
Those original artifacts are not embedded or redistributed here. The lessons are original,
reduced-scope educational adaptations, not a claim that every feature of those apps is present.

**New work in this course:** next-question onboarding, active-learning selection, drift alerts,
metamorphic tests, cost-aware schema selection, and an incident-copilot capstone. Some extend
prior themes; they are labeled as extensions rather than falsely attributed to earlier experiments.

**Documentation drift:** A future service or SDK change may require updating the adapter.
Recheck the official contract, pin a supported version, rerun the contract tests, and record the
change. Never change the model under an unfinished comparison and pool it as the same treatment.

## CompleteTech branding refresh — 23 September 2026

Original logo and brand profile verified against `CompleteTech-LLC/build-ai-skills-in-6-steps`
through the connected GitHub reader. Original logo bytes were recovered from the user's saved
`skill-maker-skill.zip` distribution and match Git blob
`1325b5a410c5dc4c8af75fce515a188714262c25` and SHA-256
`69d3535a5b677a56d4ff89e9eccbe94525f8690c426ff75c4d56fbeb3da3e3d1`.
Profile source blob: `d4c1b199c11f635fd164efe54dc9e1436a917a17`.

- https://github.com/CompleteTech-LLC/build-ai-skills-in-6-steps/blob/main/assets/brand-profile.json
- https://github.com/CompleteTech-LLC/build-ai-skills-in-6-steps/blob/main/assets/completetech_logo.jpg
- https://github.com/CompleteTech-LLC/agentic-delivery-skill/blob/main/BRAND_ASSETS.md
- https://docs.python.org/3/library/getpass.html
- https://jupyter-client.readthedocs.io/en/stable/messaging.html#messages-on-the-stdin-router-dealer-channel
- https://ipywidgets.readthedocs.io/en/stable/examples/Widget%20List.html#Password

The key prompt uses the Jupyter stdin password flag. No `ipywidgets` or anywidget dependency
is added. Branding is packaging/UI, not a change to the lesson's model fixtures.
