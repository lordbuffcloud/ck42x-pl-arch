import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from ck42x_pl_arch.tui.banner_art import BANNER_LINES, BANNER_WIDTH, banner_markup

print(f"{len(BANNER_LINES)} lines x {BANNER_WIDTH} cols\n")
print(banner_markup())
