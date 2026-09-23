# CompleteTech LLC — JEV Learning Lab

Open `JEV_Learning_Lab.ipynb` in JupyterLab or your notebook editor.

1. Run the setup cells in order.
2. At **Setup C — enter your API key**, run the cell to open the masked input box.
3. Paste your TypeSafe API key and press Enter for live examples, or press Enter with the box
   empty to continue offline. Supplying a key selects live mode; later lesson cells can incur charges.
4. Continue through the 42 lessons. Live mode starts with a 10-attempt limit, so run a few
   lessons at a time rather than running the entire course live.

No credential is hardcoded. The key is held in the client for this kernel session and is not
written to the notebook source, environment, widget state, or the course's request/decision logs.
Run `lab.clear_api_key()` to stop live calls and drop that client's credential reference.
Use a trusted notebook/server; other code in the kernel can read its memory.

Read `README.md` for installation and full instructions. The original CompleteTech logo is
embedded in the notebook, so copying only the `.ipynb` preserves the branding.
`JEV_Learning_Lab.html` is a reading edition, not a live notebook or API-key form.

Verification: 50 code cells executed offline; 55 tests passed. The native masked-input protocol
was tested with dummy input in a real local Jupyter kernel. No live provider calls were made.
