import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
for p in (ROOT / "skills" / "thai-docx" / "scripts", ROOT / "tests"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
