import json
from typing import Any, Dict, List, Tuple

import requests


EXPECTED_TOP_LEVEL_KEYS: List[str] = [
	"sites",
	"lives",
	"rules",
	"parses",
	"spider",
]


def _score_json_payload(payload: Any) -> Tuple[bool, int, List[str]]:
	if not isinstance(payload, dict):
		return False, 0, []
	keys_present = [k for k in EXPECTED_TOP_LEVEL_KEYS if k in payload]
	return len(keys_present) >= 1, len(keys_present), keys_present


def test_interface_url(url: str, timeout_sec: int = 8) -> Dict[str, Any]:
	"""Fetch and validate a TVBox interface URL.

	Heuristics: returns ok if JSON loads and at least one expected key exists.
	"""
	data: Dict[str, Any] = {
		"url": url,
		"ok": False,
		"status": None,
		"content_type": None,
		"content_length": None,
		"score": 0,
		"keys": [],
		"error": None,
	}
	try:
		resp = requests.get(url, timeout=timeout_sec, headers={"User-Agent": "Mozilla/5.0 TVBoxScanner"})
		data["status"] = resp.status_code
		data["content_type"] = resp.headers.get("Content-Type")
		data["content_length"] = int(resp.headers.get("Content-Length")) if resp.headers.get("Content-Length") else None
		text = resp.text or ""
		try:
			payload = resp.json()
		except Exception:
			# Some endpoints may be plain text with JSON inside, try to parse loosely
			try:
				payload = json.loads(text)
			except Exception:
				payload = None
		ok, score, keys = _score_json_payload(payload)
		data["ok"] = bool(ok and resp.status_code == 200)
		data["score"] = score
		data["keys"] = keys
		if not data["ok"] and resp.status_code != 200:
			data["error"] = f"HTTP {resp.status_code}"
		elif not data["ok"]:
			data["error"] = "JSON missing expected keys"
		return data
	except Exception as exc:
		data["error"] = str(exc)
		return data

