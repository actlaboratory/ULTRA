# Pipe Module for ULTRA

import namedPipe
import constants
import globalVars

server = None

def startServer():
	global server
	server = namedPipe.Server(constants.PIPE_NAME)
	server.setReceiveCallback(onReceived)
	server.start()

def onReceived(message):
	try:
		globalVars.app.hMainView.events.show()
	except:
		pass

def stopServer():
	global server
	if server == None:
		return
	server.exit()
	server.close()
	server = None

def sendPipe():
	client = namedPipe.Client(constants.PIPE_NAME)
	while True:
		try:
			client.connect()
			client.write(constants.APP_NAME)
			return
		except namedPipe.PipeServerNotFoundError:
			pass
