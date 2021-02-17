#viewObjectUtil for ViewCreator
#Copyright (C) 2019-2020 Hiroki Fujii <hfujii@hisystron.com>


def popArg(kArg, arg, default=None):
    if arg in kArg: return kArg.pop(arg)
    else: return default

def isset(args,keyargs,i,name=None,type=None):
	p = getParam(args,keyargs,i,name)
	if p==None:
		return False
	if type:
		return isinstance(p,type)
	else:
		return p==None

def getParam(args,keyargs,i,name=None):
	#argsの確認
	if len(args)>i:
		return args[i]
	#keyargsの確認
	if name:
		return keyargs.pop(name,None)
