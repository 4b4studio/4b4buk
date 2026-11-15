"""The launch contract the 4b4 Hub reads; linking policy itself lives in the hub catalog."""
import json
from pathlib import Path

from buk.config import Settings
from buk.main import create_app

ROOT = Path(__file__).resolve().parents[2]
MODULE = json.loads((ROOT / "factory-module.json").read_text(encoding="utf-8"))


def test_contract_shape():
    assert MODULE["schema"] == "4b4apps.module/0.1"
    assert MODULE["id"] == "4b4buk"
    assert MODULE["open_mode"] == "top_level_navigation"
    entry = MODULE["entry_url"]
    assert entry is None or entry.startswith("https://")
    assert (ROOT / MODULE["icon"]).is_file()


def test_contract_exposes_no_odds_entry_point():
    assert all("odds" not in link.lower() for link in MODULE["deep_links"].values())


def test_health_url_is_a_route():
    paths = {getattr(route, "path", None) for route in create_app(settings=Settings()).routes}
    assert MODULE["health_url"] in paths
