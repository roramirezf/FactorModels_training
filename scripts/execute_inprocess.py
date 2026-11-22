"""Execute ONE notebook in a fresh real IPython kernel without network sockets.

Invoked in a separate Python process per notebook by run_notebooks.py. Uses the
ipykernel message protocol to capture streams, errors, display_data and results.
"""
import os
import sys
from pathlib import Path
import nbformat
from ipykernel.inprocess.manager import InProcessKernelManager

path=Path(sys.argv[1]).resolve()
os.chdir(path.parent)
notebook=nbformat.read(path,as_version=4)
km=InProcessKernelManager(); km.start_kernel()
kc=km.client(); kc.start_channels()
try:
    kc.execute('%matplotlib inline')
    kc.get_shell_msg()
    while kc.iopub_channel.msg_ready(): kc.get_iopub_msg()
    for cell in notebook.cells:
        if cell.cell_type!='code': continue
        cell.outputs=[]
        kc.execute(cell.source,store_history=True)
        reply=kc.get_shell_msg()
        cell.execution_count=reply['content']['execution_count']
        while kc.iopub_channel.msg_ready():
            msg=kc.get_iopub_msg()
            if msg['msg_type'] in ['stream','display_data','execute_result','error']:
                cell.outputs.append(nbformat.v4.output_from_msg(msg))
            elif msg['msg_type']=='clear_output': cell.outputs=[]
            elif msg['msg_type']=='update_display_data':
                raise RuntimeError('Dynamic display updates need explicit handling')
        if reply['content']['status']!='ok':
            raise RuntimeError(f"Cell {cell.execution_count}: {reply['content'].get('ename')}: {reply['content'].get('evalue')}")
    nbformat.validate(notebook)
    nbformat.write(notebook,path)
finally:
    kc.stop_channels();km.shutdown_kernel()
