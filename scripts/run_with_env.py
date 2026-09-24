import os
import shlex
import subprocess
import sys
from pathlib import Path


def load_env(path: Path) -> None:
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if value and value[0] in {'"', "'"}:
            value = shlex.split(value, comments=False)[0]
        os.environ[key.strip()] = value


def main() -> int:
    if len(sys.argv) < 3:
        raise SystemExit("usage: run_with_env.py ENV_FILE COMMAND [ARGS ...]")
    load_env(Path(sys.argv[1]))
    return subprocess.run(sys.argv[2:], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
