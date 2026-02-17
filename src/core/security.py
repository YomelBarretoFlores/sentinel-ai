import re
from typing import Tuple


FORBIDDEN_PATTERNS = [
    r"rm\s+-rf\s+/\s*$",
    r"rm\s+-rf\s+/\*",
    r"mkfs\.",
    r"dd\s+if=",
    r":\(\)\{.*\|.*&\}\;",
    r"shutdown\s",
    r"reboot\s*$",
    r"halt\s*$",
    r"init\s+0",
    r"fdisk\s",
    r"parted\s",
    r"wipefs\s",
    r">\s*/dev/sd",
    r"chmod\s+-R\s+777\s+/\s*$",
    r"chown\s+-R.*:\s*/\s*$",
]

CRITICAL_PATTERNS = [
    r"\brm\b",
    r"\bdelete\b",
    r"\bdrop\b",
    r"\btruncate\b",
    r"\bkill\s+-9\b",
    r"\bsystemctl\s+stop\b",
    r"\bsystemctl\s+restart\b",
    r"\bservice\s+\S+\s+stop\b",
    r"\bservice\s+\S+\s+restart\b",
    r"\biptables\b",
    r"\bufw\b",
    r"\bpasswd\b",
    r"\busermod\b",
    r"\buserdel\b",
    r"\bchmod\b",
    r"\bchown\b",
    r"\bmv\s+/",
    r"\bcp\s+/dev/",
    r"\bapt\b",
    r"\bapt-get\b",
    r"\byum\b",
    r"\bdnf\b",
    r"\binstall\b",
]


def validate_command(command: str) -> Tuple[bool, str]:
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Comando bloqueado por politica de seguridad: patron prohibido"
    return True, ""


def is_critical(command: str) -> bool:
    for pattern in CRITICAL_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False
