# -*- coding: utf-8 -*-
#ConfigManager
#Copyright (C) 2019-2020 yamahubuki <itiro.ishino@gmail.com>

import os
import configparser
import logging
from logging import getLogger

import errorCodes

class ConfigManager(configparser.ConfigParser):
	def __init__(self):
		super().__init__(interpolation=None)
		self.identifier="ConfigManager"
		self.log=getLogger(self.identifier)
		self.log.debug("Create config instance")

	def read(self,fileName):
		self.fileName=fileName
		if os.path.exists(fileName):
			self.log.info("read configFile:"+fileName)
			try:
				return super().read(fileName, encoding='UTF-8')
			except configparser.ParsingError:
				self.log.warning("configFile parse failed.")
				return []
		else:
			self.log.warning("configFile not found.")
			return []

	def write(self):
		self.log.info("write configFile:"+self.fileName)
		try:
			with open(self.fileName,"w", encoding='UTF-8') as f: super().write(f)
			return errorCodes.OK
		except PermissionError as e:
			self.log.warning("write failed." + str(e))
			return errorCodes.ACCESS_DENIED
		except FileNotFoundError as e:
			self.log.warning("write failed." + str(e))
			dirName = os.path.dirname(self.fileName)
			self.log.info("try to create directory:"+dirName)
			try:
				os.makedirs(dirName, exist_ok=True)
			except:
				self.log.error("auto directory creation failed.")
				return errorCodes.ACCESS_DENIED
			try:
				with open(self.fileName,"w", encoding='UTF-8') as f: super().write(f)
				return errorCodes.OK
			except:
				self.log.error("save failed.")
				return errorCodes.ACCESS_DENIED

	def __getitem__(self,key):
		try:
			return ConfigSection(super().__getitem__(key))
		except KeyError as e:
			self.log.debug("created new section:"+key)
			self.add_section(key)
			return self.__getitem__(key)

	def getboolean(self,section,key,default=True):
		if type(default)!=bool:
			raise ValueError("default value must be boolean")
		try:
			return super().getboolean(section,key)
		except ValueError:
			self.log.debug("value is not boolean.  return default "+str(default)+" at section "+section+", key "+key)
			self[section][key]=str(default)
			return int(default)
		except configparser.NoOptionError as e:
			self.log.debug("add new boolval "+str(default)+" at section "+section+", key "+key)
			self[section][key]=default
			return default
		except configparser.NoSectionError as e:
			self.log.debug("add new section and boolval "+str(default)+" at section "+section+", key "+key)
			self.add_section(section)
			self.__getitem__(section).__setitem__(key,default)
			return default

	def getint(self,section,key,default=0,min=None,max=None):
		if type(default)!=int:
			raise ValueError("default value must be int")
		if (min!=None and type(min)!=int) or (max!=None and type(max)!=int):
			raise ValueError("min/max value must be int")
		try:
			ret = super().getint(section,key)
			if (min!=None and ret<min) or (max!=None and ret>max):
				self.log.debug("intvalue "+str(ret)+" out of range.  at section "+section+", key "+key)
				self[section][key]=str(default)
				return int(default)
			return ret
		except (configparser.NoOptionError,ValueError) as e:
			self.log.debug("add new intval "+str(default)+" at section "+section+", key "+key)
			self[section][key]=str(default)
			return int(default)
		except configparser.NoSectionError as e:
			self.log.debug("add new section and intval "+str(default)+" at section "+section+", key "+key)
			self.add_section(section)
			self.__getitem__(section).__setitem__(key,str(default))
			return int(default)

	def getstring(self,section,key,default="",selection=None,*, raw=False, vars=None,fallback=None):
		if selection!=None and not hasattr(selection, "__iter__"):
			raise TypeError("selection must be iterable. %s were given." % type(selection))
		ret=self.__getitem__(section)[key]
		if ret=="":
			if default=="":
				self[section][key]=""
				return ""
			else:
				self.log.debug("add default value.  at section "+section+", key "+key)
				self[section][key]=str(default)
				ret=str(default)
				if selection==None:return ret

		if selection!=None and ret not in selection:
			self.log.debug("value "+str(ret)+" not in selection.  at section "+section+", key "+key)
			self[section][key]=str(default)
			ret=str(default)
		return ret

	def add_section(self,name):
		if not self.has_section(name):
			return super().add_section(name)

	def items(self,section):
		try:
			return super().items(section)
		except configparser.NoSectionError:
			return []

class ConfigSection(configparser.SectionProxy):
	def __init__(self,proxy):
		super().__init__(proxy._parser, proxy._name)

	def __getitem__(self,key):
		try:
			return super().__getitem__(key)
		except KeyError:
			self._parser[self._name][key]=""
			return ""

	def __setitem__(self,key,value):
		return super().__setitem__(key,str(value))

