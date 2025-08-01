		Universal Live Tracking and Recording App -ULTRA-

	バージョン:　　ver.1.10.0
	リリース:　　　2025-05-18
	開発・配布元:　ACT Laboratory　(https://actlab.org/)
	主要開発者:　　北畠一翔
　　ソフト種別:　　オープンソースソフトウェア　(GitHubリポジトリ:https://github.com/actlaboratory/ULTRA/)
　　ライセンス:　　Apache License 2.0

第１章　はじめに
１．１　Universal Live Tracking and Recording App(ULTRA)の概要
Universal Live Tracking and Recording Appは、インターネット上に公開されている動画配信サイト等の動画をダウンロードしたり、特定のユーザが配信を始めた際に通知したりできるソフトウェアです。
今後の更新で、対応サービスを追加する予定です。

１．２　動作環境について
64ビット版Windows10で動作確認を行っています。
多くの場合、Windowsの他のバージョンでも動作すると思われます。
ただし、同梱しているffmpegが64ビット版のため、32ビット版Windowsでは動作しません。

ULTRAはWindowsの標準的なコントロールのみを使用しており、画面読み上げソフトなどの支援技術と一緒に使用できます。

１．３　対応サービス一覧
現時点では、以下のサービスに対応しています。
今後の更新で、更に対応サービスを追加する予定です。
・ツイキャス（https://twitcasting.tv/）
・YouTubeなど、「yt-dlp」（https://github.com/yt-dlp/yt-dlp）がサポートしているサービスからの動画のダウンロード
※yt-dlpとの連携機能は、基本的にYouTube動画のダウンロードのために使用することを想定しています。他のサービスの動画もダウンロードを試みますが、すべてのサービスの動画を確実にダウンロードできることを保障するものではありません。

第２章　セットアップ
２．１　インストール
ULTRAを使用するにあたって、特別なインストール作業は必要ありません。
ダウンロードしたzipファイルを適当な場所に展開し、「ULTRA」フォルダ内の「ULTRA.exe」を実行すると起動します。

２．２　アンインストール
ULTRAをコンピュータから削除する場合は、「ULTRA」フォルダを削除してください。
その他、特別な作業は不要です。

２．３　アップデート
発見された不具合の修正、新機能の追加、各サービスの仕様変更への対応などの目的で、バージョンアップを行う場合があります。
新しいバージョンが利用可能な場合、ULTRAの起動時にメッセージが表示されます。
指示に従って操作してください。

第３章　ULTRAの基本機能
この章では、ULTRAが持っている基本的な機能を説明します。
各サービスへの対応については、次章を参照してください。

３．１　配信開始時の通知機能
特定のユーザが配信を始めた際に、自動で通知する機能です。
以下の機能があり、自由に組み合わせて使用できます。
・バルーン通知：「配信開始：（ユーザ名）」という通知を表示します。Windows10では、アクションセンターからアクセスできるトースト通知が表示されます。その他のバージョンのWindowsでは、バルーン通知が表示されます。
・録画：後述の録画機能を起動し、自動で録画を開始します。
・ブラウザで開く：該当する配信を視聴できるページをブラウザで開きます。
・サウンドを再生：指定したサウンドを再生します。
デフォルトの通知方法を設定するには、メニューバーの[オプション]→[設定]を選択し、[通知]タブを使用します。

３．２　録画機能
通知方法として[録画]が有効になっている場合に、配信をリアルタイムに録画できます。
録画したデータはMP4などの動画ファイルとして保存できるほか、音声のみを保存することも可能です。
なお、録画には、本ソフトと一緒にインストールされるFFmpegというツールを使用しています。

録画の保存形式は、各サービス毎に独立して設定します。
メニューバーの[サービス]から各サービスのサブメニューを開き、[録画形式の設定]を選択してください。
なお、対応形式は、サービス毎に異なります。

３．３　メインウィンドウの操作
本ソフトのメインウィンドウには２つのリストビューがあります。
・動作履歴：録画の開始・終了など、過去に行った動作の履歴が表示されます。新しい項目は下に追加されます。
・動作状況：各サービスとの連携機能の動作状況が表示されます。サービスとの接続が行われていない場合は、「未接続」と表示されます。


第４章　各サービスとの連携機能の詳細
この章では、各サービスとの連携機能について説明します。
各サービスに固有の機能を表示するには、メニューバーの[サービス]を使用します。
目的のサービスのサブメニューを開くことで、全ての機能にアクセスできます。

４．１　ツイキャス
４．１．１　ツイキャス連携機能の概要
ツイキャス連携機能には、以下の機能があります。
・録画と同時に、コメントをテキストファイルに保存
・ツイキャスのサイト上に「録画」として公開されている動画のダウンロード
・ユーザ名を指定して録画
なお、ツイキャス連携機能を使用するためには、事前にツイキャスへの登録が必要です。
専用の「キャスアカウント」を作成できる他、Twitter等のSNSのアカウントを使用することもできます。

４．１．２　ツイキャス連携機能の使用方法
ツイキャス連携機能を使用するには、メニューバーの[サービス]→[ツイキャス]→[ツイキャス連携機能を有効化]を選択します。
初めてこの機能を使用する場合は、アクセストークンの登録を促すメッセージが表示されます。
本ソフトとツイキャスを連携するには、アクセストークンの設定が必要です。
[はい]を選択すると、ブラウザが起動し、ULTRAにアカウントの利用を許可するかどうかを確認するメッセージが表示されます。
内容を確認し、[連携アプリを許可]ボタンを押すと設定が完了します。

通知対象のユーザを設定するには、メニューバーの[サービス]→[ツイキャス]→[通知対象ユーザの管理]を選択します。
新しいユーザを追加するには、[追加]ボタンを押します。
[ユーザ名]に、英数字のユーザ名（例：act_laboratory）を入力します。
デフォルトの通知方法を使用せず、ユーザ専用の通知方法を設定するには、[専用設定を使用]を選択します。
[OK]ボタンを押すと、入力したユーザ名を基にユーザ情報が取得されます。該当するユーザが見つからない場合は、エラーメッセージが表示されます。
[現在の登録内容]でユーザを選択して[変更]ボタンを押すと、選択したユーザに対する通知方法を変更できます。ただし、ユーザ名は変更できません。
全ての設定が終了したら、[OK]ボタンを押して設定を保存します。

４．１．３　メニュー項目の詳細
メニューバーの[サービス]→[ツイキャス]には、以下の項目があります。
・ツイキャス連携機能を有効化：この項目を選択すると、ツイキャス連携機能の有効・無効が切り替わります。なお、ツイキャス連携機能を無効にした際、他の操作を受け付けなくなることがありますが、数秒で正常な状態になります。
・録画時にコメントをテキストファイルに保存する：録画を開始した際に、同時にコメントの保存を行うかどうかを設定します。コメントは、録画と同じ場所に、同じ名前のテキストファイルとして保存されます。初期状態で、この機能は無効になっています。
・ログイン状態で録画：録画をする際に、本ソフトと連携しているアカウントでログインするかどうかを設定します。この機能を有効にすることで、通常は正しく録画できない「センシティブな内容を含む配信」などの録画が可能になります（当該アカウントが適切な権限を持っている場合）。初期状態で、この機能は無効になっています。なお、この機能を使用する前に、次節の「利用に当たっての注意事項」を必ずご確認ください。
・過去ライブのダウンロード：「録画」としてツイキャスのサイトに公開されている動画をダウンロードできます。ダウンロードを開始するには、この項目を選択して現れるエディットボックスに、再生ページのURLを入力します。また、ULTRAと連携しているアカウントが適切な閲覧権限を持っていれば、プレミア配信の録画などもダウンロードできます。ただし、いくつかの制約があります。詳細については、次節の「利用に当たっての注意事項」を参照してください。
・過去ライブの一括ダウンロード：指定したユーザの過去ライブの内、「録画」として公開され、合い言葉で保護されていないものをすべてダウンロードします。この項目を選択して現れるエディットボックスにユーザ名を入力すると、自動的にダウンロードが行われます。なお、すでに本ソフトで録画されているライブはダウンロードされません。
・ユーザ情報を更新：ツイキャスでは、ユーザが自由にユーザ名や名前を変更できます。この項目を選択すると、最新のユーザ情報を取得し、ユーザ名や名前が変更されている場合にはそれを画面表示に反映します。ただし、ツイキャスAPIの実行回数制限を回避するため、ユーザ情報の取得は１分間に１件ずつ行われます。また、この機能の実行中は、[通知対象ユーザの管理]を使用できません。なお、配信開始を検知した際に自動でユーザ情報を更新するようになっているため、通常は手動でこの機能を呼び出す必要はありません。
・ユーザを一括追加：複数のユーザを指定し、まとめて追加する機能です。[通知対象ユーザの管理]と異なり、それぞれのユーザに対して専用の通知方法を設定しながら追加することはできません。必要に応じて、後から設定を行ってください。この項目を選択して現れるエディットボックスに、追加したいアカウントのユーザ名（例：act_laboratory）を、改行区切りで入力して[OK]ボタンを押すと、入力したユーザ名に合致するアカウントの検索と追加が行われます。存在しないユーザ名を指定した場合も、エラーは表示されません。なお、ツイキャスAPIの実行回数の制限を回避するため、ユーザの検索と追加は、1分間に1件ずつ行われます。また、すべての処理が終了するまで、[通知対象ユーザの管理]を使用できません。
・指定したユーザのライブを録画：指定したユーザを、録画対象として追加します。また、追加時点でユーザがライブ配信中の場合、録画を開始します。この登録は、一定時間経過後に自動で削除されます。ここで指定したユーザがライブを開始した場合、バルーン通知等は行わずに録画を開始します。
・ログインセッションを削除：[過去ライブのダウンロード]と[ログイン状態で録画]で保存したログイン情報（セッション）を削除します。[ログイン状態で録画]が有効なときにこの項目を選択すると、ログインせずに録画する状態（初期状態）に戻ります。
・アクセストークンを削除：登録されたアクセストークンを削除します。ツイキャスとの連携機能を使用中にこの項目を選択すると、自動的に連携機能が無効になります。
・アクセストークンを設定：アカウントの認証作業を再度実行します。アクセストークンの有効期限が近づいた場合や、使用するアカウントを変更したい場合に便利です。
・通知対象ユーザの管理：通知対象として登録するユーザを設定します。

４．１．４　利用に当たっての注意事項
１．　ツイキャスのアクセストークンは、登録後１８０日が経過すると使用できなくなります。アクセストークンの有効期限が近づくと、再登録を促すメッセージを表示します。本ソフトの使用を続けるには、再度アカウントの認証作業を行ってください。
２．　ツイキャスには、「グループ限定配信」や「プライベート配信」など、特定のユーザにしか閲覧できない特別な配信があります。本ソフトの通知機能は、これらの配信には対応していません。ただし、プライベート配信の録画が公開されている場合、「合い言葉」を入力することで、録画をダウンロードすることは可能です。また、プレミア配信の録画など、特定のアカウントでのみ閲覧できる録画のダウンロードにも対応しています（後述）。
３．　ULTRAに設定したアクセストークンの情報は、ULTRAをインストールしたフォルダ内の「data」フォルダにある「twitcasting」サブフォルダ内に、「account.bin」というファイル名で保存されます。このファイルを外部に流出させないよう、十分ご注意ください。また、複数のコンピュータでULTRAを使用する場合、１台のコンピュータで認証作業を行った後、account.binを別のコンピュータにコピーしてください。
４．　プレミア配信の録画など、特定のアカウントでしか閲覧できないライブについては、その詳細情報を取得することができません。[過去ライブのダウンロード]を実行して再生ページのURLを入力すると、情報の取得に失敗した旨を通知するメッセージが表示されます。[はい]を選択すると、ULTRAと連携しているアカウントのパスワードの入力が求められます。正しいパスワードを入力し、ログインに成功すると、改めてライブのダウンロードを試みます。1度ログインに成功すると、そのユーザ名とログイン情報（セッション）を保存するため、使用するアカウントを変更しない限り、パスワードを再度入力する必要は通常ありません。また、このような方法で録画したライブは、配信開始日時を取得できないため、録画を開始した時点での日時がファイル名に使用されます。また、ファイル名の設定内容に関係なく、ファイル名の末尾にライブのID（数値）を追加します。
５．　[ログイン状態で録画]を使用するには、本ソフトと連携しているアカウントのパスワードを入力する必要があります。初めてこの機能を有効にすると、パスワードの入力を促すメッセージが表示されます。正しいパスワードを入力し、ログインに成功すると、その情報（セッション）を保存します。そのため、使用するアカウントを変更しない限り、再度パスワードを入力する必要はありません。
６．　[過去ライブのダウンロード]と[ログイン状態で録画]では、同じログイン情報を共有しています。そのため、一方でパスワードを入力してログインに成功すると、もう一方の機能を使用する際にパスワードを入力する必要はありません。また、セッション情報は、ULTRAをインストールしたフォルダ内の「data」フォルダにある「twitcasting」サブフォルダ内に、「session.dat」というファイル名で保存されます。このファイルを外部に流出させないよう、十分ご注意ください。
７．　ULTRA Version 1.5.2の更新に伴い、[ログイン状態で録画]および[過去ライブのダウンロード]機能でTwitterアカウントにログインする際、ツイキャスのサイトで設定された「ログインパスワード」を使用するようになりました。この機能の使用前に、ツイキャスのサイトでログインパスワードを設定し、それをULTRAに入力する必要があります。なお、旧バージョンで過去にログインしたことがあり、そのセッションが利用可能な場合、手動でセッションを削除したり、何らかの理由でセッションが無効になったりしない限り、特別な操作は不要です。
８．　ツイキャスには、アカウントごとにAPIのアクセス回数に制限があります。そのため、他のツイキャス関連アプリケーションと同じアカウントでAPIへのアクセスを行うと、アクセス回数が多すぎると運営に判断され、アクセスをブロックされてしまう可能性があります。

４．１．5　ULTRA Version 1.9.4への更新に伴う新着ライブの取得方法の変更について
従来、ULTRAの新着ライブ通知機能は、ツイキャスが提供する「Realtime API」を利用していました。
このAPIは、一度ツイキャスと接続を確立すれば、自動的に新着ライブの情報が送られる仕組みです。
しかし、ある時期から接続に失敗したり、接続が成功しても新着ライブの情報が送られてこなかったりする問題が頻発するようになりました。
ツイキャスにも何度か不具合を報告しましたが、一時的に改善するものの、すぐに同様の問題が再発し、不安定な状況が続いています。
そのため、ULTRAユーザーの皆様からも「通知機能が動作しない」というご報告を多数いただいております。
そこで、従来のRealtime APIを用いた監視機能に加え、定期的にツイキャスの新着ライブリストを取得し、通知対象のライブがないかチェックする仕組みを実装しました。
これにより、Realtime APIが正常に動作していない場合でも、新着ライブの監視機能を引き続きご利用いただけます。
ただし、この方法で取得できるのは最新100件のライブのみです。
短時間に100件を超えるライブが開始された場合、この方法だけでは一部のライブを検知できない可能性があります。
また、上記注意事項の８．に関連して、新着ライブリストを確認するたびに1回ずつAPIへアクセスを行います。
ULTRAのみを使用する場合は、APIのアクセス制限を超過しないよう調整していますが、他のツイキャス関連アプリケーションと併用すると、アクセス制限に達する可能性が高まります。
ご利用の際はご注意ください。

4．2　「yt-dlp」対応サービスからの動画ダウンロード機能
4．2．1　yt-dlpとの連携機能の概要
本ソフトと一緒にインストールされる「yt-dlp」と連携し、動画をダウンロードする機能です。
基本的に、YouTube動画のダウンロード機能として使用することを想定しています。
動画をダウンロードするには、メニューバーの[サービス]→[その他のサービス（yt-dlp）]→[URLを指定してダウンロード]を選択し、再生ページのURLを入力します。
なお、動画の形式は[動画]と[音声のみ]を選択できますが、具体的なファイル形式（mp4、mp3など）は、対象の動画の種類によって変化します。
また、保存先フォルダ・ファイル名に関して、ユーザ名の末尾に対象サービス名（例：youtube）を、ファイル名の末尾に動画のIDを、それぞれ追加します。
動画ごとのダウンロードに加え、プレイリストやチャンネルのURLを指定し、そこに含まれる動画をまとめてダウンロードすることもできます。
上記の[URLを指定してダウンロード]にプレイリストやチャンネルのURLを入力してください。
また、ダウンロードしたいURLとダウンロード間隔を複数設定しておき、定期的にダウンロードすることもできます。
メニューバーの[サービス]→[その他のサービス（yt-dlp）]→[一括ダウンロードURLの管理]を実行し、ダウンロードしたいURLとダウンロード間隔（秒）を設定します。
[追加]ボタンを押すと、URLとダウンロード間隔を指定するダイアログが表示されます。
ダウンロード間隔は、通常3600秒（1時間）に設定されています。
内容を入力して[OK]ボタンを押すと、入力したURLに該当するプレイリストの情報が取得されます。
大きなプレイリストを指定した場合には、ここでしばらく時間がかかったり、「応答なし」と表示されたりすることがありますが、そのままお待ちください。
プレイリストの取得に成功すると、[タイトル]欄にプレイリストのタイトルが表示されます。
なお、リストからプレイリストを選択して[変更]ボタンを押すと、ダウンロード間隔に加え、タイトルを編集することができます。
通常、プレイリストのタイトルは、初めてそのプレイリストを追加した際に取得したものを使用し続け、サイト側でプレイリストのタイトルが変更されても、それを反映することはありません。
プレイリストのタイトルを変更したい場合には、この画面で設定する必要があります。
また、ここで指定するタイトルは、本ソフト上の表示にのみ影響します。
そのため、サイト側のタイトルに合わせる必要はなく、わかりやすいものを指定できます。
すべての設定が終了したら、[OK]ボタンで内容を保存します。
プレイリストの定期的なダウンロードは、メニューバーの[サービス]→[その他のサービス（yt-dlp）]→[一括ダウンロードを有効化]のチェック状態を切り替えることで、開始・停止できます。

4．2．2　制限事項
本機能の利用に関して、現状、以下の制限があります。
・動画のダウンロードに当たっては、「yt-dlpで取得した情報を元にffmpegを呼び出す」という方法をとっています。そのため、yt-dlpの対応サービスの内、ダウンロード時に特殊な処理が必要なサービスでは、本ソフトでの動画のダウンロードに失敗する可能性があります。現時点で、「ニコニコ動画」の動画をダウンロードできない事象を確認しています。
・本ソフトを用いてYouTubeの動画をダウンロードした際、「録画エラー」として何らかのエラーメッセージが表示されることがあります。しかし、ダウンロードに失敗しているのか、成功しているのかは、保存されたファイルを確認しなければ判断できません。そこで、同じ動画を複数回ダウンロードしてしまうことのないよう、録画エラーが発生した場合でも、エラー内容を表示するのみで、直ちに録画処理を終了します（再度録画を開始することはありません）。
・YouTube動画のアップロード時刻を取得することができません。そのため、「アップロードされた日の0時0分0秒」として処理を行います。また、日時情報をまったく取得できない場合、ダウンロード操作を行った日時を使用します。

第５章　メニューリファレンス
ここでは、ULTRAの各メニュー項目について解説します。
また、メニューを選択することによって表示される設定画面の内容についても記載しています。

５．１　ファイル
５．１．１　ウィンドウを隠す
何らかのサービスと連携している場合に、ULTRAのメインウィンドウを非表示にできます。
ウィンドウを再度表示するには、タスクトレイにあるULTRAのアイコンをダブルクリックするか、右クリックで開くコンテキストメニューから[ウィンドウを表示]を選択します。
なお、既定の設定では、Alt+F4を押すなどしてウィンドウを閉じた場合にも、タスクトレイに最小化されます。

５．１．２　終了
ULTRAを終了します。

５．２　サービス
各サービスに固有の機能にアクセスするために使用します。
詳細については、前章までの説明を参照してください。

５．３　オプション
５．３．１　設定
ULTRAの動作に関する様々な設定を行うことができます。
この項目を選択すると、各種設定を行うためのダイアログボックスが表示されます。

このダイアログボックスは、複数のタブ（ページ）で構成されています。
Ctrl+Tab、Ctrl+Shift+Tabを押すと、表示するタブを切り替えることができます。
また、画面上部に表示されているタブをクリックすることで、直接目的のタブを表示させることもできます。

設定を保存してダイアログボックスを閉じるには、[OK]ボタンを押します。
変更を破棄してダイアログボックスを閉じるには、[キャンセル]ボタンを押します。

５．３．１．１　一般
ULTRAの動作全般に関する設定を行います。

５．３．１．１．１　起動時にウィンドウを隠す
ULTRAを起動した際、自動的にメインウィンドウを最小化するかどうかを設定します。
既定でチェックされていません。

５．３．１．１．２　終了時にタスクトレイに最小化
ULTRAのメインウィンドウでAlt+F4を押したり、画面上の「×」をクリックしたりした場合に、ウィンドウをタスクトレイに最小化するかどうかを設定します。
この設定を無効にすると、ULTRAのウィンドウを閉じた際に即座にプログラムを終了します。
この設定は、既定でチェックされています。

５．３．１．２　表示/言語
画面表示に関する設定です。
また、ULTRAの表示言語を変更することもできます。

５．３．１．２．１　言語
ULTRAの表示に使用する言語を設定します。
ただし、各サービスから取得される情報は、ここでの設定と必ずしも一致しません。
この設定を有効にするには、ULTRAの再起動が必要です。

５．３．１．２．２　画面表示モード
画面の表示方法を、[標準]、[ダーク]の間で設定します。
既定では[標準]に設定されています。
この設定を有効にするには、ULTRAの再起動が必要です。

５．３．１．３　通知
登録したユーザが配信を開始した際の、デフォルトの通知方法を設定します。
５．３．１．３．１　バルーン通知
Windows10ではトースト通知、その他のバージョンではバルーンを表示します。
既定でチェックされています。

５．３．１．３．２　録画
自動で録画を開始します。
既定でチェックされています。

５．３．１．３．３　ブラウザで開く
再生ページをブラウザで開きます。
既定でチェックされていません。

５．３．１．３．４　サウンドを再生
指定したサウンドを再生します。
既定でチェックされていません。

５．３．１．３．５　再生するサウンド
[サウンドを再生]が有効な場合に再生するサウンドファイルを設定します。
[参照]ボタンを使用して、ファイルを選択することもできます。
空白に設定すると、通知音は再生されません。

５．３．１．４　録画
録画機能の設定を行います。

５．３．１．４．１　保存先フォルダ
録画の保存先フォルダを設定します。
[参照]ボタンを使用して、既存のフォルダを選択することもできます。
また、フォルダ名の一部として「%source%」という文字列を指定すると、録画対象のサービスの名前に置き換えられます。
既定では、「output\%source%」に設定されています。
なお、指定したフォルダが存在しない場合、録画開始時に自動で作成されます。

５．３．１．４．２　ユーザごとにサブフォルダを作成
録画を保存する際、ユーザごとにサブフォルダを作成するかどうかを設定します。
既定でチェックされています。

５．３．１．４．３　保存ファイル名
保存するファイル名を指定します。
「%user%」を指定すると、その部分が配信者のユーザ名に置き換えられます。
「%movie%」を指定すると、その部分が動画の識別子（配信サイト側で設定されたもの）に置き換えられます。
また、%year%、%month%、%day%、%hour%、%minute%、%second%の各文字列は、配信開始日時に対応しています。
既定では、「%user%_%year%%month%%day%_%hour%%minute%%second%」に設定されています。

５．３．１．５　ネットワーク
ULTRAの自動更新や、通信にプロキシサーバーを使用する場合に必要な設定を行います。

５．３．１．５．１　起動時に更新を確認
起動時にULTRAの更新を確認するかどうかを設定します。
この設定は、既定でチェックされています。

５．３．１．５．２　プロキシサーバーの情報を手動で設定する
プロキシサーバーの情報を手動で設定するかどうかを設定します。
通常、ULTRAはWindowsに設定されたプロキシサーバーの情報を使用して接続を行いますが、何らかの理由で個別に設定したい場合は、この設定をチェックしてください。
この設定は、既定ではチェックされていません。

５．３．１．５．３　サーバーURL
[プロキシサーバーの情報を手動で設定する]が有効な場合に、プロキシサーバーのURLを設定します。

５．３．１．５．４　ポート番号
[プロキシサーバーの情報を手動で設定する]が有効な場合に、プロキシサーバーのポート番号を設定します。

５．３．２　ショートカットキーの設定
よく使う機能にショートカットキーを割り当てたり、すでに設定されている割り当てを変更したりできます。
ここで設定したショートカットキーは、ULTRAのウィンドウが前面に表示されている場合にのみ機能します。
前面に表示されているウィンドウに関係なく、ULTRAの起動中は常に使用できるショートカットキーを設定するには、次節の[グローバルホットキーの設定]を使用します。

[ショートカットキーの設定]ダイアログボックスには、以下の項目があります。
現在の登録内容：ショートカットキーを設定できるコマンドと、現在割り当てられているショートカットキーを表示します。該当する項目にショートカットキーが設定されていない場合は、「なし」と表示されます。
変更：選択した設定を変更します。
OK：設定を保存し、ダイアログボックスを閉じます。
キャンセル：設定を破棄し、ダイアログボックスを閉じます。

ショートカットキーを設定するには、以下の手順で操作します。
１．　[現在の登録内容]から、設定したい項目を選択します。
２．　[変更]ボタンを押します。
３．　[ショートカット1]の[設定]ボタンを押します。
４．　設定したいキーの組み合わせを押します。ショートカットキーの割り当てを削除したい場合は、Escapeキーを押します。
なお、１つのコマンドについて、ショートカットキーを最大５個設定できます。

５．３．３　グローバルホットキーの設定
よく使う機能にグローバルホットキーを割り当てたり、すでに設定されている割り当てを変更したりできます。
ここで設定したグローバルホットキーは、ULTRAが起動している間、他のウィンドウにフォーカスされている場合でも常に機能します。
設定方法は、[ショートカットキーの設定]と同じです。

５．４　ヘルプ
５．４．１　バージョン情報
ULTRAのバージョン番号を確認できます。

５．４．２　更新を確認
新しいバージョンが利用可能かどうかを確認します。
画面の指示に従って操作してください。

第６章　その他
６．１　利用に当たっての注意事項
１．　プロキシサーバーを使用する環境でお使いの場合は、プロキシサーバーのアドレスとして、「http://」で始まるURLを設定する必要があるようです。IPアドレスのみを設定していると、録画機能が正しく動作しないことを確認しています。通常、アプリの起動時にWindowsの設定を参照し、プロキシサーバーの情報を自動で設定しますが、動作に問題がある場合には、[オプション]→[設定]を開き、[ネットワーク]タブより、手動での設定をお試しください。
２．　ULTRAの使用中、以下のようなメッセージが表示されることがあります。
----------
An error has occurred. Contact to the developer for further assistance.
----------
このメッセージは、ソフトウェアに何らかの問題が起きていることを表しています。[OK]ボタンを押すと、自動的にULTRAは終了します。
この現象が発生した場合、ULTRAをインストールしたフォルダ内に「errorlog.txt」というファイルが作成されています。
このファイルの内容とそれまでに行った操作を、開発者までお知らせください。

６．２　連絡先
このソフトウェアを利用しての感想やご要望、不具合のご報告などは、以下のメールアドレスまたは掲示板へご連絡ください。

ACT Laboratory サポート：support@actlab.org
ACT Laboratory 掲示板：https://actlab.org/bbs/
ACT Laboratory Twitter：https://twitter.com/act_laboratory

