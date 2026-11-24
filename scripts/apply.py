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
GLASS_LAYOUT = "main-nebula-glass"
THEME_FILE = "nowaywork.theme.css"
GLASS_CSS_START = "/* nebula-desktop-theme: glass start */"
GLASS_CSS_END = "/* nebula-desktop-theme: glass end */"


class Applier:
    def __init__(self, dry_run: bool) -> None:
        self.dry_run = dry_run

    def log(self, msg: str) -> None:
        print(("[dry-run] " if self.dry_run else "") + msg)

    def backup(self, path: Path) -> None:
        if path.exists():
            dest = path.with_name(f"{path.name}.bak-{STAMP}")
            sequence = 1
            while dest.exists():
                dest = path.with_name(f"{path.name}.bak-{STAMP}-{sequence}")
                sequence += 1
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


def apply_herdr(a: Applier, glass: bool) -> None:
    home = herdr_home()
    if not home.is_dir():
        raise SystemExit(f"Herdr home not found: {home} (start Herdr once, or set HERDR_APP_HOME)")
    src = ROOT / "herdr"
    a.copy(src / "layouts" / f"{LAYOUT}.json", home / "layouts" / f"{LAYOUT}.json")
    if glass:
        a.copy(src / "layouts" / f"{GLASS_LAYOUT}.json", home / "layouts" / f"{GLASS_LAYOUT}.json")
    a.copy(src / "backgrounds" / "nebula-1536x1024.png", home / "backgrounds" / "nebula-1536x1024.png")
    theme = home / "themes" / "dracula.json"
    if theme.exists():
        a.log(f"keep   {theme} (already present)")
    else:
        a.copy(src / "themes" / "dracula.json", theme)
    wanted = json.loads((src / "settings.theme.json").read_text(encoding="utf-8"))
    a.merge_json(home / "settings.json", lambda d: d.update(wanted))

    cli = shutil.which("herdr-app")
    layout = GLASS_LAYOUT if glass else LAYOUT
    switch = ["herdr-app", "do", "layout.switch", json.dumps({"name": layout})]
    if not cli:
        a.log(f"herdr-app CLI not on PATH; switch layout in the app (ctrl-shift-l) to '{layout}'")
        return
    a.log("run    " + " ".join(switch))
    if not a.dry_run:
        result = subprocess.run(switch, capture_output=True, text=True)
        if result.returncode != 0:
            a.log(f"layout switch failed ({result.returncode}): {result.stderr.strip() or result.stdout.strip()}")


def apply_discord(a: Applier, glass: bool) -> None:
    home = vencord_home()
    if not home.is_dir():
        raise SystemExit(f"Vencord folder not found: {home} (install Vencord and start Discord once)")
    quick_css = home / "settings" / "quickCss.css"
    existing = quick_css.read_bytes().decode("utf-8") if quick_css.exists() else ""
    snippet = (ROOT / "discord" / "nebula-glass.quick.css").read_text(encoding="utf-8")
    before, start, tail = existing.partition(GLASS_CSS_START + "\n")
    if start:
        _, end, after = tail.partition(GLASS_CSS_END + "\n")
        if not end:
            raise SystemExit(f"Unclosed nebula glass block: {quick_css}")
        existing_user_css = before.removesuffix("\n\n") + after
    else:
        existing_user_css = existing
    # Recognize the original standalone QuickCSS from the MacBook, too.
    if existing_user_css == snippet:
        existing_user_css = ""
    if glass:
        separator = "\n\n" if existing_user_css else ""
        wanted_css = f"{existing_user_css}{separator}{GLASS_CSS_START}\n{snippet}{GLASS_CSS_END}\n"
    else:
        wanted_css = existing_user_css

    a.copy(ROOT / "discord" / THEME_FILE, home / "themes" / THEME_FILE)
    if wanted_css != existing:
        a.backup(quick_css)
        a.log(f"update {quick_css}")
        if not a.dry_run:
            quick_css.parent.mkdir(parents=True, exist_ok=True)
            quick_css.write_bytes(wanted_css.encode("utf-8"))

    def update(settings: dict[str, object]) -> None:
        themes = settings.get("enabledThemes")
        themes = list(themes) if isinstance(themes, list) else []
        if THEME_FILE not in themes:
            themes.append(THEME_FILE)
        settings["enabledThemes"] = themes
        settings["transparent"] = True
        if sys.platform == "darwin":
            settings["macosVibrancyStyle"] = "fullscreen-ui"
        if glass:
            settings["useQuickCss"] = True

    a.merge_json(home / "settings" / "settings.json", update)
    a.log("Discord must be fully quit before this step and restarted after it (Vencord keeps settings in memory).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply the nebula Herdr layout and Discord (Vencord) theme.")
    parser.add_argument("--only", choices=["herdr", "discord"], help="apply one part only")
    parser.add_argument("--dry-run", action="store_true", help="print what would change, write nothing")
    parser.add_argument("--glass", action="store_true", help="use the macOS translucent wallpaper preset")
    args = parser.parse_args()
    if args.glass and sys.platform != "darwin":
        parser.error("--glass is only supported on macOS")
    a = Applier(args.dry_run)
    if args.only in (None, "herdr"):
        apply_herdr(a, args.glass)
    if args.only in (None, "discord"):
        apply_discord(a, args.glass)


if __name__ == "__main__":
    main()
