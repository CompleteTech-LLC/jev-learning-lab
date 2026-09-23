"""Offline contract and domain tests. No real provider calls or credentials required."""
from __future__ import annotations
import contextlib
import copy
import io
import json
import math
import os
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import patch
import urllib.error
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import jev_runtime as rt


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.q = {"answer":rt.choice("Select an option.", {"a":"first", "b":"second"})}
        self.fx = {"answer":rt.fx_choice(self.q["answer"],"a")}
        self.raw = {"model":rt.MODEL,"answers":copy.deepcopy(self.fx),"usage":None}

    def test_default_is_offline(self):
        c = rt.TutorialLab()
        r = c.ask("test", "fictional", self.q, self.fx)
        self.assertEqual(r["source"], "offline_fixture")
        self.assertEqual(c.live_attempts, 0)
        self.assertIsNone(c.records[0]["usage"])

    def test_live_requires_explicit_consent(self):
        with self.assertRaises(PermissionError): rt.TutorialLab("live")

    def test_missing_fixture_rejected(self):
        with self.assertRaises(ValueError): rt.TutorialLab().ask("test", "fictional", self.q)

    def test_choice_limit(self):
        q = {"q":rt.choice("Select", {str(i):"description" for i in range(256)})}
        with self.assertRaises(ValueError): rt.validate_questions("text",q)

    def test_score_level_limits(self):
        for n in [1,11]:
            with self.subTest(n=n), self.assertRaises(ValueError):
                rt.validate_questions("text",{"q":rt.score("Rate",["description"]*n)})

    def test_missing_answer_rejected(self):
        self.raw["answers"] = {}
        with self.assertRaises(ValueError): rt.validate_response(self.q,self.raw)

    def test_unknown_answer_id_rejected(self):
        self.raw["answers"]["extra"] = rt.fx_noul(.5)
        with self.assertRaises(ValueError): rt.validate_response(self.q,self.raw)

    def test_bad_probabilities_rejected(self):
        for p in [float("nan"),float("inf"),-.1,1.1,True]:
            raw = copy.deepcopy(self.raw)
            raw["answers"]["answer"]["probabilities"]["a"] = p
            with self.subTest(p=p), self.assertRaises(ValueError):
                rt.validate_response(self.q,raw)

    def test_distribution_total_rejected(self):
        self.raw["answers"]["answer"]["probabilities"] = {"a":.7,"b":.1}
        with self.assertRaises(ValueError): rt.validate_response(self.q,self.raw)

    def test_unknown_choice_rejected(self):
        self.raw["answers"]["answer"]["choice"] = "outside"
        with self.assertRaises(ValueError): rt.validate_response(self.q,self.raw)

    def test_nonmaximum_choice_rejected(self):
        self.raw["answers"]["answer"]["choice"] = "b"
        with self.assertRaises(ValueError): rt.validate_response(self.q,self.raw)

    def test_noul_probability_contract(self):
        q = {"q":rt.noul("Is the claim supported?")}
        for p in [True,-1,2,float("nan")]:
            with self.subTest(p=p), self.assertRaises(ValueError):
                rt.validate_response(q,{"model":rt.MODEL,"answers":{"q":rt.fx_noul(p)}})

    def test_score_expected_value_and_legend(self):
        q = {"q":rt.score("Rate",["low","medium","high"])}
        a = rt.fx_score(q["q"],[.1,.6,.3])
        raw = {"model":rt.MODEL,"answers":{"q":a}}
        self.assertAlmostEqual(rt.validate_response(q,raw)["answers"]["q"]["score"],1.2)
        bad = copy.deepcopy(raw); bad["answers"]["q"]["score"] = 2
        with self.assertRaises(ValueError): rt.validate_response(q,bad)
        bad = copy.deepcopy(raw); bad["answers"]["q"]["legend"]["0"] = "different"
        with self.assertRaises(ValueError): rt.validate_response(q,bad)

    def test_low_confidence_abstains(self):
        self.raw["answers"]["answer"]["confidence"] = .2
        self.assertIsNone(rt.chosen(self.raw,"answer"))

    def test_byte_guard(self):
        with self.assertRaises(ValueError): rt.validate_questions("x"*90000,self.q)

    def test_fixture_never_in_payload(self):
        c = rt.TutorialLab("live",True,2)
        with patch.object(c,"_post",return_value=self.raw) as post:
            c.ask("test",{"input":"fictional"},self.q,self.fx)
        payload = post.call_args.args[0]
        self.assertEqual(set(payload),{"state","questions","model"})
        self.assertNotIn("fixture",payload)
        self.assertEqual(c.records[0]["source"],"live_api")  # Mocked boundary, not actual inference.

    def test_budget_stops_without_fallback(self):
        c = rt.TutorialLab("live",True,1)
        with patch.object(c,"_post",return_value=self.raw) as post:
            c.ask("first","fictional",self.q,self.fx)
            with self.assertRaises(RuntimeError): c.ask("second","fictional",self.q,self.fx)
        self.assertEqual(post.call_count,1)
        self.assertEqual(c.records[-1]["status"],"error")

    def test_provider_error_never_becomes_fixture(self):
        c = rt.TutorialLab("live",True)
        with patch.object(c,"_post",side_effect=RuntimeError("provider unavailable")):
            with self.assertRaises(RuntimeError): c.ask("test","fictional",self.q,self.fx)
        self.assertEqual(c.records[-1]["status"],"error")
        self.assertNotIn("answers",c.records[-1])

    def test_resolved_model_mismatch_rejected(self):
        c = rt.TutorialLab("live",True)
        wrong = copy.deepcopy(self.raw); wrong["model"] = "a-different-model"
        with patch.object(c,"_post",return_value=wrong):
            with self.assertRaises(ValueError): c.ask("test","fictional",self.q,self.fx)

    def test_wire_request_shape_with_fake_transport(self):
        fake = io.BytesIO(json.dumps(self.raw).encode())
        c = rt.TutorialLab("live",True)
        with patch.dict(os.environ,{"TYPESAFE_API_KEY":"TEST-NOT-A-REAL-KEY"}), \
             patch("urllib.request.urlopen",return_value=fake) as transport:
            c.ask("test","fictional",self.q,self.fx)
        req = transport.call_args.args[0]
        self.assertEqual(req.full_url,"https://api.typesafe.ai/v1/systemone")
        self.assertEqual(req.method,"POST")
        self.assertEqual(json.loads(req.data)["questions"],self.q)
        self.assertNotIn("TEST-NOT-A-REAL-KEY",json.dumps(c.records))
        self.assertNotIn("TEST-NOT-A-REAL-KEY",json.dumps(c.requests))

    def test_http_error_is_sanitized(self):
        c = rt.TutorialLab("live",True)
        err = urllib.error.HTTPError("https://api.typesafe.ai/v1/systemone",429,
            "private response detail",{},io.BytesIO(b"private body"))
        with patch.dict(os.environ,{"TYPESAFE_API_KEY":"TEST-NOT-A-REAL-KEY"}), \
             patch("urllib.request.urlopen",side_effect=err):
            with self.assertRaises(RuntimeError) as raised: c.ask("test","text",self.q,self.fx)
        self.assertIn("429",str(raised.exception))
        self.assertNotIn("private",str(raised.exception))

    def test_invalid_key_is_not_sent(self):
        for key in ["", "key with space", "key\x00bad", "key\x7fbad"]:
            c = rt.TutorialLab("live",True)
            with patch.object(rt.os,"environ",{"TYPESAFE_API_KEY":key}), \
                 patch("urllib.request.urlopen") as transport:
                with self.assertRaises(RuntimeError): c.ask("test","text",self.q,self.fx)
                transport.assert_not_called()


class NotebookDomainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = json.loads((ROOT/"JEV_Learning_Lab.ipynb").read_text(encoding="utf-8"))
        cls.cells = raw["cells"]
        cls.g = {}
        try:
            import matplotlib.pyplot as plt
            plotting = patch.object(plt,"show",lambda:None)
        except ImportError:
            plotting = contextlib.nullcontext()
        # Refuse outbound socket connections while executing all notebook code.
        # Plotting is optional; an Agg warning in this non-Jupyter test runner is ignored.
        with patch.dict(os.environ,{"JEV_LAB_NONINTERACTIVE":"1"}), plotting, contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings(), \
             patch.object(socket.socket,"connect",side_effect=AssertionError("Network disabled in offline tests")), \
             patch("urllib.request.urlopen",side_effect=AssertionError("HTTP disabled in offline tests")):
            warnings.simplefilter("ignore")
            for index,cell in enumerate(cls.cells):
                if cell["cell_type"] == "code":
                    exec(compile("".join(cell["source"]),f"notebook-cell-{index}","exec"),cls.g)

    def test_complete_offline_run(self):
        self.assertEqual(self.g["run_report"]["curriculum_lessons"],42)
        self.assertEqual(self.g["lab"].live_attempts,0)
        self.assertFalse(self.g["RUN_DSPY"])
        self.assertTrue(all(x["source"]=="offline_fixture" for x in self.g["lab"].records))
        self.assertTrue(all(x["status"]=="ok" for x in self.g["lab"].records))

    def test_runtime_is_self_contained(self):
        embedded = next("".join(c["source"]) for c in self.cells if "runtime" in c.get("metadata",{}).get("tags",[]))
        self.assertEqual(embedded.strip(),(ROOT/"jev_runtime.py").read_text().strip())

    def test_tictactoe_reference_draw(self):
        self.assertEqual(self.g["ttt_value"](tuple("........."),"X"),0)

    def test_tictactoe_replay_after_json_roundtrip(self):
        episode = self.g["ttt_episode"]
        restored = json.loads(json.dumps(episode["trace"]))
        self.assertEqual(self.g["replay_ttt"](restored),episode["board"])

    def test_tictactoe_rejects_wrong_turn(self):
        with self.assertRaises(ValueError): self.g["ttt_apply"](tuple("........."),0,"O")

    def test_2048_no_double_merges(self):
        self.assertEqual(self.g["merge_line"]([2,2,2,2]),([4,4,0,0],8))
        self.assertEqual(self.g["merge_line"]([4,4,8,0]),([8,8,0,0],8))

    def test_checkers_mandatory_complete_capture(self):
        turns = self.g["checker_turns"]({(2,1):"r",(3,2):"b",(5,4):"b",(2,5):"r"},"r")
        self.assertEqual(len(turns),1)
        self.assertEqual(len(turns[0]["captured"]),2)

    def test_checkers_crowning_ends_capture(self):
        turns = self.g["checker_turns"]({(5,0):"r",(6,1):"b",(6,3):"b"},"r")
        self.assertEqual(len(turns),1)
        self.assertEqual(len(turns[0]["captured"]),1)
        self.assertTrue(turns[0]["promotes"])

    def test_stale_world_rejected(self):
        self.assertEqual(self.g["authorize_toy_action"](self.g["proposal"],self.g["changed"])["reason"],"stale_snapshot")

    def test_dependency_cycle_detected(self):
        edges = [{"subject":"A","predicate":"depends_on","object":"B"},
                 {"subject":"B","predicate":"depends_on","object":"A"}]
        self.assertTrue(self.g["dependency_cycle"](edges))
        self.assertFalse(self.g["dependency_cycle"](edges[:1]))

    def test_review_cannot_authorize(self):
        self.assertFalse(self.g["review_decision"]["authorized"])
        self.assertEqual(self.g["review_verdict"](True,None)["verdict"],"unavailable")
        self.assertEqual(self.g["review_verdict"](False,None)["verdict"],"reject")

    def test_review_threshold_rejected(self):
        for value in [True,.3,1.2,float("nan")]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.g["review_verdict"](True,None,value)

    def test_graph_retraction(self):
        self.assertEqual(self.g["remaining_edges"],[])
        self.assertEqual(len(self.g["compiled"]),1)

    def test_tamper_detection(self):
        self.assertTrue(self.g["verify_chain"](self.g["receipt_chain"],self.g["trusted_demo_anchor"]))
        self.assertFalse(self.g["verify_chain"](self.g["tampered"],self.g["trusted_demo_anchor"]))

    def test_metrics_missing_is_not_negative(self):
        m = self.g["binary_metrics"]([1,0,1],[1.0,0.0,None])
        self.assertEqual(m["valid"],2)
        self.assertEqual(m["unavailable"],1)
        self.assertEqual(m["brier"],0)
        self.assertEqual(m["accuracy"],1)

    def test_no_accepted_cases_has_undefined_risk(self):
        m = self.g["risk_coverage"]([1,0],[.6,.4],.99)
        self.assertEqual(m["accepted"],0)
        self.assertIsNone(m["selective_risk"])

    def test_no_forbidden_tool_selected(self):
        self.assertNotIn("shell",self.g["eligible"])
        self.assertNotEqual(self.g["selected_tool"],"shell")

    def test_capstone_never_executes(self):
        self.assertFalse(self.g["capstone_receipt"]["authorized"])
        self.assertFalse(self.g["capstone_receipt"]["executed"])

    def test_synthetic_values_not_sent_as_gold(self):
        for payload in self.g["lab"].requests:
            self.assertEqual(set(payload),{"model","state","questions"})
            if isinstance(payload["state"],dict):
                self.assertNotIn("gold",payload["state"])
                self.assertNotIn("label",payload["state"])
                self.assertNotIn("fixture",payload["state"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
