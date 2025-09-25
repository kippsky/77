import json
import os
import re
import shutil
import subprocess
from typing import Any, Dict, List, Set, Tuple

import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template_string, request, Response


# ----------------------------- Inline UI assets -----------------------------

INDEX_HTML = """<!doctype html>
<html>
<head>
	<meta charset=\"utf-8\" />
	<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
	<title>TVBox 接口搜索与测试</title>
	<link rel=\"stylesheet\" href=\"/static/styles.css\" />
</head>
<body>
	<header>
		<h1>TVBox 接口搜索与测试</h1>
	</header>
	<main>
		<section class=\"controls\">
			<button id=\"btn-refresh\">搜索接口</button>
			<label><input type=\"checkbox\" id=\"seed-only\" /> 仅使用内置种子</label>
			<input type=\"text\" id=\"custom-url\" placeholder=\"粘贴自定义接口 URL\" />
			<button id=\"btn-add\">添加</button>
			<button id=\"btn-test-selected\">测试选中</button>
			<button id=\"btn-test-all\">测试全部</button>
		</section>

		<section class=\"layout\">
			<div class=\"col\">
				<h2>接口列表</h2>
				<ul id=\"url-list\"></ul>
			</div>
			<div class=\"col\">
				<h2>测试结果</h2>
				<div id=\"results\"></div>
			</div>
		</section>

		<section class=\"adb\">
			<h2>ADB 辅助（可选）</h2>
			<div id=\"adb-status\">检查中...</div>
			<div id=\"adb-panel\" style=\"display:none;\">
				<button id=\"btn-list-devices\">列出设备</button>
				<select id=\"adb-devices\"></select>
				<button id=\"btn-launch-tvbox\">启动 TVBox</button>
				<button id=\"btn-paste-into-device\">将选中 URL 输入到设备</button>
			</div>
		</section>
	</main>
	<script src=\"/static/app.js\"></script>
</body>
</html>
"""


STYLES_CSS = """body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif; margin: 0; padding: 0; }
header { background: #0f172a; color: #fff; padding: 14px 18px; }
main { padding: 16px; }

.controls { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 12px; }
.layout { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.col { border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; }

#url-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
#url-list li { display: flex; gap: 8px; align-items: center; padding: 6px; border-bottom: 1px dashed #e2e8f0; }
#url-list li button { margin-left: auto; }
#url-list li button + button { margin-left: 8px; }

.result { border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px; margin-bottom: 8px; }
.result.ok { border-color: #22c55e; }
.result.bad { border-color: #ef4444; }
.result .url { font-weight: 600; margin-bottom: 4px; }
.result .err { color: #ef4444; }

.adb { margin-top: 20px; }

@media (max-width: 900px) {
	.layout { grid-template-columns: 1fr; }
}
"""


