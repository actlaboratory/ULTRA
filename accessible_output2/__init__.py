#2020.09.22 Python3.8対応、platform_util除去対応実施 (yamahubuki)
#2023.12.31 Pyinstaller 6.3 対応 (cat)


from __future__ import absolute_import
import ctypes
import os
import sys
import types


def load_library(libname, cdll=False):
	if hasattr(sys,"frozen"):
		if sys.version_info.major>=3 and sys.version_info.minor>=8:
			os.add_dll_directory(os.path.join(sys._MEIPASS, 'accessible_output2', 'lib'))
		libfile = os.path.join(sys._MEIPASS, 'accessible_output2', 'lib', libname)
	else:
		import inspect
		module_path=os.path.abspath(os.path.dirname(inspect.getmodule(inspect.stack()[0][0]).__file__))
		if sys.version_info.major>=3 and sys.version_info.minor>=8:
			os.add_dll_directory(os.path.join(module_path, 'lib'))
		libfile = os.path.join(module_path, 'lib', libname)
	if cdll:
		return ctypes.cdll[libfile]
	else:
		return ctypes.windll[libfile]

def get_output_classes():
	from . import outputs
	module_type = types.ModuleType
	classes = [m.output_class for m in outputs.__dict__.values() if type(m) == module_type and hasattr(m, 'output_class')]
	return sorted(classes, key=lambda c: c.priority)

def find_datafiles():
	import os
	import platform
	from glob import glob
	import accessible_output2
	if platform.system() != 'Windows':
		return []
	path = os.path.join(accessible_output2.__path__[0], 'lib', '*.dll')
	results = glob(path)
	dest_dir = os.path.join('accessible_output2', 'lib')
	return [(dest_dir, results)]
