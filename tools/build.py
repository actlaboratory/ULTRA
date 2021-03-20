# -*- coding: utf-8 -*-
#app build tool
#Copyright (C) 2019 Yukio Nozawa <personal@nyanchangames.com>
#Copyright (C) 2019 - 2020 guredora <contact@guredora.com>

import glob
import os
import sys
import subprocess
import shutil
import distutils.dir_util
import PyInstaller
import diff_archiver
import hashlib
import json
import sys
import urllib.request
import zipfile
sys.path.append(os.getcwd())
import constants

def runcmd(cmd):
	proc=subprocess.Popen(cmd.split(), shell=True, stdout=1, stderr=2)
	proc.communicate()

appveyor=False

if len(sys.argv)==2 and sys.argv[1]=="--appveyor":
	appveyor=True
print("Starting build for %s(appveyor mode=%s)" % (constants.APP_NAME, appveyor))
build_filename=os.environ['APPVEYOR_REPO_TAG_NAME'] if 'APPVEYOR_REPO_TAG_NAME' in os.environ else 'snapshot'
print("Will be built as %s" % build_filename)

pyinstaller_path="pyinstaller.exe" if appveyor is False else "%PYTHON%\\Scripts\\pyinstaller.exe"
hooks_path = os.path.join(PyInstaller.__path__[0], "hooks/")
print("hooks_path is %s" % (hooks_path))
print("pyinstaller_path=%s" % pyinstaller_path)
if not os.path.exists("locale"):
	print("Error: no locale folder found. Your working directory must be the root of the project. You shouldn't cd to tools and run this script.")

package_path = os.path.join("dist", os.path.splitext(os.path.basename(constants.STARTUP_FILE))[0])
if os.path.isdir(package_path):
	print("Clearling previous build...")
	shutil.rmtree("dist\\")
	shutil.rmtree("build\\")

print("making version info...")
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
print("Building...")
for hook in constants.NEED_HOOKS:
	shutil.copy(hook, hooks_path)
if constants.APP_ICON == None:
	runcmd("%s --windowed --log-level=ERROR --version-file=version.txt %s" % (pyinstaller_path, constants.STARTUP_FILE))
else:
	runcmd("%s --windowed --log-level=ERROR --version-file=version.txt --icon=%s %s" % (pyinstaller_path, constants.APP_ICON, constants.STARTUP_FILE))
shutil.copytree("locale\\",os.path.join(package_path, "locale"), ignore=shutil.ignore_patterns("*.po", "*.pot", "*.po~"))
for item in constants.PACKAGE_CONTAIN_ITEMS:
	if os.path.isdir(item):
		shutil.copytree(item, os.path.join(package_path, item))
	if os.path.isfile(item):
		shutil.copyfile(item, os.path.join(package_name, os.path.basename(item)))
for elem in glob.glob("public\\*"):
	if os.path.isfile(elem):
		shutil.copyfile(elem, os.path.join(package_path, os.path.basename(elem)))
	else:
		shutil.copytree(elem, os.path.join(package_path, os.path.basename(elem)))
#end copypublic
print("deleting temporary version file...")
os.remove("version.txt")
print("Compressing into package...")
shutil.make_archive("%s-%s" % (constants.APP_NAME, build_filename),'zip','dist')

if build_filename=="snapshot":
	print("Skipping batch archiving because this is a snapshot release.")
else:
	archive_name = "%s-%s.zip" % (constants.APP_NAME, build_filename)
	if constants.BASE_PACKAGE_URL is not None:
		print("Making patch...")
		patch_name = "%s-%spatch" % (constants.APP_NAME, build_filename)
		archiver=diff_archiver.DiffArchiver(constants.BASE_PACKAGE_URL, archive_name, patch_name,clean_base_package=True, skip_root = True)
		archiver.work()
	if constants.UPDATER_URL is not None:
		print("downloading updater...")
		urllib.request.urlretrieve(constants.UPDATER_URL, "updater.zip")
		print("writing updater...")
		with zipfile.ZipFile("updater.zip", "r") as zip:
			zip.extractall()
		with zipfile.ZipFile(archive_name, mode = "a") as zip:
			zip.write("ionic.zip.dll", "%s/ionic.zip.dll" % (constants.APP_NAME))
			zip.write("updater.exe", "%s/updater.exe" % (constants.APP_NAME))
	print("computing hash...")
	with open(archive_name, mode = "rb") as f:
		content = f.read()
		package_hash = hashlib.sha1(content).hexdigest()
	if constants.BASE_PACKAGE_URL is not None:
		with open(patch_name+".zip", mode = "rb") as f:
			content = f.read()
			patch_hash = hashlib.sha1(content).hexdigest()
	print("creating package info...")
	with open("%s-%s_info.json" % (constants.APP_NAME, build_filename), mode = "w") as f:
		info = {}
		info["package_hash"] = package_hash
		if constants.BASE_PACKAGE_URL is not None:
			info["patch_hash"] = patch_hash
		json.dump(info, f)
print("Build finished!")