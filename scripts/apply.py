from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAMP = time.strftime("%Y%m%d%H%M%S")
LAYOUT = "main-nebula"
THEME_FILE = "nowaywork.theme.css"


class Applier:
    def __init__(self, dry_run: bool) -> None:
        self.dry_run = dry_run

    def log(self, msg: str) -> None:
        print(("[dry-run] " if self.dry_run else "") + msg)

    def backup(self, path: Path) -> None:
        if path.exists():
            dest = path.with_name(f"{path.name}.bak-{STAMP}")
            self.log(f"backup {path} -> {dest.name}")
            if not self.dry_run:
                shutil.copy2(path, dest)

    def copy(self, src: Path, dest: Path) -> None:
        if dest.exists() and dest.read_bytes() == src.read_bytes():
            self.log(f"same   {dest}")
            return
        self.backup(dest)
        self.log(f"copy   {src.relative_to(ROOT)} -> {dest}")
        if not self.dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

    def merge_json(self, path: Path, update) -> None:
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        before = json.dumps(data, sort_keys=True)
        update(data)
        if json.dumps(data, sort_keys=True) == before:
            self.log(f"same   {path}")
            return
        self.backup(path)
        self.log(f"merge  {path}")
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")


def herdr_home() -> Path:
    env = os.environ.get("HERDR_APP_HOME")
    return Path(env).expanduser() if env else Path.home() / ".config" / "herdr-app"


def vencord_home() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Vencord"
    if sys.platform == "win32":
        return Path(os.environ["APPDATA"]) / "Vencord"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "Vencord"


def apply_herdr(a: Applier) -> None:
    home = herdr_home()
    if not home.is_dir():
        raise SystemExit(f"Herdr home not found: {home} (start Herdr once, or set HERDR_APP_HOME)")
    src = ROOT / "herdr"
    a.copy(src / "layouts" / f"{LAYOUT}.json", home / "layouts" / f"{LAYOUT}.json")
    a.copy(src / "backgrounds" / "nebula-1536x1024.png", home / "backgrounds" / "nebula-1536x1024.png")
    theme = home / "themes" / "dracula.json"
    if theme.exists():
        a.log(f"keep   {theme} (already present)")
    else:
        a.copy(src / "themes" / "dracula.json", theme)
    wanted = json.loads((src / "settings.theme.json").read_text(encoding="utf-8"))
    a.merge_json(home / "settings.json", lambda d: d.update(wanted))

    cli = shutil.which("herdr-app")
    switch = ["herdr-app", "do", "layout.switch", json.dumps({"name": LAYOUT})]
    if not cli:
        a.log(f"herdr-app CLI not on PATH; switch layout in the app (ctrl-shift-l) to '{LAYOUT}'")
        return
    a.log("run    " + " ".join(switch))
    if not a.dry_run:
        result = subprocess.run(switch, capture_output=True, text=True)
        if result.returncode != 0:
            a.log(f"layout switch failed ({result.returncode}): {result.stderr.strip() or result.stdout.strip()}")


def apply_discord(a: Applier) -> None:
    home = vencord_home()
    if not home.is_dir():
        raise SystemExit(f"Vencord folder not found: {home} (install Vencord and start Discord once)")
    a.copy(ROOT / "discord" / THEME_FILE, home / "themes" / THEME_FILE)

    def update(settings: dict[str, object]) -> None:
        themes = settings.get("enabledThemes")
        themes = list(themes) if isinstance(themes, list) else []
        if THEME_FILE not in themes:
            themes.append(THEME_FILE)
        settings["enabledThemes"] = themes
        settings["transparent"] = True
        if sys.platform == "darwin":
            settings["macosVibrancyStyle"] = "fullscreen-ui"

    a.merge_json(home / "settings" / "settings.json", update)
    a.log("Discord must be fully quit before this step and restarted after it (Vencord keeps settings in memory).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply the nebula Herdr layout and Discord (Vencord) theme.")
    parser.add_argument("--only", choices=["herdr", "discord"], help="apply one part only")
    parser.add_argument("--dry-run", action="store_true", help="print what would change, write nothing")
    args = parser.parse_args()
    a = Applier(args.dry_run)
    if args.only in (None, "herdr"):
        apply_herdr(a)
    if args.only in (None, "discord"):
        apply_discord(a)


if __name__ == "__main__":
    main()
