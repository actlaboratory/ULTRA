# twitcastingAccount login
# Copyright (C) 2021 yamahubuki <itiro.ishino@gmail.com>

import requests
import errorCodes

from bs4 import BeautifulSoup

#IDとpwを用いてログインし、セッションを返却
#ID冒頭のc:は不要
def login(id,pw):
	session = requests.Session()
	session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"})

	# STEP1: Refeler対策のため、トップページへダミーアクセス
	ret = session.get("https://twitcasting.tv/",timeout=5)
	if ret.status_code!=200:
		return errorCodes.LOGIN_TWITCASTING_ERROR

	# STEP2: ログインページからCSRFトークンを取得
	page = session.get("https://twitcasting.tv/indexcaslogin.php?redir=%2F")
	if page.status_code!=200 or len(page.history)!=0:
		return errorCodes.LOGIN_TWITCASTING_ERROR
	try:
		soup = BeautifulSoup(page.content, "lxml")
		form = soup.find("form", {"id":"login-form"})
		ret = form.find("input", {"name":"cs_session_id","type":"hidden"})
		token =  ret["value"]
	except:
		return errorCodes.LOGIN_TWITCASTING_ERROR

	# STEP3: ログイン用のリクエスト
	headers = {
		"Content-Type":"application/x-www-form-urlencoded",
		"Accept":"Accept: text/html, application/xhtml+xml, image/jxr, */*",
		"Accept-Language":"ja-JP",
		"User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
	}
	body = {
		"username":id,
		"password":pw,
		"action":"login",
		"cs_session_id":token,
	}
	result = session.post("https://twitcasting.tv/indexcaslogin.php?redir=%2F"+"&keep=1", body, headers=headers, timeout=5)

	#STEP3: 結果の判定と返却
	if result.status_code!=200 or len(result.history)!=1 or result.history[0].status_code!=302 or result.url!="https://twitcasting.tv/":
		if result.status_code==200 and len(result.history)==0 and result.url.startswith("https://twitcasting.tv/indexcaslogin.php?"):
			return errorCodes.LOGIN_TWITCASTING_WRONG_ACCOUNT
		return errorCodes.LOGIN_TWITCASTING_ERROR
	return session
