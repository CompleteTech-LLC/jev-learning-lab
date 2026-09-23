"""Original, dependency-free teaching runtime. Offline fixtures are NOT inference."""
from __future__ import annotations
import copy
import hashlib
import json
import math
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any, Callable

MODEL = "jev-1.13.0"
POLICY_VERSION = "jev-learning-lab/1.1"


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def noul(instructions: str) -> dict:
    return {"type": "noul", "instructions": instructions}


def choice(instructions: str, options: dict[str, Any]) -> dict:
    return {"type": "choice", "instructions": instructions, "criteria": options}


def score(instructions: str, levels: list[str]) -> dict:
    return {"type": "score", "instructions": instructions, "criteria": levels}


def finite_number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def probability(value: Any) -> bool:
    return finite_number(value) and 0 <= value <= 1


def validate_questions(state: Any, questions: dict) -> None:
    if not isinstance(state, (str, dict, list)):
        raise ValueError("State must be text, an object, or an array.")
    if not isinstance(questions, dict) or not questions:
        raise ValueError("A nonempty question mapping is required.")
    for qid, q in questions.items():
        if not isinstance(qid, str) or not qid or not isinstance(q, dict):
            raise ValueError("Invalid question ID or question object.")
        if not isinstance(q.get("instructions"), str) or not q["instructions"].strip():
            raise ValueError("This tutorial requires explicit text instructions.")
        kind = q.get("type")
        if kind == "choice":
            options = q.get("criteria")
            if not isinstance(options, dict) or not 2 <= len(options) <= 255:
                raise ValueError("Tutorial Choice questions require 2–255 options.")
            if any(not isinstance(k, str) or not k for k in options):
                raise ValueError("Choice keys must be nonempty strings.")
        elif kind == "score":
            if not isinstance(q.get("criteria"), list) or not 2 <= len(q["criteria"]) <= 10:
                raise ValueError("Score requires 2–10 descriptive levels.")
        elif kind != "noul":
            raise ValueError("Unknown primitive.")
    # These are LOCAL conservative byte limits, NOT the provider's token limits.
    state_bytes = len(canonical(state).encode("utf-8"))
    longest = max(len(canonical(q).encode("utf-8")) for q in questions.values())
    if state_bytes + longest > 80_000:
        raise ValueError("Local state + longest-question byte budget exceeded.")
    if len(canonical({"state": state, "questions": questions}).encode("utf-8")) > 120_000:
        raise ValueError("Local request byte budget exceeded.")


def validate_response(questions: dict, response: dict) -> dict:
    """Validate the documented wire contract; never invent missing values."""
    if not isinstance(response, dict) or not isinstance(response.get("model"), str):
        raise ValueError("Missing response model provenance.")
    answers = response.get("answers")
    if not isinstance(answers, dict) or set(answers) != set(questions):
        raise ValueError("Missing or unexpected answer IDs.")
    result = copy.deepcopy(response)
    for qid, q in questions.items():
        a = result["answers"][qid]
        if not isinstance(a, dict) or a.get("type") != q["type"]:
            raise ValueError("Answer type mismatch.")
        if q["type"] == "noul":
            if not probability(a.get("noul")):
                raise ValueError("Invalid Noul probability.")
            continue
        if not probability(a.get("confidence")):
            raise ValueError("Invalid or missing Choice/Score confidence.")
        p = a.get("probabilities")
        if not isinstance(p, dict):
            raise ValueError("Missing probability distribution.")
        p = {str(k): v for k, v in p.items()}
        expected_keys = (set(q["criteria"]) if q["type"] == "choice"
                         else {str(i) for i in range(len(q["criteria"]))})
        if set(p) != expected_keys or not all(probability(v) for v in p.values()):
            raise ValueError("Invalid distribution keys or probabilities.")
        if not math.isclose(sum(p.values()), 1, abs_tol=1e-4):
            raise ValueError("Probabilities do not sum to one.")
        a["probabilities"] = p
        if q["type"] == "choice":
            selected = a.get("choice")
            if selected not in p or p[selected] + 1e-4 < max(p.values()):
                raise ValueError("Choice is not a maximum-probability option.")
        else:
            expected_score = sum(int(k) * v for k, v in p.items())
            if (not finite_number(a.get("score"))
                or not 0 <= a["score"] <= len(q["criteria"]) - 1
                or not math.isclose(a["score"], expected_score, abs_tol=0.011)):
                raise ValueError("Score does not match its probability-weighted level.")
            legend = a.get("legend")
            expected_legend = {str(i): v for i, v in enumerate(q["criteria"])}
            if not isinstance(legend, dict) or {str(k): v for k, v in legend.items()} != expected_legend:
                raise ValueError("Missing or mismatched Score legend.")
    return result


