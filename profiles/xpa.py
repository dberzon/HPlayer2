from core.engine.hplayer import HPlayer2
from core.engine import network

import os, sys, types, platform

profilename = os.path.basename(__file__).split('.')[0]

# DIRECTORY / FILE
if HPlayer2.isRPi(): base_path = '/data/sync/xpa'
else: base_path = '/home/mgr/Videos'

# INIT HPLAYER
hplayer = HPlayer2(base_path, "/data/hplayer2-"+profilename+".cfg")

# PLAYERS
player 	= hplayer.addPlayer('mpv','mpv')
midi 	= hplayer.addPlayer('midi','midi')

# Interfaces
hplayer.addInterface('zyre', 'wlan0')
hplayer.addInterface('http2', 8080)
# hplayer.addInterface('http', 8037)
hplayer.addInterface('keyboard')

if HPlayer2.isRPi():
	hplayer.addInterface('keypad')
	hplayer.addInterface('gpio', [21], 310)




# MASTER / SLAVE sequencer
iamLeader = False

# Broadcast Order on OSC/Zyre to other Pi's
#
def broadcast(path, *args):
	if path.startswith('play'):
		hplayer.interface('zyre').node.broadcast(path, list(args), 100)   ## WARNING LATENCY !!
	else:
		hplayer.interface('zyre').node.broadcast(path, list(args))

# Detect if i am zyre Leader
@hplayer.on('zyre.*')
def leadSequencer(data):
	global iamLeader
	iamLeader = (data['from'] == 'self')

# Receive a sequence command -> do Play !
@hplayer.on('zyre.playdir')
def doPlay(data):
	s = data['args'][0]
	hplayer.playlist.play( hplayer.files.selectDir(s)+'/'+HPlayer2.name()+'*' )

# Receive an exit command -> last seq
@hplayer.on('zyre.end')
def doExit(s):
	hplayer.playlist.play( hplayer.files.selectDir(-1)+'/'+HPlayer2.name()+'*' )

# Media end: next dir / or loop (based on directory name)
@hplayer.on('playlist.end')
# @midi.on('stop')
def endSequence():
	if not iamLeader:  
		return
	if 'loop' in hplayer.files.currentDir():
		broadcast('playdir', hplayer.files.currentIndex())
	else:
		broadcast('playdir', hplayer.files.nextIndex())


# Bind Keypad / GPIO events
#
hplayer.on('keypad.left', 		lambda: broadcast('playdir', 1))
hplayer.on('keypad.up', 		lambda: broadcast('playdir', 2))
hplayer.on('keypad.down', 		lambda: broadcast('playdir', 3))
hplayer.on('keypad.right', 		lambda: broadcast('playdir', 4)) 
hplayer.on('keypad.select', 	lambda: broadcast('end'))
hplayer.on('gpio.21-on', 		lambda: broadcast('end'))


# Keyboard
#
hplayer.on('KEY_KP0-down', 		lambda: broadcast('playdir', 0))
hplayer.on('KEY_KP1-down', 		lambda: broadcast('playdir', 1))
hplayer.on('KEY_KP2-down', 		lambda: broadcast('playdir', 2))
hplayer.on('KEY_KP3-down', 		lambda: broadcast('playdir', 3))
hplayer.on('KEY_KP4-down', 		lambda: broadcast('playdir', 4))
hplayer.on('KEY_KP5-down', 		lambda: broadcast('playdir', 5))
hplayer.on('KEY_KP6-down', 		lambda: broadcast('playdir', 6))
hplayer.on('KEY_KP7-down', 		lambda: broadcast('playdir', 7))
hplayer.on('KEY_KP8-down', 		lambda: broadcast('playdir', 8))
hplayer.on('KEY_KP9-down', 		lambda: broadcast('playdir', 9))
hplayer.on('KEY_KPENTER-down',  lambda: broadcast('end'))

hplayer.on('KEY_KPPLUS-down', 	lambda: broadcast('volume', player.settings()['volume']+1))
hplayer.on('KEY_KPPLUS-hold', 	lambda: broadcast('volume', player.settings()['volume']+1))
hplayer.on('KEY_KPMINUS-down', 	lambda: broadcast('volume', player.settings()['volume']-1))	
hplayer.on('KEY_KPMINUS-hold', 	lambda: broadcast('volume', player.settings()['volume']-1))	



# PATCH Keypad LCD update
def lcd_update(self):
	lines = ["", ""]

	# Line 1 : SCENE + VOLUME
	lines[0] = hplayer.files.currentDir().ljust(13, ' ')[:13]
	lines[0] += str(hplayer.settings.get('volume')).rjust(3, ' ')[:3]

	# Line 2 : MEDIA
	if not player.status()['media']: lines[1] = '-stop-'
	else: lines[1] = os.path.basename(player.status()['media'])[:-4]
	lines[1] = lines[1].ljust(14, ' ')[:14]
	lines[1] += str(hplayer.interface('zyre').activeCount()).rjust(2, ' ')[:2]

	return lines

if hplayer.isRPi():
	hplayer.interface('keypad').update = types.MethodType(lcd_update, hplayer.interface('keypad'))



# RUN
hplayer.run()                               						# TODO: non blocking
