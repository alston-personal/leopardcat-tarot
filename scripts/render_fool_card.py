#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys


ROOT = Path("/home/ubuntu/leopardcat-tarot")


def main():
    config_path = ROOT / "generator" / "cards" / "card-00-the-fool.json"
    cmd = [sys.executable, str(ROOT / "generator" / "render_card.py"), str(config_path)]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
