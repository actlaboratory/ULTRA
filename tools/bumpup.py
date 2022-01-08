# -*- coding: utf-8 -*-
#Version setter
#Copyright (C) 2020 Yukio Nozawa <personal@nyanchangames.com>
#Copyright (C) 2021 yamahubuki <itiro.ishino@gmail.com>
#Copyright (C) 2021 Hiroki Fujii <hfujii@hisystron.com>

import datetime
import json
import os
import re
import sys

VERSION_FILE_NAME="version.json"

# step1: input next version
def getVersion():
	current = getCurrentVersion()
	print("Current version is %s." % current)
	current=current.split(".")
	next=["0","0","0"]
	if len(sys.argv)==2:
		for i,j in enumerate(["major", "minor", "patch"]):
			if sys.argv[1] == j:
				print("Auto-bumpup %s version." % j)
				next[i]=str(int(current[i])+1)
				return ".".join(next)
			else:
				next[i]=current[i]
		print("Warning: Unrecognized bumpup option %s." % arg)

	next = current
	next[2]=str(int(next[2])+1)
	next=".".join(next)
	inp=input("Type next version (leave blank to use %s): " % next)
	if inp=="": return next
	if re.match(r"\d+\.\d+\.\d+",inp):
		return inp
	else:
		print("Version must be major.minor.patch")
		print("Aborting.")
		sys.exit(1)
	#end abort


# step2: input release date
def getReleaseDate():
	today=str(datetime.date.today())
	inp=input("type next release date (leave blank to use %s): " % today)
	if inp=="": return today
	try:
		dc=datetime.date.fromisoformat(inp)
		return inp
	except:
		print("Invalid date format.")
		print("Aborting.")
		sys.exit(1)
#end abort


# load existing version or default
def getCurrentVersion():
	if os.path.exists(VERSION_FILE_NAME):
		print("Loading version.json...")
		try:
			with open(VERSION_FILE_NAME,"r") as f:
				return json.load(f)["version"]
		except:
			print("Unable to parse %s, using default." % VERSION_FILE_NAME)
			return "1.0.0"
	else:
		print("File not found %s, using default." % VERSION_FILE_NAME)
		return "1.0.0"


#step3: bumpup
#build.pyからも呼び出しているので変更時は注意
def bumpup(v, d):
	v = {
		"version": v,
		"release_date": d,
	}
	with open(VERSION_FILE_NAME, "w") as f:
		json.dump(v,f)
	print("Saved %s." % VERSION_FILE_NAME)
	patch("public/readme.txt",r'バージョン:　　ver\.', r'リリース:　　　', v)
	patch("constants.py",r'APP_VERSION="', r'APP_LAST_RELEASE_DATE="', v)

def patch(filename, version_regexp, release_date_regexp, version_object):
	try:
		with open(filename, "r", encoding="UTF-8") as f:
			c=f.read()
		#end read
		p=re.sub(r"("+version_regexp+r")\d+\.\d+\.\d+",r"\g<1>"+version_object["version"],c)
		p=re.sub(r"("+release_date_regexp+r")\d+\-\d+\-\d+",r"\g<1>"+version_object["release_date"],p)
		with open(filename, "w", encoding="UTF-8") as f:
			f.write(p)
		#end write
		print("Patched %s." % filename)
	except Exception as err:
		print("Cannot patch %s (%s)" % (filename,str(err)))
#end patch

# 直接実行時
if __name__ == "__main__":
	version = getVersion()
	print("Bumpup to: %s" % version)
	dt = getReleaseDate()
	bumpup(version, dt)
