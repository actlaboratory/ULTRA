# npc service
# Copyright (C) 2021 yamahubuki <itiro.ishino@gmail.com>

import os
import time
import tweepy
import twitterAuthorization
import webbrowser
import wx

import constants
import errorCodes
import views.auth
import simpleDialog

from logging import getLogger


log = getLogger("%s.twitterService" % (constants.LOG_PREFIX))


def getToken():
	manager = twitterAuthorization.TwitterAuthorization(constants.TWITTER_CONSUMER_KEY, constants.TWITTER_CONSUMER_SECRET, constants.TWITTER_PORT)
	l="ja"
	try:
		l=globalVars.app.config["general"]["language"].split("_")[0].lower()
	except:
		pass#end うまく読めなかったら ja を採用
	#end except
	manager.setMessage(
		lang=l,
		success=_("認証に成功しました。このウィンドウを閉じて、アプリケーションに戻ってください。"),
		failed=_("認証に失敗しました。もう一度お試しください。"),
		transfer=_("しばらくしても画面が切り替わらない場合は、別のブラウザでお試しください。")
	)
	webbrowser.open(manager.getUrl())
	d = views.auth.waitingDialog()
	d.Initialize(_("Twitterアカウント認証"))
	d.Show(False)
	while True:
		time.sleep(0.01)
		wx.YieldIfNeeded()
		if manager.getToken():
			d.Destroy()
			break
		if d.canceled == 1 or manager.getToken() == "":
			simpleDialog.dialog(_("処理結果"), _("キャンセルされました。"))
			manager.shutdown()
			d.Destroy()
			return
	return manager.getToken()

def getFollowList(token,target):
	auth = tweepy.OAuthHandler(constants.TWITTER_CONSUMER_KEY, constants.TWITTER_CONSUMER_SECRET)
	auth.set_access_token(*token)
	try:
		twitterApi = tweepy.API(auth,proxy=os.environ['HTTPS_PROXY'])
	except KeyError:
		twitterApi = tweepy.API(auth)

	ret = []
	try:
		user = twitterApi.get_user(screen_name=target)
		friendsCount = user.friends_count
		friends = tweepy.Cursor(twitterApi.friends,screen_name=target,include_user_entities=False,skip_status=True,count=200).items()
		for friend in friends:
			ret.append(friend.screen_name)
		return ret
	except tweepy.error.RateLimitError:
		log.error("rateLimitError")
		return ret
	except tweepy.error.TweepError as e:
		log.error(e)
		log.error("%s" %(e.response))
		simpleDialog.errorDialog(_("Twitterからフォローリストを取得できませんでした。指定したユーザが存在しないか、フォローしていない非公開アカウントである可能性があります。"))
		return []
	except Exception:
		log.error(e)
		simpleDialog.errorDialog(_("Twitterからフォローリストを取得できませんでした。しばらくたってから再度お試しください。状況が改善しない場合には、開発者までお問い合わせください。"))
		return []
