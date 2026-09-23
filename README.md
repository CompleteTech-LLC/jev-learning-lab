# JEV Learning Lab
## From typed decisions to auditable agents

A self-contained Jupyter course prepared for the CompleteTech LLC learning collection.
42 lessons, 50 executable code cells, 42 exercises with hints, and an end-to-end capstone.
The notebook adapts earlier JEV work into original teaching examples and adds new applications.

**Open `JEV_Learning_Lab.ipynb` to learn and run code. Open `JEV_Learning_Lab.html` to read
its saved outputs without installing Jupyter.** The notebook does not depend on adjacent Python
files; the helper runtime is embedded and also supplied separately for reuse.

## CompleteTech branding

The original CompleteTech logo, blue/navy palette, and “Innovation at Every Integration”
tagline are applied. The notebook embeds the logo directly; it remains standalone.
Source hashes and asset-rights notes are in `BRANDING.md` and `assets/brand-profile.json`.

## Start offline

The distributed notebook is already executed. No API key is needed to read it or run its default
mode. On Windows, macOS, or Linux with Python 3.10 or newer:

```sh
python -m venv .venv
```

Activate the environment using the command for your shell:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```sh
# macOS / Linux
source .venv/bin/activate
```

Then install the notebook tools and open the course:

```sh
python -m pip install -r requirements.txt
python -m jupyterlab JEV_Learning_Lab.ipynb
```

An existing Jupyter or VS Code notebook environment also works. Use **Restart Kernel and Run
All** for the complete progression. At Setup C, press Enter in the masked box to stay offline. The runtime and examples use Python's standard library;
Matplotlib is optional, and the evaluation lesson prints its numeric results without it.

## Course map

| Lessons | Focus |
|---|---|
| 01–06 | Exact code versus judgment; Choice, Noul, Score; batching and abstention |
| 07–18 | Extraction, ITSM, onboarding, Discord moderation, language signals, RAG, citations, CMDB matching, fictional 311 reports, injection boundaries, encoded state, hierarchical labels |
| 19–25 | PLC scans and recovery; Tic-Tac-Toe including a full match and replay; Connect Four, Dots & Boxes, 2048, and Checkers |
| 26–29 | Card-combat planning; Factorio macro skills, persistent goals and productive waiting; cross-game freshness checks |
| 30–36 | Research graphs, constraints and retraction; code review; context paging; caching; bounded retries; audit receipts and replay |
| 37–42 | Evaluation; question-formulation comparison and optional DSPy; active learning; drift monitoring; cost-aware tool selection; robustness tests; incident-copilot capstone |

Every lesson states the learning objective, the model/code boundary, a runnable example, an
exercise, and a solution direction. A linked table of contents and source notes are included.

## What offline results mean

**All saved model-shaped answers are author-written fixtures, not live JEV responses.** They
exercise schemas, policies, games, and evaluation plumbing. They do not measure JEV accuracy,
latency, calibration, cost, native gameplay, robustness, or optimization gains. Some fixtures use
a deterministic reference policy, explicitly labeled as such. Changing input text does not make
the fixture intelligent. Use controlled live experiments to test semantic behavior.

No Discord action, GitHub change, machine actuation, Factorio connection, external game session,
resource deployment, or purchase occurs. The notebook contains reduced-scope simulations, not
complete copies of the earlier applications. The PLC material is simulation only.

## Enable deliberate live experiments

Run **Setup C — enter your API key**. A masked box appears below the cell. Paste your
TypeSafe API key and press Enter. Providing a key explicitly selects live mode for the lesson
cells you run next; charges may apply. Press Enter with the box empty for offline learning.
No API request is sent during key entry, and its local format check does not authenticate it.

The key is held only in the `lab` client's kernel memory. It is not copied into a source cell,
widget state, environment variable, or request/decision ledger. No widget package is needed.
Use a trusted Jupyter server (HTTPS when remote); code in the same kernel can read memory.
To clear this client's key and disable live calls, run `lab.clear_api_key()`. Restart the kernel
to discard the session; this is not guaranteed secure memory erasure.

The default cap is 10 attempts. Increase `lab.max_live_calls` only after reviewing usage; it is
not a dollar cap. Run a few lessons rather than running the entire course live immediately.

Advanced environment-variable use remains supported: provide `TYPESAFE_API_KEY` outside the
notebook, set `MODE="live"` and `ALLOW_LIVE_CALLS=True` in Setup A, and **skip Setup C**.
Never paste a key into Python source. For unattended offline execution, set
`JEV_LAB_NONINTERACTIVE=1`; the packaged verifier does this automatically.

