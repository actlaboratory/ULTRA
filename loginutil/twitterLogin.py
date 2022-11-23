# NPC Twitter login module
# Copyright (C) 2021 yamahubuki <itiro.ishino@gmail.com>

import errorCodes

import requests
import urllib.parse

from bs4 import BeautifulSoup


def getToken(session):
	page = session.get("https://peing.net/ja/",timeout=5)
	soup = BeautifulSoup(page.content, "lxml")
	form = soup.find("form", {"action":"/auth/twitter"})
	ret = form.find("input", {"name":"authenticity_token","type":"hidden"})
	return ret["value"]

def login(id, password):
	session = requests.Session()
	session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"})

	#STEP1: referer対策のためのリクエスト
	# STEP1: Refeler対策のため、トップページへダミーアクセス
	ret = session.get("https://twitcasting.tv/",timeout=5)
	if ret.status_code!=200:
		return errorCodes.LOGIN_TWITCASTING_ERROR

	#STEP2: Twitterのログインページへジャンプ
	ret = session.get("https://twitcasting.tv/?goauth=1&b=%2F&keep=1",timeout=5)
	if not ret.url.startswith("https://api.twitter.com/oauth/authenticate?"):
		return errorCodes.LOGIN_TWITCASTING_ERROR

	#STEP3: 取得したページを解析して次のリクエストを生成
	soup = BeautifulSoup(ret.content, "lxml")
	headers = {}
	data = {
		"authenticity_token": soup.find("input", {"name":"authenticity_token","type":"hidden"})["value"],
		"redirect_after_login": soup.find("input", {"name":"redirect_after_login","type":"hidden"})["value"],
		"oauth_token": soup.find("input", {"name":"oauth_token","type":"hidden"})["value"],
		"session[username_or_email]": id,
		"session[password]": password
	}

	#STEP4: ログインリクエスト
	ret =  session.post("https://api.twitter.com/oauth/authenticate",headers=headers,data=data,timeout=5)
	if ret.url.startswith("https://twitter.com/login/error?"):
		return errorCodes.LOGIN_TWITTER_WRONG_ACCOUNT
	elif ret.url.startswith("https://twitter.com/account/access") or ret.url.startswith("https://twitter.com/login"):
		return errorCodes.LOGIN_RECAPTCHA_NEEDED
	elif not ret.url.startswith("https://api.twitter.com/oauth/authenticate"):
		return errorCodes.LOGIN_TWITTER_ERROR

	#STEP5: 戻り先URLの取得
	try:
		soup = BeautifulSoup(ret.content, "lxml")
		url = soup.find("meta",{"http-equiv":"refresh"})["content"][6:]
	except:
		return errorCodes.LOGIN_CONFIRM_NEEDED
	if not url.startswith("https://twitcasting.tv/?"):
		return errorCodes.LOGIN_TWITTER_ERROR

	#STEP6: 戻り先URLへアクセス
	ret = session.get(url)
	if not ret.url.startswith("https://twitcasting.tv/") or len(ret.history)!=1:
		return errorCodes.LOGIN_TWITCASTING_ERROR
	return session
