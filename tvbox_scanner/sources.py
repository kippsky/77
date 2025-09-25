import re
from typing import List, Set

import requests
from bs4 import BeautifulSoup


SEED_URLS: List[str] = [
	# Commonly circulated TVBox interface roots from the web
	"http://饭太硬.top/tv",
	"http://肥猫.live",
	"https://tvbox.cainisi.cf",
	"https://agit.ai/Yoursmile7/TVBox/raw/branch/master/XC.json",
	"http://xhww.fun:63/小米/DEMO.json",
	"http://pandown.pro/tvbox/tvbox.json",
	"http://rihou.cc:88/荷城茶秀",
	"https://100km.top/0",
]

# Pages that often list multiple interface URLs
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
		# Typical suffixes or path markers
		return any(k in url.lower() for k in [".json", "/tv", "tvbox", "box", "接口", "api"])  # broad heuristic
	return False


def _extract_links_from_html(html_text: str, base_url: str) -> List[str]:
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
	"""Discover candidate TVBox interface URLs.

	Returns a deduplicated list of candidates including known seeds and scraped ones.
	"""
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
				for link in _extract_links_from_html(resp.text, base_url=page):
					add(link)
		except Exception:
			continue

	return result