# fx_* functions manufacture AUTHOR-WRITTEN fixtures, never model predictions.
# Their confidence numbers are illustrative, not a reconstruction of vendor math.
def fx_noul(p: float) -> dict:
    return {"type": "noul", "noul": p}


def fx_choice(q: dict, selected: str, p: float = 0.94, confidence: float = 0.85) -> dict:
    options = list(q["criteria"])
    if selected not in options:
        raise ValueError("Fixture selected an unknown option.")
    rest = (1 - p) / (len(options) - 1)
    return {"type": "choice", "choice": selected, "confidence": confidence,
            "probabilities": {k: p if k == selected else rest for k in options}}


def fx_score(q: dict, probabilities: list[float], confidence: float = 0.85) -> dict:
    if len(probabilities) != len(q["criteria"]):
        raise ValueError("Fixture length mismatch.")
    return {"type": "score", "score": sum(i * p for i, p in enumerate(probabilities)),
            "confidence": confidence,
            "probabilities": {str(i): p for i, p in enumerate(probabilities)},
            "legend": {str(i): v for i, v in enumerate(q["criteria"])}}


class TutorialLab:
    """Explicit fixture/live modes, bounded attempts, validated answers, provenance.

    Live mode uses the documented HTTP API using the Python standard library.
    It has NO dependency on the optional SDK. It never executes suggested actions.
    """
    def __init__(self, mode: str = "offline", allow_live: bool = False,
                 max_live_calls: int = 10, model: str = MODEL):
        if mode not in {"offline", "live"}:
            raise ValueError("Mode must be offline or live.")
        if mode == "live" and not allow_live:
            raise PermissionError("Set ALLOW_LIVE_CALLS=True explicitly.")
        if type(max_live_calls) is not int or max_live_calls < 1:
            raise ValueError("max_live_calls must be a positive integer.")
        self.mode, self.model = mode, model
        self.max_live_calls, self.live_attempts = max_live_calls, 0
        self.records: list[dict] = []
        self.requests: list[dict] = []  # In-memory teaching visibility, no credentials.
        # None allows the advanced environment-variable path; "" explicitly clears it.
        self._session_api_key: str | None = None

    def set_api_key(self, key: str) -> None:
        """Keep a validated-format key only in this client; do not authorize live calls."""
        if not isinstance(key, str):
            raise ValueError("API key must be text.")
        key = key.strip()
        if (not key or len(key) > 4096 or not key.isascii()
                or any(c.isspace() or ord(c) < 33 or ord(c) == 127 for c in key)):
            raise ValueError("API key is empty or contains unsupported characters.")
        self._session_api_key = key

    def clear_api_key(self) -> None:
        """Forget this client's key and stop further live calls; do not reset accounting."""
        self._session_api_key = ""
        self.mode = "offline"

    def _post(self, payload: dict) -> dict:
        key = (self._session_api_key if self._session_api_key is not None
               else os.environ.get("TYPESAFE_API_KEY", "")).strip()
        if not key or any(c.isspace() or ord(c) < 33 or ord(c) == 127 for c in key) or not key.isascii():
            raise RuntimeError("Use the masked API-key box in Setup C, or set TYPESAFE_API_KEY outside the notebook.")
        req = urllib.request.Request(
            "https://api.typesafe.ai/v1/systemone",
            data=canonical(payload).encode("utf-8"), method="POST",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read(4_000_001)
                if len(data) > 4_000_000:
                    raise ValueError("Response exceeded local byte budget.")
                return json.loads(data)
        except urllib.error.HTTPError as exc:
            # No response bodies, secrets, request text, or authorization headers.
            raise RuntimeError(f"TypeSafe HTTP {exc.code}; stopped, no fixture fallback.") from None
        except (urllib.error.URLError, TimeoutError):
            raise RuntimeError("TypeSafe connection/timeout failure; stopped, no fixture fallback.") from None

    def ask(self, case: str, state: Any, questions: dict, fixture: dict | None = None) -> dict:
        validate_questions(state, questions)
        payload = {"model": self.model, "state": copy.deepcopy(state),
                   "questions": copy.deepcopy(questions)}
        request_hash = digest(payload)
        source = "offline_fixture" if self.mode == "offline" else "live_api"
        start = time.perf_counter()
        entry = {"case": case, "source": source, "request_sha256": request_hash,
                 "requested_model": self.model, "question_count": len(questions),
                 "request_bytes": len(canonical(payload).encode("utf-8")),
                 "policy_version": POLICY_VERSION}
        try:
            if self.mode == "offline":
                if fixture is None:
                    raise ValueError("Offline mode needs an explicit author-written fixture.")
                raw = {"model": "offline-fixture/v1", "answers": copy.deepcopy(fixture), "usage": None}
            else:
                if self.live_attempts >= self.max_live_calls:
                    raise RuntimeError("Live call budget reached. Inspect usage before increasing it.")
                self.live_attempts += 1
                # Fixture/expected labels are NEVER part of the wire request.
                raw = self._post(payload)
                if raw.get("model") != self.model:
                    raise ValueError("Returned model differs from the pinned requested version.")
            result = validate_response(questions, raw)
            result.update({"source": source, "case": case, "request_sha256": request_hash})
            entry.update({"status": "ok", "resolved_model": result["model"],
                          "usage": result.get("usage"), "answers": copy.deepcopy(result["answers"])})
            return result
        except Exception as exc:
            entry.update({"status": "error", "error_type": type(exc).__name__, "usage": None})
            raise
        finally:
            entry["elapsed_ms"] = round((time.perf_counter() - start) * 1000, 3)
            entry["timing_kind"] = "local_fixture_overhead" if self.mode == "offline" else "client_observed_request"
            self.records.append(entry)
            self.requests.append(payload)


def show(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False))


