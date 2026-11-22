"""Execute each current course notebook in a fresh kernel, preserving outputs."""
import os
import json
import time
import argparse
import subprocess
import sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parent
# Writable caches avoid dependence on user-level Jupyter/matplotlib configuration.
os.environ.setdefault('MPLCONFIGDIR', str(root / '.cache/matplotlib'))
os.environ.setdefault('IPYTHONDIR', str(root / '.cache/ipython'))
parser = argparse.ArgumentParser()
parser.add_argument('--notebook', help='Execute one exact notebook stem (for iteration)')
parser.add_argument('--inprocess', action='store_true', help='Fresh process + fresh IPython kernel per notebook; no sockets')
args = parser.parse_args()
for key in ['MPLCONFIGDIR', 'IPYTHONDIR']:
    Path(os.environ[key]).mkdir(parents=True, exist_ok=True)
paths = sorted((root / 'notebooks').glob('0[1-6]_*.ipynb'))
if args.notebook:
    paths = [p for p in paths if p.stem == args.notebook]
    if not paths: parser.error('Unknown notebook')
report = {}
if args.notebook and (root/'validation.json').exists():
    report = json.loads((root/'validation.json').read_text())
else:
    (root/'validation.json').write_text('{}\n')
for path in paths:
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    start = time.perf_counter()
    try:
        if args.inprocess:
            subprocess.run([sys.executable, str(root/'scripts/execute_inprocess.py'), str(path)], check=True, timeout=600)
            notebook = nbformat.read(path, as_version=4)
        else:
            NotebookClient(notebook, timeout=600, kernel_name='mofa-course',
                           resources={'metadata': {'path': str(root / 'notebooks')}}).execute()
        assert all(o.output_type != 'error' for c in notebook.cells if c.cell_type=='code' for o in c.outputs)
    except Exception:
        report[path.name] = dict(seconds=round(time.perf_counter()-start,2), status='failed')
        (root/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
        raise
    nbformat.write(notebook, path)
    report[path.name] = dict(seconds=round(time.perf_counter()-start, 2),
                            code_cells=sum(c.cell_type=='code' for c in notebook.cells),
                            kernel_mode='fresh_process_inprocess_kernel' if args.inprocess else 'jupyter_tcp', status='passed')
    (root/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(path.name, report[path.name], flush=True)