APP_JS = """const urlListEl = document.getElementById('url-list');
const resultsEl = document.getElementById('results');
const seedOnlyEl = document.getElementById('seed-only');
const customUrlEl = document.getElementById('custom-url');

const adbStatusEl = document.getElementById('adb-status');
const adbPanelEl = document.getElementById('adb-panel');
const adbDevicesEl = document.getElementById('adb-devices');

const state = {
	urls: [],
	selected: new Set(),
};

function renderList() {
	urlListEl.innerHTML = '';
	state.urls.forEach((u, idx) => {
		const li = document.createElement('li');
		const cb = document.createElement('input');
		cb.type = 'checkbox';
		cb.checked = state.selected.has(u);
		cb.addEventListener('change', () => {
			if (cb.checked) state.selected.add(u); else state.selected.delete(u);
		});
		const span = document.createElement('span');
		span.textContent = u;
		const copyBtn = document.createElement('button');
		copyBtn.textContent = '复制';
		copyBtn.addEventListener('click', async () => {
			await navigator.clipboard.writeText(u);
			copyBtn.textContent = '已复制';
			setTimeout(() => (copyBtn.textContent = '复制'), 1200);
		});
		const testBtn = document.createElement('button');
		testBtn.textContent = '测试';
		testBtn.addEventListener('click', () => testOne(u));

		li.appendChild(cb);
		li.appendChild(span);
		li.appendChild(copyBtn);
		li.appendChild(testBtn);
		urlListEl.appendChild(li);
	});
}

function renderResult(item) {
	const div = document.createElement('div');
	div.className = 'result ' + (item.ok ? 'ok' : 'bad');
	div.innerHTML = `
		<div class=\"url\">${item.url}</div>
		<div>ok=${item.ok}, score=${item.score}, status=${item.status}, type=${item.content_type}</div>
		<div>keys: ${(item.keys || []).join(', ')}</div>
		${item.error ? `<div class=\"err\">${item.error}</div>` : ''}
	`;
	resultsEl.prepend(div);
}

async function fetchSources() {
	resultsEl.innerHTML = '';
	urlListEl.innerHTML = '<li>加载中...</li>';
	const resp = await fetch(`/api/sources?seed_only=${seedOnlyEl.checked ? '1' : '0'}`);
	const data = await resp.json();
	state.urls = data.urls;
	state.selected = new Set();
	renderList();
}

async function testOne(url) {
	const resp = await fetch('/api/test', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }) });
	const data = await resp.json();
	renderResult(data);
}

async function testSelected() {
	const urls = Array.from(state.selected);
	if (!urls.length) return;
	const resp = await fetch('/api/test/bulk', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ urls }) });
	const data = await resp.json();
	(data.results || []).forEach(renderResult);
}

async function testAll() {
	const resp = await fetch('/api/test/bulk', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ urls: state.urls }) });
	const data = await resp.json();
	(data.results || []).forEach(renderResult);
}

async function checkAdb() {
	try {
		const resp = await fetch('/api/adb/status');
		const data = await resp.json();
		if (data.adb_available) {
			adbStatusEl.textContent = 'ADB 可用';
			adbPanelEl.style.display = '';
		} else {
			adbStatusEl.textContent = 'ADB 不可用（可选）';
		}
	} catch (e) {
		adbStatusEl.textContent = 'ADB 状态未知';
	}
}

async function listDevices() {
	const resp = await fetch('/api/adb/devices');
	const data = await resp.json();
	adbDevicesEl.innerHTML = '';
	(data.devices || []).forEach((s) => {
		const opt = document.createElement('option');
		opt.value = s;
		opt.textContent = s;
		adbDevicesEl.appendChild(opt);
	});
}

async function launchTvbox() {
	const serial = adbDevicesEl.value || '';
	const resp = await fetch('/api/adb/launch', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ serial }) });
	const data = await resp.json();
	alert(data.message || (data.ok ? 'OK' : 'FAIL'));
}

async function pasteIntoDevice() {
	const serial = adbDevicesEl.value || '';
	const urls = Array.from(state.selected);
	if (!urls.length) return alert('请先选择一个 URL');
	const text = urls[0];
	const resp = await fetch('/api/adb/paste', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ serial, text }) });
	const data = await resp.json();
	alert(data.message || (data.ok ? 'OK' : 'FAIL'));
}

document.getElementById('btn-refresh').addEventListener('click', fetchSources);
document.getElementById('btn-add').addEventListener('click', () => {
	const v = (customUrlEl.value || '').trim();
	if (!v) return;
	if (!state.urls.includes(v)) state.urls.unshift(v);
	state.selected.add(v);
	customUrlEl.value = '';
	renderList();
});
document.getElementById('btn-test-selected').addEventListener('click', testSelected);
document.getElementById('btn-test-all').addEventListener('click', testAll);

document.getElementById('btn-list-devices').addEventListener('click', listDevices);
document.getElementById('btn-launch-tvbox').addEventListener('click', launchTvbox);
document.getElementById('btn-paste-into-device').addEventListener('click', pasteIntoDevice);

checkAdb();
fetchSources();
"""


# ----------------------------- Discovery logic ------------------------------

SEED_URLS: List[str] = [
	"http://饭太硬.top/tv",
	"http://肥猫.live",
	"https://tvbox.cainisi.cf",
	"https://agit.ai/Yoursmile7/TVBox/raw/branch/master/XC.json",
	"http://xhww.fun:63/小米/DEMO.json",
	"http://pandown.pro/tvbox/tvbox.json",
	"http://rihou.cc:88/荷城茶秀",
	"https://100km.top/0",
]

SEED_PAGES: List[str] = [
	"https://tvbox.catvod.com/",
	"https://yinghe.tv/tvbox-jsonlist/",
	"https://www.jikejiang.com/6376.html",
	"https://www.ikuandai.cn/13342.html",
	"https://www.dynav.net/802.html",
	"https://yinghe.lol/tvbox-zhiboyuan/",
]


