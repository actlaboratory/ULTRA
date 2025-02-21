# -*- coding: utf-8 -*-
#app build tool
#Copyright (C) 2019 Yukio Nozawa <personal@nyanchangames.com>
#Copyright (C) 2019-2020 guredora <contact@guredora.com>
#Copyright (C) 2021 yamahubuki <itiro.ishino@gmail.com>
#Copyright (C) 2021 Hiroki Fujii <hfujii@hisystron.com>

#constantsのimport前に必要
import os
import sys
sys.path.append(os.getcwd())

import datetime
import glob
import hashlib
import json
import math
import PyInstaller
import shutil
import subprocess
import urllib.request
import zipfile

import diff_archiver

import constants

from tools import bumpup


class build:
	def __init__(self):
		# appVeyorかどうかを判別し、処理をスタート
		appveyor = self.setAppVeyor()
		print("Starting build for %s(appveyor mode=%s)" % (constants.APP_NAME, appveyor))

		# パッケージのパスとファイル名を決定
		package_path = os.path.join("dist", os.path.splitext(os.path.basename(constants.STARTUP_FILE))[0])
		if 'APPVEYOR_REPO_TAG_NAME' in os.environ:
			build_filename = os.environ['APPVEYOR_REPO_TAG_NAME']
		else:
			build_filename = 'snapshot'
		print("Will be built as %s" % build_filename)

		# pyinstallerのパスを決定
		if not appveyor:
			pyinstaller_path = "pyinstaller.exe"
		else:
			pyinstaller_path = "%PYTHON%\\Scripts\\pyinstaller.exe"
		print("pyinstaller_path=%s" % pyinstaller_path)
		hooks_path = os.path.join(PyInstaller.__path__[0], "hooks/")
		print("hooks_path is %s" % (hooks_path))

		# localeフォルダの存在を確認
		if not os.path.exists("locale"):
			print("Error: no locale folder found. Your working directory must be the root of the project. You shouldn't cd to tools and run this script.")
			exit(-1)

		# 前のビルドをクリーンアップ
		self.clean(package_path)

		# appveyorでのスナップショットの場合はバージョン番号を一時的に書き換え
		if build_filename == "snapshot" and appveyor:
			self.makeSnapshotVersionNumber()

		# ビルド
		self.makeVersionInfo()
		self.build(pyinstaller_path, hooks_path, package_path, build_filename)
		archive_name = "%s-%s.zip" % (constants.APP_NAME, build_filename)

		# スナップショットでなければ
		if build_filename == "snapshot" and not appveyor:
			print("Skipping batch archiving because this is a local snapshot.")
		else:
			patch_name = self.makePatch(build_filename, archive_name)
			if constants.UPDATER_URL is not None:
				self.addUpdater(archive_name)
			self.makePackageInfo(archive_name, patch_name, build_filename)
		print("Build finished!")

	def runcmd(self,cmd):
		proc=subprocess.Popen(cmd.split(), shell=True, stdout=1, stderr=2)
		proc.communicate()
		return proc.poll()

	def setAppVeyor(self):
		if len(sys.argv)>=2 and sys.argv[1]=="--appveyor":
			return True
		return False

	def clean(self,package_path):
		if os.path.isdir(package_path):
			print("Clearling previous build...")
			shutil.rmtree("dist\\")
			shutil.rmtree("build\\")

	def makeSnapshotVersionNumber(self):
		#日本標準時オブジェクト
		JST = datetime.timezone(datetime.timedelta(hours=+9))
		#Pythonは世界標準時のZに対応していないので文字列処理で乗り切り、それを日本標準時に変換
		dt = datetime.datetime.fromisoformat(os.environ["APPVEYOR_REPO_COMMIT_TIMESTAMP"][0:19]+"+00:00").astimezone(JST)
		major = str(dt.year)[2:4]+str(dt.month).zfill(2)
		minor = str(dt.day)
		patch = str(int(math.floor((dt.hour*3600+dt.minute*60+dt.second)/86400*1000)))
		constants.APP_VERSION = major+"."+minor+"."+patch
		constants.APP_LAST_RELEASE_DATE = str(dt.date())
		bumpup.bumpup(major+"."+minor+"."+patch, str(dt.date()))

	def makeVersionInfo(self):
		print("making version info... version="+constants.APP_VERSION)
		with open("tools/baseVersionInfo.txt", mode = "r") as f:
			version_text = f.read()
		version_text = version_text.replace("%FILE_VERSION%", constants.APP_VERSION.replace(".", ","))
		version_text = version_text.replace("%PRODUCT_VERSION%", constants.APP_VERSION.replace(".", ","))
		version_text = version_text.replace("%COMPANY_NAME%", constants.APP_DEVELOPERS)
		version_text = version_text.replace("%FILE_DESCRIPTION%", constants.APP_FULL_NAME)
		version_text = version_text.replace("%FILE_VERSION_TEXT%", constants.APP_VERSION)
		version_text = version_text.replace("%REGAL_COPYRIGHT%", constants.APP_COPYRIGHT_MESSAGE)
		original_file_name = os.path.splitext(os.path.basename(constants.STARTUP_FILE))[0]+".exe"
		version_text = version_text.replace("%ORIGINAL_FILENAME%", original_file_name)
		version_text = version_text.replace("%PRODUCT_NAME%", constants.APP_NAME)
		version_text = version_text.replace("%PRODUCT_VERSION_TEXT%", constants.APP_VERSION)
		with open("version.txt", mode = "w") as f:
			f.write(version_text)

	def build(self,pyinstaller_path, hooks_path, package_path, build_filename):
		print("Building...")
		for hook in constants.NEED_HOOKS:
			shutil.copy(hook, hooks_path)
		if constants.APP_ICON == None:
			ret = self.runcmd("%s --windowed --log-level=ERROR --version-file=version.txt %s" % (pyinstaller_path, constants.STARTUP_FILE))
		else:
			ret = self.runcmd("%s --windowed --log-level=ERROR --version-file=version.txt --icon=%s %s" % (pyinstaller_path, constants.APP_ICON, constants.STARTUP_FILE))
		print("build finished with status %d" % ret)
		if ret != 0:
			sys.exit(ret)

		shutil.copytree("locale\\",os.path.join(package_path, "locale"), ignore=shutil.ignore_patterns("*.po", "*.pot", "*.po~"))
		for item in constants.PACKAGE_CONTAIN_ITEMS:
			if os.path.isdir(item):
				shutil.copytree(item, os.path.join(package_path, item))
			if os.path.isfile(item):
				shutil.copyfile(item, os.path.join(package_path, os.path.basename(item)))
		for elem in glob.glob("public\\*"):
			if os.path.isfile(elem):
				shutil.copyfile(elem, os.path.join(package_path, os.path.basename(elem)))
			else:
				shutil.copytree(elem, os.path.join(package_path, os.path.basename(elem)))
		#end copypublic

		print("deleting temporary version file...")
		os.remove("version.txt")
		os.remove(os.path.splitext(os.path.basename(constants.STARTUP_FILE))[0]+".spec")

		print("Compressing into package...")
		shutil.make_archive("%s-%s" % (constants.APP_NAME, build_filename),'zip','dist')

	def makePatch(self, build_filename, archive_name):
		patch_name = None
		if constants.BASE_PACKAGE_URL is not None:
			print("Making patch...")
			patch_name = "%s-%spatch" % (constants.APP_NAME, build_filename)
			archiver=diff_archiver.DiffArchiver(constants.BASE_PACKAGE_URL, archive_name, patch_name,clean_base_package=True, skip_root = True)
			archiver.work()
		return patch_name

	def addUpdater(self, archive_name):
		print("downloading updater...")
		urllib.request.urlretrieve(constants.UPDATER_URL, "updater.zip")
		print("writing updater...")
		with zipfile.ZipFile("updater.zip", "r") as zip:
			zip.extractall()
		with zipfile.ZipFile(archive_name, mode = "a") as zip:
			zip.write("ionic.zip.dll", "%s/ionic.zip.dll" % (constants.APP_NAME))
			zip.write("updater.exe", "%s/updater.exe" % (constants.APP_NAME))
		os.remove("ionic.zip.dll")
		os.remove("updater.exe")
		os.remove("updater.zip")

	def makePackageInfo(self, archive_name, patch_name, build_filename):
		print("computing hash...")
		with open(archive_name, mode = "rb") as f:
			package_hash = hashlib.sha1(f.read()).hexdigest()
		if constants.BASE_PACKAGE_URL is not None:
			with open(patch_name+".zip", mode = "rb") as f:
				patch_hash = hashlib.sha1(f.read()).hexdigest()
		else:
			patch_hash = None
		print("creating package info...")
		info = {}
		info["package_hash"] = package_hash
		info["patch_hash"] = patch_hash
		info["version"] = constants.APP_VERSION
		info["released_date"] = constants.APP_LAST_RELEASE_DATE
		with open("%s-%s_info.json" % (constants.APP_NAME, build_filename), mode = "w") as f:
			json.dump(info, f)


if __name__ == "__main__":
	build()