The adapter uses the documented TypeSafe HTTP endpoint directly; the official SDK is not needed.
It requests the pinned `jev-1.13.0` model and checks the returned model. Recheck current supported
versions before future use. Documentation was checked on 23 September 2026.

Run a few lessons and inspect usage before expanding the request budget. A complete live run
would exceed the initial budget and its request count can change with model decisions. The
budget limits attempted requests, not money. There is no invented price or token estimate.
A failed live call **never silently switches to a fixture**. For live use after starting offline,
run Setup C again; its prompt changes the existing client without resetting the ledger or budget.
Changing the parameter variable alone does not reconfigure an already-created client. Do not enable Run All on private data without reviewing each egress path.

Live judgments can disagree with the examples. The notebook reports model agreement rather
than asserting that a model must produce an expected prediction. Assertions check exact host
behavior. The illustrative confidence/probability thresholds are not production calibration.

The optional SDK recipe is documentation-checked but was not installed or live-tested during
packaging. `requirements-sdk-optional.txt` records that reference version. Optional DSPy uses a
**separate generative model** configured through `DSPY_MODEL`, its own credentials, and a separate
provider bill. It is disabled by default and is not a completed MIPRO/GEPA integration. JEV is the
typed evaluator, not assumed to be a generic text-generation provider.

## Verify and inspect evidence

See `verification.json` for the exact Python version and fresh test counts for this refresh. Run the built-in unittest suite:

```sh
python -m unittest discover -s tests -v
```

The domain tests execute all notebook code with outbound socket and HTTP calls blocked, and
suppress only plot display in that non-Jupyter runner. Separate transport tests use a fake HTTP
response, never the provider. The executed notebook includes the actual rendered plot.

For a fresh-kernel execution and an independent output notebook:

```sh
python -m pip install -r requirements-dev.txt
python verify_notebook.py
```

The verifier refuses non-offline parameter settings and refuses to overwrite an existing output
unless `--overwrite` is explicitly supplied. It writes `execution-report.json` and
`JEV_Learning_Lab.verified.ipynb` by default. Review the script before running altered notebooks.

Packaging evidence is recorded in `test-report.txt`, `execution-report.json`, and
`verification.json`. Interactive password entry is skipped in the automated full run and tested
separately with a fake reader **and an actual local Jupyter kernel's password-input messages**.
Run `python verify_key_prompt.py` to repeat the native-input protocol check with dummy data.
No real credential or provider request is used. These checks
verify implementation mechanics, not JEV model quality or provider authentication.

## Package contents

- `JEV_Learning_Lab.ipynb`: complete executed notebook, standalone.
- `JEV_Learning_Lab.html`: readable edition with saved outputs and embedded chart.
- `jev_runtime.py`: reusable teaching HTTP/fixture adapter, validation, and credential helpers.
- `assets/completetech_logo.jpg`: original verified logo, also embedded in the notebook.
- `assets/brand-profile.json`, `assets/notebook-theme.css`, and `BRANDING.md`: identity and source notes.
- `tests/test_credentials.py`: masked-input, clearing, budget, and secret-exclusion regression tests.
- `tests/test_learning_lab.py`: contract, failure, replay, and domain tests.
- `verify_notebook.py`: fresh-kernel offline verifier.
- `verify_key_prompt.py` and `key-input-verification.json`: real Jupyter masked-input protocol check using dummy data.
- `curriculum.json`: machine-readable lesson index.
- `SOURCES.md` and `provenance.json`: source and adaptation notes.
- `execution-report.json`, `test-report.txt`, and `verification.json`: packaging evidence.
- `requirements*.txt`: notebook/development tools and optional SDK recipe.
- `MANIFEST.json`: package file hashes, excluding itself; integrity inventory, not a signature.

## Sharing and deployment boundaries

Do not share notebooks containing private request/response text. Clearing an API key is not
sufficient: clear outputs and inspect source cells, receipts, and logs too. The optional local
evidence export is off by default and refuses to overwrite an earlier export directory.

Hash chains demonstrate consistency relative to a trusted anchor, not authentication by
an untrusted author. Production authorization, storage, concurrency, revocation, egress, safety,
and compliance are host responsibilities. This course is independent community educational
material, not an official TypeSafe product or an endorsement by TypeSafe AI or DSPy.
