"""Validate the current PowerPoint JSON spec. The JSON is the canonical slide source.

Run the PowerPoint builder after editing it; do not regenerate it from stale literals.
"""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
spec_path = Path(__file__).with_name("bigdata-slides.json")
spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
assert isinstance(spec.get("strings"), dict)
assert isinstance(spec.get("slides"), list) and spec["slides"]
print(f"Validated {len(spec['slides'])} slides in {spec_path}")
