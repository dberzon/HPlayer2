from core.engine.hplayer import Hplayer
from core.engine import network
from core.engine.filemanager import FileManager
import os, sys, types, platform

profilename = os.path.basename(__file__).split('.')[0]

# INIT HPLAYE
hplayer = Hplayer()

# NAME
playerName = network.get_hostname()

# PLAYERS
player = hplayer.addPlayer('mpv','mpv')
player.loop(0)
midi = hplayer.addPlayer('midi','midi')
midi.loop(0)

# player.doLog['events'] = True

# Interfaces
hplayer.addInterface('zyre', 'wlan0')
hplayer.addInterface('http2', 8080)
# hplayer.addInterface('http', 8037)
hplayer.addInterface('keyboard')

if hplayer.isRPi():
	hplayer.addInterface('keypad')
	hplayer.addInterface('gpio', [21], 310)


# DIRECTORY / FILE
if hplayer.isRPi(): base_path = '/data/sync/xpa'
else: base_path = '/home/mgr/Videos'

# FILES
files = FileManager( [base_path] )

# MASTER / SLAVE sequencer
iamLeader = False

# Broadcast Order on OSC/Zyre to other Pi's
#
def broadcast(path, *args):
	if path.startswith('play'):
		hplayer.getInterface('zyre').node.broadcast(path, list(args), 100)   ## WARNING LATENCY !!
	else:
		hplayer.getInterface('zyre').node.broadcast(path, list(args))

# Detect if i am zyre Leader
@hplayer.on('zyre.*')
def leadSequencer(data):
	global iamLeader
	iamLeader = (data['from'] == 'self')

# Receive a sequence command -> do Play !
@hplayer.on('zyre.playdir')
def doPlay(s):
	if type(s) is list: s = s[0]
	player.play( files.selectDir(s)+'/'+playerName+'*' )

# Receive an exit command -> last seq
@hplayer.on('zyre.end')
def doExit(s):
	player.play( files.selectDir(-1)+'/'+playerName+'*' )

# Media end: next dir / or loop (based on directory name)
@player.on('stop')
def endSequence():
	if not iamLeader: 
		return
	if 'loop' in files.currentDir():
		broadcast('playdir', files.currentIndex())
	else:
		broadcast('playdir', files.nextIndex())


# Bind Keypad / GPIO events
#
hplayer.on(['keypad-left'], 				lambda: broadcast('playdir', 1))
hplayer.on(['keypad-up'], 					lambda: broadcast('playdir', 2))
hplayer.on(['keypad-down'], 				lambda: broadcast('playdir', 3))
hplayer.on(['keypad-right'], 				lambda: broadcast('playdir', 4)) 
hplayer.on(['keypad-select', 'gpio21-on'], 	lambda: broadcast('end'))


# Keyboard
#
hplayer.on(['KEY_KP0-down'], 	lambda: broadcast('playdir', 0))
hplayer.on(['KEY_KP1-down'], 	lambda: broadcast('playdir', 1))
hplayer.on(['KEY_KP2-down'], 	lambda: broadcast('playdir', 2))
hplayer.on(['KEY_KP3-down'], 	lambda: broadcast('playdir', 3))
hplayer.on(['KEY_KP4-down'], 	lambda: broadcast('playdir', 4))
hplayer.on(['KEY_KP5-down'], 	lambda: broadcast('playdir', 5))
hplayer.on(['KEY_KP6-down'], 	lambda: broadcast('playdir', 6))
hplayer.on(['KEY_KP7-down'], 	lambda: broadcast('playdir', 7))
hplayer.on(['KEY_KP8-down'], 	lambda: broadcast('playdir', 8))
hplayer.on(['KEY_KP9-down'], 	lambda: broadcast('playdir', 9))
hplayer.on(['KEY_KPENTER-down'], lambda: broadcast('end'))
hplayer.on(['KEY_KPPLUS-down', 	'KEY_KPPLUS-hold'], 	broadcast('volume', player.settings()['volume']+1))
hplayer.on(['KEY_KPMINUS-down', 	'KEY_KPMINUS-hold'], 	broadcast('volume', player.settings()['volume']-1))	



# PATCH Keypad LCD update
def lcd_update(self):
	lines = ["", ""]

	# Line 1 : SCENE + VOLUME
	lines[0] = files.currentDir().ljust(13, ' ')[:13]
	lines[0] += str(self.player.settings()['volume']).rjust(3, ' ')[:3]

	# Line 2 : MEDIA
	if not self.player.status()['media']: lines[1] = '-stop-'
	else: lines[1] = os.path.basename(self.player.status()['media'])[:-4]
	lines[1] = lines[1].ljust(14, ' ')[:14]
	lines[1] += str(player.getInterface('zyre').activeCount()).rjust(2, ' ')[:2]

	return lines

if hplayer.isRPi():
	hplayer.getInterface('keypad').update = types.MethodType(lcd_update, hplayer.getInterface('keypad'))



# RUN
hplayer.setBasePath([base_path])        							# Media base path
hplayer.persistentSettings("/data/hplayer2-"+profilename+".cfg")   	# Path to persitent config
hplayer.run()                               						# TODO: non blocking
