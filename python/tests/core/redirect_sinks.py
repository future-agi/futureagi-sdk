"""Loopback listeners, a test certificate and planted markers for the cross-origin redirect tests."""

from __future__ import annotations

import datetime
import ipaddress
import secrets
import shutil
import socket
import ssl
import subprocess
import threading
import time
from typing import Any


class _Listener:
    """A loopback listener that records ``(scheme, raw request bytes)`` for each request and answers a redirect on
    paths without ``/done`` in the scheme it is told to, else ``200`` with ``{}``."""

    def __init__(self, host: str, port: int = 0, tls: ssl.SSLContext | None = None) -> None:
        self.host, self.tls = host, tls
        self.records: list[tuple[str, bytes]] = []
        self.redirect: tuple[str, int, str] | None = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(16)
        self.port = self.sock.getsockname()[1]
        threading.Thread(target=self._serve, daemon=True).start()

    def _serve(self) -> None:
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn: socket.socket) -> None:
        conn.settimeout(10)
        scheme = "http"
        try:
            if self.tls is not None and conn.recv(1, socket.MSG_PEEK) == b"\x16":
                conn, scheme = self.tls.wrap_socket(conn, server_side=True), "https"
            while True:
                data = b""
                while b"\r\n\r\n" not in data:
                    chunk = conn.recv(65536)
                    if not chunk:
                        return
                    data += chunk
                head, _, body = data.partition(b"\r\n\r\n")
                length = 0
                for line in head.split(b"\r\n")[1:]:
                    name, _, value = line.partition(b":")
                    if name.strip().lower() == b"content-length":
                        length = int(value.strip())
                while len(body) < length:
                    chunk = conn.recv(65536)
                    if not chunk:
                        break
                    body += chunk
                self.records.append((scheme, data if length == 0 else head + b"\r\n\r\n" + body))
                path = head.split(b" ")[1].decode()
                if self.redirect and self.redirect[0] == scheme and "/done" not in path:
                    status, location = self.redirect[1], self.redirect[2]
                    answer = f"HTTP/1.1 {status} Moved\r\nLocation: {location}\r\nContent-Length: 0\r\n\r\n"
                else:
                    answer = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 2\r\n\r\n{}"
                conn.sendall(answer.encode())
        except (OSError, ssl.SSLError, ValueError, IndexError):
            return
        finally:
            conn.close()

    def close(self) -> None:
        self.sock.close()


def _tls_files(tmp_path: Any) -> tuple[str, str] | None:
    """A self-signed certificate for 127.0.0.1, 127.0.0.2 and localhost, made in the test with ``cryptography``, else
    with the ``openssl`` command; ``None`` when neither is here."""
    cert_file, key_file = tmp_path / "cert.pem", tmp_path / "key.pem"
    try:
        from cryptography import x509
    except ImportError:
        tool = shutil.which("openssl")
        if tool is None:
            return None
        subprocess.run(
            [tool, "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "2", "-subj", "/CN=127.0.0.1",
             "-addext", "subjectAltName=IP:127.0.0.1,IP:127.0.0.2,DNS:localhost",
             "-keyout", str(key_file), "-out", str(cert_file)],
            check=True, capture_output=True,
        )
        return str(cert_file), str(key_file)
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
    start = datetime.datetime.fromtimestamp(time.time() - 86400, datetime.timezone.utc)
    names = [x509.IPAddress(ipaddress.ip_address(ip)) for ip in ("127.0.0.1", "127.0.0.2")] + [x509.DNSName("localhost")]
    cert = (
        x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(start)
        .not_valid_after(start + datetime.timedelta(days=2))
        .add_extension(x509.SubjectAlternativeName(names), critical=False)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    cert_file.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_file.write_bytes(
        key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    )
    return str(cert_file), str(key_file)


def _markers() -> dict[str, str]:
    tag = secrets.token_hex(8)
    names = ("cookie-header", "cookie-jar", "authorization", "x-api-key", "x-secret-key")
    return {name: f"MARKER{name.replace('-', '').upper()}{tag}" for name in names}
