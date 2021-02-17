from .base import Output
import pyperclip

class Clipboard(Output):
	def speak(self, text, **options):
		pyperclip.copy(text)