def _looks_like_interface_url(url: str) -> bool:
	if not url:
		return False
	if any(s in url for s in ["javascript:", "mailto:"]):
		return False
	if url.lower().startswith(("http://", "https://")):
		return any(k in url.lower() for k in [".json", "/tv", "tvbox", "box", "接口", "api"])  # heuristic
	return False


def _extract_links_from_html(html_text: str) -> List[str]:
	soup = BeautifulSoup(html_text, "lxml")
	urls: Set[str] = set()
	for a in soup.find_all("a", href=True):
		h = a["href"].strip()
		if _looks_like_interface_url(h):
			urls.add(h)
	for code in soup.find_all(["code", "pre"]):
		text = code.get_text("\n", strip=True)
		for m in re.findall(r"https?://[^\s'\"]+", text):
			if _looks_like_interface_url(m):
				urls.add(m)
	return list(urls)


def discover_interface_urls(seed_only: bool = False, timeout_sec: int = 8) -> List[str]:
	result: List[str] = []
	seen: Set[str] = set()

	def add(url: str) -> None:
		u = url.strip()
		if not u or u in seen:
			return
		seen.add(u)
		result.append(u)

	for u in SEED_URLS:
		add(u)

	if seed_only:
		return result

	for page in SEED_PAGES:
		try:
			resp = requests.get(page, timeout=timeout_sec, headers={"User-Agent": "Mozilla/5.0 TVBoxScanner"})
			if resp.status_code == 200 and ("text/html" in resp.headers.get("Content-Type", "") or resp.text.startswith("<")):
				for link in _extract_links_from_html(resp.text):
					add(link)
		except Exception:
			continue

	return result


# ------------------------------ Testing logic -------------------------------

EXPECTED_TOP_LEVEL_KEYS: List[str] = ["sites", "lives", "rules", "parses", "spider"]


def _score_json_payload(payload: Any) -> Tuple[bool, int, List[str]]:
	if not isinstance(payload, dict):
		return False, 0, []
	keys_present = [k for k in EXPECTED_TOP_LEVEL_KEYS if k in payload]
	return len(keys_present) >= 1, len(keys_present), keys_present


def test_interface_url(url: str, timeout_sec: int = 8) -> Dict[str, Any]:
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


# ------------------------------ ADB utilities -------------------------------

def adb_available() -> bool:
	return shutil.which("adb") is not None


def _run(cmd: List[str]) -> Tuple[int, str, str]:
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
	out, err = proc.communicate(timeout=10)
	return proc.returncode, out.strip(), err.strip()


def list_connected_devices() -> List[str]:
	code, out, _ = _run(["adb", "devices"])
	if code != 0:
		return []
	lines = out.splitlines()
	serials: List[str] = []
	for line in lines[1:]:
		parts = line.split()
		if len(parts) >= 2 and parts[1] == "device":
			serials.append(parts[0])
	return serials


def launch_tvbox_app(serial: str = "") -> Tuple[bool, str]:
	component_candidates = [
		"com.github.tvbox.osc/.ui.activity.HomeActivity",
		"com.github.tvbox.osc/.MainActivity",
	]
	base_cmd = ["adb"] + (["-s", serial] if serial else [])
	for comp in component_candidates:
		code, out, err = _run(base_cmd + ["shell", "am", "start", "-n", comp])
		if code == 0 and "Error" not in out and "Error" not in err:
			return True, f"Launched {comp}"
	return False, "Failed to launch TVBox. Is it installed?"


def paste_text_into_device(serial: str, text: str) -> Tuple[bool, str]:
	if not text:
		return False, "No text to paste"
	escaped = (
		text.replace(" ", "%s")
		.replace("&", "\\&")
		.replace("(", "\\(")
		.replace(")", "\\)")
		.replace("|", "\\|")
		.replace("<", "\\<")
		.replace(">", "\\>")
	)
	base_cmd = ["adb"] + (["-s", serial] if serial else [])
	code, out, err = _run(base_cmd + ["shell", "input", "text", escaped])
	if code == 0:
		return True, "Text sent via adb input"
	return False, err or out or "Failed to send text"


# --------------------------------- Flask app --------------------------------

def create_app() -> Flask:
	app = Flask(__name__)

	@app.get("/")
	def index() -> Any:
		return render_template_string(INDEX_HTML)

	@app.get("/static/styles.css")
	def styles() -> Response:
		return Response(STYLES_CSS, mimetype="text/css")

	@app.get("/static/app.js")
	def script() -> Response:
		return Response(APP_JS, mimetype="application/javascript")

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

