#key map management
#Copyright (C) 2019 Yukio Nozawa <personal@nyanchangames.com>
#Copyright (C) 2019-2020 yamahubuki <itiro.ishino@gmail.com>

import keymapHandlerBase

class KeymapHandler(keymapHandlerBase.KeymapHandlerBase):

	def __init__(self, dict=None, filter=None):
		super().__init__(dict, filter, permitConfrict=permitConfrict)


#�������j���[�ɑ΂���L�[�̊��蓖�Ă̏d�����������ۂ��𒲂ׂ�
#items�ɂ͒��ׂ���AcceleratorEntry�̃��X�g������
def permitConfrict(items,log):
	return False

class KeyFilter(keymapHandlerBase.KeyFilterBase):
	pass

