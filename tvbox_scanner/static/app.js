const urlListEl = document.getElementById('url-list');
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
		<div class="url">${item.url}</div>
		<div>ok=${item.ok}, score=${item.score}, status=${item.status}, type=${item.content_type}</div>
		<div>keys: ${(item.keys || []).join(', ')}</div>
		${item.error ? `<div class="err">${item.error}</div>` : ''}
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

