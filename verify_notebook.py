#!/usr/bin/env python3
"""Execute the packaged notebook in a fresh Python kernel, in offline mode only."""
from __future__ import annotations
import argparse
import ast
import json
import os
from pathlib import Path
import platform
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",default="JEV_Learning_Lab.verified.ipynb")
    parser.add_argument("--overwrite",action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    try:
        import nbformat
        from nbclient import NotebookClient
    except ImportError:
        print("Install requirements-dev.txt to run the fresh-kernel verifier.",file=sys.stderr)
        return 2
    notebook = nbformat.read(root/"JEV_Learning_Lab.ipynb",as_version=4)
    nbformat.validate(notebook)
    parameters = next(c for c in notebook.cells if "parameters" in c.metadata.get("tags",[]))
    settings = {}
    for node in ast.parse(parameters.source).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            settings[node.targets[0].id] = ast.literal_eval(node.value)
    if settings.get("MODE") != "offline" or settings.get("ALLOW_LIVE_CALLS") is not False or settings.get("RUN_DSPY") is not False:
        print("Refusing execution: restore the packaged offline parameters first.",file=sys.stderr)
        return 2
    output = Path(args.output).expanduser()
    if not output.is_absolute(): output = root/output
    if output.exists() and not args.overwrite:
        print(f"Output already exists: {output}. Use --overwrite deliberately.",file=sys.stderr)
        return 2
    env = dict(os.environ)
    env.pop("TYPESAFE_API_KEY",None)
    env.pop("DSPY_MODEL",None)
    env["JEV_LAB_NONINTERACTIVE"] = "1"
    client = NotebookClient(notebook,timeout=90,kernel_name="python3",
                            resources={"metadata":{"path":str(root)}},allow_errors=False)
    client.execute(env=env)
    errors = [o for c in notebook.cells if c.cell_type=="code" for o in c.outputs if o.output_type=="error"]
    if errors: raise RuntimeError("Unexpected cell error after execution")
    report_cell = next(c for c in notebook.cells if "run-report" in c.metadata.get("tags",[]))
    report = json.loads("".join(o.text for o in report_cell.outputs if o.output_type=="stream"))
    if report["mode"] != "offline" or report["live_attempts"] != 0:
        raise RuntimeError("Offline provenance verification failed")
    nbformat.write(notebook,output)
    summary = {"status":"passed","fresh_kernel":True,"python":platform.python_version(),
        "code_cells_executed":sum(c.cell_type=="code" for c in notebook.cells),
        "error_outputs":len(errors),"run_report":report,
        "live_provider_inference_tested":False,"interactive_key_entry_skipped":True,"optional_dspy_tested":False,
        "optional_official_sdk_tested":False}
    (root/"execution-report.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
    print("Verified notebook:",output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
