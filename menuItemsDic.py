

import re

def getValueString(ref_id):
	""" ナビキーとダイアログ文字列を消去した文字列を取り出し """
	dicVal = dic[ref_id]
	s = re.sub("\.\.\.$", "", dicVal)
	s = re.sub("\(&.\)$", "", s)
	return re.sub("&", "", s)



dic={
	"SHOW": _("ウィンドウを表示(&S)"),
	"HIDE": _("ウィンドウを隠す(&H)"),
	"EXIT": _("終了(&X)"),
	"TC_SUB": _("ツイキャス(&T)"),
	"TC_ENABLE": _("ツイキャス連携機能を有効化(&E)"),
	"TC_SAVE_COMMENTS": _("録画時にコメントをテキストファイルに保存する "),
	"TC_LOGIN_TOGGLE": _("ログイン状態で録画"),
	"TC_UPDATE_USER": _("ユーザ情報を更新(&U)"),
	"TC_ADD_MULTIPLE": _("ユーザを一括追加(&B)"),
	"TC_RECORD_ARCHIVE": _("過去ライブのダウンロード(&A)") + "...",
	"TC_RECORD_ALL": _("過去ライブの一括ダウンロード(&D)"),
	"TC_RECORD_USER": _("指定したユーザのライブを録画(&R)") + "...",
	"TC_REMOVE_SESSION": _("ログインセッションを削除"),
	"TC_REMOVE_TOKEN": _("アクセストークンを削除"),
	"TC_SET_TOKEN": _("アクセストークンを設定(&T)"),
	"TC_MANAGE_USER": _("通知対象ユーザの管理(&M)") + "...",
	"TC_FILETYPES": _("録画形式の設定"),
	"YDL_SUB": _("その他のサービス（&yt-dlp）"),
	"YDL_ENABLE": _("一括ダウンロードを有効化(&E)"),
	"YDL_DOWNLOAD": _("&URLを指定してダウンロード"),
	"YDL_MANAGE_LISTS": _("一括ダウンロードURLの管理(&M)") + "...",
	"YDL_FILETYPES": _("録画形式の設定"),
	"LIVE17_SUB": _("17LIVE"),
	"LIVE17_DOWNLOAD": _("アーカイブURLを指定してダウンロード(&A)"),
	"LIVE17_DOWNLOAD_ALL": _("ユーザーのアーカイブを一括ダウンロード(&U)"),
	"LIVE17_FILETYPES": _("録画形式の設定"),
	"OP_SETTINGS": _("設定(&S)") + "...",
	"OP_SHORTCUT": _("キーボードショートカットの設定(&K)") + "...",
	"OP_HOTKEY": _("グローバルホットキーの設定(&H)") + "...",
	"OP_STARTUP": _("Windows起動時の自動起動を有効化(&W)"),
	"HELP_UPDATE":_("最新バージョンを確認(&U)")+"...",
	"HELP_VERSIONINFO":_("バージョン情報(&V)")+"...",
}
