"""Negative controls run only inside disconnected test containers."""
import json
from pathlib import Path
import socket
import subprocess
import sys

sys.path.insert(0, '/kit')
from network import RuntimeGuard

guard = RuntimeGuard()
guard.install()
mode = sys.argv[1]
if mode.startswith('sendmsg'):
    family = socket.AF_INET6 if mode.endswith('6') else socket.AF_INET
    address = ('2001:db8::1', 53) if family == socket.AF_INET6 else ('203.0.113.1', 53)
    with socket.socket(family, socket.SOCK_DGRAM) as sock:
        try:
            sock.sendmsg([b'not-a-credential-payload'], [], 0, address)
        except OSError:
            pass
else:
    code = "import socket\ns=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)\ntry: s.sendto(b'not-a-credential-payload',('203.0.113.1',53))\nexcept OSError: pass\ns.close()"
    if mode == 'child-tcp':
        code = "import socket\ns=socket.socket();s.settimeout(1)\ntry: s.connect(('203.0.113.1',443))\nexcept OSError: pass\ns.close()"
    if mode == 'grandchild-udp':
        code = 'import subprocess,sys; subprocess.run([sys.executable,"-c",' + repr(code) + '],check=True)'
    subprocess.run([sys.executable, '-I', '-c', code], check=True)
Path('/result/probe.json').write_text(json.dumps({'checks': [{'name': 'install.control', 'state': 'PASS'}], 'network': guard.result()}))
