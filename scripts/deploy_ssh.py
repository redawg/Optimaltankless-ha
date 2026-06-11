#!/usr/bin/env python3
"""Deploy custom_components/optimaltankless to Forest Home via SSH."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST = os.environ.get("HA_HOST", "172.16.255.250")
LOCAL_ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "optimaltankless"
REMOTE_ROOT = "/config/custom_components/optimaltankless"
CANDIDATES = [
    ("root", os.environ.get("HA_SSH_PASSWORD", "")),
    ("homeassistant", os.environ.get("HA_SSH_PASSWORD", "")),
]


def upload_dir(sftp: paramiko.SFTPClient, local: Path, remote: str) -> None:
    try:
        sftp.mkdir(remote)
    except OSError:
        pass
    for item in local.iterdir():
        remote_path = f"{remote}/{item.name}"
        if item.is_dir():
            upload_dir(sftp, item, remote_path)
        else:
            print(f"PUT {item.name}")
            sftp.put(str(item), remote_path)


def connect() -> paramiko.SSHClient | None:
    password = os.environ.get("HA_SSH_PASSWORD", "")
    if not password:
        return None
    for user, _ in CANDIDATES:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                HOST,
                username=user,
                password=password,
                timeout=15,
                look_for_keys=False,
                allow_agent=False,
            )
            print(f"Connected as {user}@{HOST}")
            return client
        except Exception as exc:
            print(f"SSH failed for {user}: {exc}")
            client.close()
    return None


def main() -> int:
    client = connect()
    if not client:
        print("SSH deploy unavailable (set HA_SSH_PASSWORD)", file=sys.stderr)
        return 1

    client.exec_command(f"mkdir -p {REMOTE_ROOT}")[1].channel.recv_exit_status()
    sftp = client.open_sftp()
    upload_dir(sftp, LOCAL_ROOT, REMOTE_ROOT)
    sftp.close()

    _, stdout, stderr = client.exec_command("ha core restart")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode() or stderr.read().decode())
    client.close()
    print("SSH_DEPLOY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
