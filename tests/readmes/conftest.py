import sys
from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"
if str(FIXTURES) not in sys.path:
    sys.path.insert(0, str(FIXTURES))
