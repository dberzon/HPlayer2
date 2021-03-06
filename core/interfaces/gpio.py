from .base import BaseInterface
import RPi.GPIO as GPIO

class GpioInterface (BaseInterface):

    def __init__(self, hplayer, pins, debounce=50, pullupdown='PUP'):
        super().__init__(hplayer, "GPIO")

        self._state = {}
        self._pins = pins
        self._debounce = debounce
        GPIO.setmode(GPIO.BCM)
        if pullupdown == 'PUP':
            GPIO.setup(pins, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        elif pullupdown == 'PDOWN':
            GPIO.setup(pins, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        else:
            GPIO.setup(pins, GPIO.IN)

    # GPIO receiver THREAD
    def listen(self):
        self.log("starting GPIO listener")

        def clbck(pinz):
            #self.log("channel", pinz, "triggered")
            if not GPIO.input(pinz):
                if self._state[pinz]:
                    self.emit(str(pinz)+'-off')
                self.emit(str(pinz)+'-on')
                self.emit(str(pinz), 1)
                self._state[pinz] = True
            else:
                if not self._state[pinz]:
                    self.emit(str(pinz)+'-on')
                self.emit(str(pinz)+'-off')
                self.emit(str(pinz), 0)
                self._state[pinz] = False

        for pin in self._pins:
            # self.log("channel", pin, "watched")
            self._state[pin] = False
            GPIO.add_event_detect(pin, GPIO.BOTH, callback=clbck, bouncetime=self._debounce)

        self.stopped.wait()
