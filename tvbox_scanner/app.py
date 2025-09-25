import json
import os
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template, request

from sources import discover_interface_urls
from tester import test_interface_url
from adb_helper import (
	adb_available,
	list_connected_devices,
	launch_tvbox_app,
	paste_text_into_device,
)


def create_app() -> Flask:
	app = Flask(__name__, template_folder="templates", static_folder="static")

	@app.get("/")
	def index() -> Any:
		return render_template("index.html")

	@app.get("/api/sources")
	def api_sources() -> Any:
		seed_only = request.args.get("seed_only") == "1"
		urls = discover_interface_urls(seed_only=seed_only)
		return jsonify({"count": len(urls), "urls": urls})

	@app.post("/api/test")
	def api_test() -> Any:
		payload: Dict[str, Any] = request.get_json(force=True) or {}
		url: str = payload.get("url", "").strip()
		if not url:
			return jsonify({"ok": False, "error": "Missing url"}), 400
		result = test_interface_url(url)
		return jsonify(result)

	@app.post("/api/test/bulk")
	def api_test_bulk() -> Any:
		payload: Dict[str, Any] = request.get_json(force=True) or {}
		urls: List[str] = list({u.strip() for u in (payload.get("urls") or []) if isinstance(u, str) and u.strip()})
		results: List[Dict[str, Any]] = []
		for url in urls:
			results.append(test_interface_url(url))
		return jsonify({"count": len(results), "results": results})

	@app.get("/api/adb/status")
	def api_adb_status() -> Any:
		return jsonify({"adb_available": adb_available()})

	@app.get("/api/adb/devices")
	def api_adb_devices() -> Any:
		if not adb_available():
			return jsonify({"ok": False, "error": "adb not found"}), 400
		devices = list_connected_devices()
		return jsonify({"ok": True, "devices": devices})

	@app.post("/api/adb/launch")
	def api_adb_launch() -> Any:
		if not adb_available():
			return jsonify({"ok": False, "error": "adb not found"}), 400
		payload: Dict[str, Any] = request.get_json(force=True) or {}
		serial = (payload.get("serial") or "").strip()
		ok, msg = launch_tvbox_app(serial)
		return jsonify({"ok": ok, "message": msg})

	@app.post("/api/adb/paste")
	def api_adb_paste() -> Any:
		if not adb_available():
			return jsonify({"ok": False, "error": "adb not found"}), 400
		payload: Dict[str, Any] = request.get_json(force=True) or {}
		serial = (payload.get("serial") or "").strip()
		text = (payload.get("text") or "").strip()
		ok, msg = paste_text_into_device(serial, text)
		return jsonify({"ok": ok, "message": msg})

	return app


if __name__ == "__main__":
	port = int(os.environ.get("PORT", "5000"))
	app = create_app()
	app.run(host="0.0.0.0", port=port, debug=True)

