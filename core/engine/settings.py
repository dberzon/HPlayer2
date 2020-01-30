from ..module import Module
import pickle
import os

class Settings(Module):

    _settings = {
        'flip':         False,
        'autoplay':     False,
        'loop':         0,              # 0: no loop / 1: loop one / 2: loop all
        'volume':       100,
        'mute':         False,
        'audiomode':    'stereo',
        'pan':          [100,100]
    }

    def __init__(self, hplayer, persistent=None):
        super().__init__(hplayer, 'Settings', 'yellow')

        self._settingspath = persistent
        if self._settingspath and os.path.isfile(self._settingspath):
            try:
                with open(self._settingspath, 'rb') as fd:
                    self._settings = pickle.load(fd)
                self.log('settings loaded:', self._settings)
                for key, value in self._settings.items():
                    self.emit(key, value, self.export())
            except:
                self.log('ERROR loading settings file', self._settingspath)


    def export(self):
        return self._settings.copy()


    def get(self, key):
        if key in self._settings:
            return self._settings[key]
        return None

    def set(self, key, val):
        self._settings[key] = val
        self.emit('updated', self.export())
        self.emit(key, val, self.export())
        self.save()

    def save(self):
        if self._settingspath:
            with open(self._settingspath, 'wb') as fd:
                pickle.dump(self._settings, fd)