def chosen(result: dict, question_id: str, minimum_confidence: float = 0.7,
           minimum_probability: float = 0.7) -> str | None:
    a = result["answers"][question_id]
    if a["type"] != "choice":
        raise ValueError("chosen() requires Choice.")
    if a["confidence"] < minimum_confidence or a["probabilities"][a["choice"]] < minimum_probability:
        return None
    return a["choice"]


def expect_raises(error_type: type[Exception], operation: Callable[[], Any]) -> None:
    try:
        operation()
    except error_type:
        return
    raise AssertionError(f"Expected {error_type.__name__}")


def prompt_for_api_key(client: TutorialLab, reader: Callable[[str], str] | None = None) -> str:
    """Use a native masked prompt, not a saved source cell or serializable widget trait.

    Supplying a key is explicit opt-in to later live lesson calls. This function
    makes no network request and never resets the ledger or attempt budget.
    A custom reader is only a test seam; normal callers use getpass.
    """
    import getpass
    import warnings
    client.clear_api_key()  # Cancellation or malformed input must leave calls disabled.
    entered = None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            entered = (reader or getpass.getpass)(
                "TypeSafe API key (LIVE requests; charges may apply) — Enter for OFFLINE: "
            )
        if not isinstance(entered, str):
            raise ValueError("Expected text from the masked input.")
        if not entered.strip():
            print("OFFLINE — no key stored. All lessons use authored fixtures.")
            return "offline"
        client.set_api_key(entered)
        client.mode = "live"
        print("LIVE selected — key held in this kernel session; input is not written to notebook source.")
        print("No authentication request was made. The key has not yet been verified by TypeSafe.")
        print(f"Remaining live attempts: {max(0, client.max_live_calls - client.live_attempts)}. Run a few lesson cells at a time.")
        return "live"
    except (KeyboardInterrupt, EOFError):
        client.clear_api_key()
        print("Key entry cancelled. OFFLINE mode retained; no request was sent.")
        return "offline"
    except getpass.GetPassWarning:
        client.clear_api_key()
        print("Masked input is unavailable here. No key was read; OFFLINE mode retained.")
        print("Use a trusted Jupyter notebook frontend or the documented environment-variable path.")
        return "offline"
    except ValueError:
        client.clear_api_key()
        print("Key was not accepted: use a nonempty ASCII key without spaces or control characters.")
        print("OFFLINE mode retained. Run this cell again to retry.")
        return "offline"
    finally:
        entered = None  # Reduce references; this is not a guarantee of memory erasure.

