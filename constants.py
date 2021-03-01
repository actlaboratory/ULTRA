# -*- coding: utf-8 -*-
#constant values
#Copyright (C) 20XX anonimous <anonimous@sample.com>

import wx

#アプリケーション基本情報
APP_FULL_NAME = "Universal Live Tracking And Recording App"#アプリケーションの完全な名前
APP_NAME="ULTRA"#アプリケーションの名前
APP_ICON = None
APP_VERSION="0.0.01"
APP_LAST_RELEASE_DATE="20xx-xx-xx"
APP_COPYRIGHT_YEAR="20xx"
APP_LICENSE="Apache License 2.0"
APP_DEVELOPERS="animous"
APP_DEVELOPERS_URL="https://example.com/"
APP_DETAILS_URL="https://example.com/template"
APP_COPYRIGHT_MESSAGE = "Copyright (c) %s %s All lights reserved." % (APP_COPYRIGHT_YEAR, APP_DEVELOPERS)

SUPPORTING_LANGUAGE={"ja-JP": "日本語","en-US": "English"}

#各種ファイル名
LOG_PREFIX="ultra"
LOG_FILE_NAME="ultra.log"
SETTING_FILE_NAME="data\\settings.ini"
KEYMAP_FILE_NAME="data\\keymap.ini"
TC_USER_DATA = "data\\twitcasting\\users.dat"
FFMPEG_PATH = "bin\\ffmpeg.exe"
# 各サービスのアカウントデータの格納場所
AC_TWITCASTING = "data\\twitcasting\\account.bin"



#フォントの設定可能サイズ範囲
FONT_MIN_SIZE=5
FONT_MAX_SIZE=35

#３ステートチェックボックスの状態定数
NOT_CHECKED=wx.CHK_UNCHECKED
HALF_CHECKED=wx.CHK_UNDETERMINED
FULL_CHECKED=wx.CHK_CHECKED
#build関連定数
BASE_PACKAGE_URL = None
PACKAGE_CONTAIN_ITEMS = ()#パッケージに含めたいファイルやfolderがあれば指定
NEED_HOOKS = ()#pyinstallerのhookを追加したい場合は指定
STARTUP_FILE = "ultra.py"#起動用ファイルを指定
# update情報
UPDATE_URL = "https://actlab.org/api/checkUpdate"
UPDATER_VERSION = "1.0.0"
UPDATER_WAKE_WORD = "hello"

# ツイキャス認証関係
TC_CID = "1266762249164619776.2ba35a3fe972584b3ab34e30c0c88ab6b4516d6aaf951c8a02744e21f22b23ba"
TC_URL = "https://apiv2.twitcasting.tv/oauth2/authorize"
TC_PORT = 9339

# その他
NOT_FOUND = -1
