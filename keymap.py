#key map management
#Copyright (C) 2019 Yukio Nozawa <personal@nyanchangames.com>
#Copyright (C) 2019-2020 yamahubuki <itiro.ishino@gmail.com>

import keymapHandlerBase

class KeymapHandler(keymapHandlerBase.KeymapHandlerBase):

	def __init__(self, dict=None, filter=None):
		super().__init__(dict, filter, permitConfrict=permitConfrict)


#複数メニューに対するキーの割り当ての重複を許すか否かを調べる
#itemsには調べたいAcceleratorEntryのリストを入れる
def permitConfrict(items,log):
	return False

class KeyFilter(keymapHandlerBase.KeyFilterBase):
	pass

