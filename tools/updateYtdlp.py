# -*- coding: utf-8 -*-
#requirements.txt内のyt-dlpのバージョンを最新に更新する

import re
import requests

REQUIREMENTS_FILE_NAME = "requirements.txt"
PYPI_URL = "https://pypi.org/pypi/yt-dlp/json"

def getLatestVersion():
	r = requests.get(PYPI_URL, timeout=10)
	r.raise_for_status()
	return r.json()["info"]["version"]

def updateRequirements(version):
	with open(REQUIREMENTS_FILE_NAME, "r", encoding="utf-8") as f:
		text = f.read()
	newText, count = re.subn(r"yt-dlp==\d+\.\d+\.\d+", "yt-dlp==" + version, text)
	if count == 0:
		print("yt-dlp==x.x.x is not found in %s." % REQUIREMENTS_FILE_NAME)
		return False
	if newText == text:
		print("yt-dlp is already up to date (%s)." % version)
		return False
	with open(REQUIREMENTS_FILE_NAME, "w", encoding="utf-8") as f:
		f.write(newText)
	print("Updated yt-dlp to %s." % version)
	return True

if __name__ == "__main__":
	version = getLatestVersion()
	print("Latest yt-dlp version: %s" % version)
	updateRequirements(version)
