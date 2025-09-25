import shutil
import subprocess
from typing import List, Tuple


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
	# Encode spaces and special chars for 'input text'
	# Replace spaces; escape special shell chars minimally
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

