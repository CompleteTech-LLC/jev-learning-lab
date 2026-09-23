#!/usr/bin/env python3
"""Verify the actual Jupyter masked-input protocol with dummy input, no provider calls."""
from pathlib import Path
import json
import os
import time
from jupyter_client import KernelManager

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
DUMMY = 'JUPYTER-PROTOCOL-TEST-ONLY-NOT-A-REAL-KEY'

def collect(client, parent):
    messages = []
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        msg = client.get_iopub_msg(timeout=15)
        if msg.get('parent_header',{}).get('msg_id') != parent:
            continue
        messages.append({'type':msg['msg_type'],'content':msg['content']})
        if msg['msg_type'] == 'status' and msg['content']['execution_state'] == 'idle':
            break
    else:
        raise TimeoutError('Kernel did not return to idle.')
    if any(m['type']=='error' for m in messages):
        raise AssertionError('Kernel execution returned an error.')
    if DUMMY in json.dumps(messages):
        raise AssertionError('Dummy credential leaked to a public execution message.')
    return messages

def main():
    raw=json.loads((ROOT/'JEV_Learning_Lab.ipynb').read_text())
    key_code=''.join(next(c for c in raw['cells'] if 'api-key-entry' in c.get('metadata',{}).get('tags',[]))['source'])
    env=dict(os.environ)
    env.pop('JEV_LAB_NONINTERACTIVE',None)
    env.pop('TYPESAFE_API_KEY',None)
    km=KernelManager(kernel_name='python3')
    km.start_kernel(cwd=str(ROOT),env=env)
    client=km.client()
    client.start_channels()
    try:
        client.wait_for_ready(timeout=30)
        init=f'import sys\nsys.path.insert(0, {str(SRC)!r})\nfrom jev_runtime import *\nlab = TutorialLab()\n'
        parent=client.execute(init+key_code,allow_stdin=True)
        stdin=client.get_stdin_msg(timeout=30)
        assert stdin['msg_type']=='input_request'
        assert stdin['content']['password'] is True
        assert 'LIVE' in stdin['content']['prompt']
        client.input(DUMMY)
        first=collect(client,parent)
        parent=client.execute('assert lab.mode == "live"\nassert lab._session_api_key\nassert lab.live_attempts == 0\nassert not lab.records\nprint("live_state_verified")')
        collect(client,parent)
        # The exact same notebook cell must support blank input and clear its key.
        parent=client.execute(key_code,allow_stdin=True)
        stdin=client.get_stdin_msg(timeout=30)
        assert stdin['content']['password'] is True
        client.input('')
        second=collect(client,parent)
        parent=client.execute('assert lab.mode == "offline"\nassert lab._session_api_key == ""\nassert lab.live_attempts == 0\nprint("offline_state_verified")')
        collect(client,parent)
        report={'status':'passed','transport':'actual local Jupyter kernel stdin messages',
          'real_notebook_api_key_cell_executed':True,'password_flag_true':True,
          'dummy_key_activates_live':True,'blank_input_clears_key_and_selects_offline':True,
          'dummy_key_absent_from_public_execution_messages':True,'provider_calls':0,
          'real_api_key_used':False,'browser_frontends_tested':[]}
        (ROOT/'key-input-verification.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    finally:
        client.stop_channels()
        km.shutdown_kernel(now=True)

if __name__=='__main__':main()
