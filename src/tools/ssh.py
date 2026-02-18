import paramiko
import time
from typing import Tuple, Optional, List
from ..core.utils import check_stop


class SSHClient:
    def __init__(self, hostname: str, username: str, password: Optional[str] = None, key_filename: Optional[str] = None, port: int = 22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.port = port
        self.client = None

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                key_filename=self.key_filename,
                timeout=10
            )
            print(f"[SSH] Conexion establecida con {self.username}@{self.hostname}:{self.port}")
        except Exception as e:
            print(f"[SSH] Error de conexion: {e}")
            raise e

    def execute_command(self, command: str, use_sudo: bool = False) -> Tuple[int, str, str]:
        if not self.client:
            self.connect()

        check_stop()

        if use_sudo:
            command = f"sudo -S {command}"
            print(f"[SSH] Ejecutando (sudo): {command}")
            stdin, stdout, stderr = self.client.exec_command(command, get_pty=True)
            time.sleep(0.3)
            stdin.write(f"{self.password}\n")
            stdin.flush()
        else:
            print(f"[SSH] Ejecutando: {command}")
            stdin, stdout, stderr = self.client.exec_command(command)


        while not stdout.channel.exit_status_ready():
            try:
                check_stop()
            except Exception:
                print(f"[SSH] Interrupcion solicitada. Cerrando conexion.")
                if self.client:
                    self.client.close()
                raise
            time.sleep(0.5)

        exit_code = stdout.channel.recv_exit_status()
        try:
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
        except Exception:

            out = ""
            err = "Interrupted"

        if use_sudo and out.startswith("[sudo]"):
            lines = out.split("\n")
            out = "\n".join(lines[1:]).strip()

        return exit_code, out, err


    def close(self):
        if self.client:
            self.client.close()
