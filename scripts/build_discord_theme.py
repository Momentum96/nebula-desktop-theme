import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "discord" / "theme.src.css"
IMAGE = ROOT / "discord" / "nebula-bg.jpg"
OUT = ROOT / "discord" / "nowaywork.theme.css"
PLACEHOLDER = "__NEBULA_BG_DATA_URI__"


def main() -> None:
    src = SRC.read_text(encoding="utf-8")
    if src.count(PLACEHOLDER) != 1:
        raise SystemExit(f"{SRC} must contain {PLACEHOLDER} exactly once")
    data_uri = "data:image/jpeg;base64," + base64.b64encode(IMAGE.read_bytes()).decode()
    OUT.write_text(src.replace(PLACEHOLDER, data_uri), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
