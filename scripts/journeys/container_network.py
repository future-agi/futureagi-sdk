"""Host-side syscall accounting for all consumer descendants, before OS routing.

Linux VM prerequisite: Docker. A trusted network-none observer container has
SYS_PTRACE and the host PID namespace, attaching only to the specified consumer.
Candidates keep default seccomp, dropped capabilities and no-new-privileges.
No trace tool or writable control file is in the candidate.
The disconnected network blocks traffic; this observer counts even failed socket
syscalls, including native DNS/UDP, threads, children and grandchildren. In-process
guards additionally account for refusals that never reached a syscall.
"""
import ipaddress
import os
from pathlib import Path
import re
import shlex
import subprocess
import time


ADDRESS = re.compile(r'\{sa_family=AF_INET6?\b[^}]*\}')
HOST = re.compile(r'(?:inet_addr\(|inet_pton\(AF_INET6, )"([^"]+)"')
PORT = re.compile(r'sin6?_port=htons\((\d+)\)')


def summarize(path, runtime_offset, proxy):
    denied, allowed = [], 0
    position = 0
    with Path(path).open('rb') as stream:
        for raw in stream:
            phase = 'install' if position < runtime_offset else 'runtime'
            position += len(raw)
            line = raw.decode('utf8', 'replace')
            for address in ADDRESS.findall(line):
                host, port = HOST.search(address), PORT.search(address)
                host = host[1] if host else None
                port = int(port[1]) if port else None
                try:
                    local = ipaddress.ip_address(host).is_loopback
                except ValueError:
                    local = False
                # DNS is never part of a loopback fixture; include Docker's DNS relay.
                permitted = (local and port != 53) or (phase == 'install' and (host, port) == proxy)
                if permitted:
                    allowed += 1
                else:
                    denied.append({'host': host or 'unknown-internet-address', 'port': port, 'phase': phase,
                                   'source': 'container-syscall'})
    return {'denied_count': len(denied), 'denied': denied, 'allowed_count': allowed, 'complete': True}


class ContainerNetwork:
    def __init__(self, control, result, trace, proxy):
        self.control, self.result, self.trace = Path(control), Path(result), Path(trace)
        self.proxy = proxy
        self.runtime_offset = 1 << 63
        self.process = None
        self.channel = None
        self.error_stream = None
        self.control.mkdir()
        os.mkfifo(self.control / 'jobs')

    def start(self, pid, image):
        self.error_stream = self.trace.with_suffix('.stderr').open('w')
        self.trace.touch()
        # The observer's unmapped uid differs from the runner on remapped Docker
        # daemons. This one payload-free output file is not mounted in candidates.
        self.trace.chmod(0o666)
        self.observer_name = self.control.name + '-observer'
        # -s 0 removes buffers/iov payloads (including credential headers).
        # -v expands sendmmsg arrays so every destination is accounted for.
        # Only a single output file is mounted; no host files or Docker socket.
        self.process = subprocess.Popen(['docker', 'run', '--rm', '--name', self.observer_name,
                                         '--network=none', '--userns=host', '--pid=host', '--read-only', '--cap-drop=ALL',
                                         '--cap-add=SYS_PTRACE', '--security-opt=no-new-privileges',
                                         '--mount', f'type=bind,source={self.trace},target=/network.trace',
                                         image, '-f', '-s', '0', '-v',
                                         '-e', 'trace=connect,sendto,sendmsg,sendmmsg',
                                         '-o', '/network.trace', '-p', str(pid)], stderr=self.error_stream)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            self.healthy()
            status = Path(f'/proc/{pid}/status').read_text()
            if re.search(r'^TracerPid:\s+[1-9]\d*$', status, re.M):
                self.channel = os.open(self.control / 'jobs', os.O_WRONLY | os.O_NONBLOCK)
                return
            time.sleep(0.05)
        raise RuntimeError('Container syscall observer did not attach')

    def healthy(self):
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError('Container syscall observer is unavailable')

    def offline(self):
        self.healthy()
        self.runtime_offset = self.trace.stat().st_size

    def execute(self, sequence, argv, cwd, log, timeout=1200):
        self.healthy()
        identity = str(sequence)
        done = self.result / (identity + '.exit')
        output = self.result / (identity + '.log')
        command = ('cd ' + shlex.quote(cwd) + '\n' + shlex.join(list(map(str, argv))) +
                   ' > /result/' + output.name + ' 2>&1\ncode=$?\n' +
                   "printf '%s\\n' \"$code\" > /result/" + done.name + '.tmp\n' +
                   'mv /result/' + done.name + '.tmp /result/' + done.name + '\n')
        (self.control / (identity + '.sh')).write_text(command)
        os.write(self.channel, (identity + '\n').encode())
        deadline = time.monotonic() + timeout
        while not done.exists():
            self.healthy()
            if time.monotonic() > deadline:
                raise TimeoutError('Traced consumer command timed out')
            time.sleep(0.05)
        self.healthy()
        Path(log).write_bytes(output.read_bytes())
        return int(done.read_text())

    def finish(self):
        # Called only after docker rm: no background descendant can escape the
        # accounting window, even if the top-level probe already wrote JSON.
        if self.channel is not None:
            os.close(self.channel)
        try:
            if self.process is None or self.process.wait(timeout=30) != 0:
                raise RuntimeError('Container syscall accounting incomplete')
            return summarize(self.trace, self.runtime_offset, self.proxy)
        finally:
            if self.process is not None and self.process.poll() is None:
                subprocess.run(['docker', 'rm', '--force', self.observer_name], capture_output=True, timeout=30)
                self.process.wait(timeout=30)
            if self.error_stream:
                self.error_stream.close()
