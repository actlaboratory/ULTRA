# -*- coding: utf-8 -*-
#Version setter
#Copyright (C) 2020 Yukio Nozawa <personal@nyanchangames.com>
import datetime
import json
import os
import re
import sys

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

bump={"major": False, "minor": False, "patch": False}
if len(sys.argv)==2:
	arg=sys.argv[1]
	if arg in bump:
		print("Auto-bumpup %s version." % arg)
		bump[arg]=True
	else:
		print("Warning: Unrecognized bumpup option %s." % arg)
	#end auto bumpup option
#end cmd

VERSION_FILE_NAME="version.json"
v={"version": "1.0.0", "release_date": "undefined"}

#step 1: load existing version
if os.path.exists(VERSION_FILE_NAME):
	print("Loading version.json...")
	try:
		with open(VERSION_FILE_NAME,"r") as f:
			v=json.load(f)
	except:
		print("Unable to parse %s, using default." % VERSION_FILE_NAME)

#step 2: input
print("Current version is %s." % v["version"])
next=v["version"].split(".")
if bump["major"]:
	next[0]=str(int(next[0])+1)
	inp=".".join(next)
elif bump["minor"]:
	next[1]=str(int(next[1])+1)
	inp=".".join(next)
elif bump["patch"]:
	next[2]=str(int(next[2])+1)
	inp=".".join(next)
else:
	next[2]=str(int(next[2])+1)
	next=".".join(next)
	inp=input("Type next version (leave blank to use %s): " % next)
	if inp=="": inp=next
	if not re.match(r"\d+\.\d+\.\d+",inp):
		print("Version must be major.minor.patch")
		print("Aborting.")
		sys.exit(1)
	#end abort
print("Bumpup to: %s" % inp)
v["version"]=inp

#step 3: input release date
today=str(datetime.date.today())
inp=input("type next release date (leave blank to use %s): " % today)
if inp=="": inp=today
try:
	dc=datetime.date.fromisoformat(inp)
except:
	print("Invalid date format.")
	print("Aborting.")
	sys.exit(1)
#end abort

v["release_date"]=inp
with open(VERSION_FILE_NAME, "w") as f:
	json.dump(v,f)

print("Saved %s." % VERSION_FILE_NAME)
patch("public/readme.txt",r'バージョン:　　ver\.', r'リリース:　　　', v)
patch("constants.py",r'APP_VERSION="', r'APP_LAST_RELEASE_DATE="', v)
