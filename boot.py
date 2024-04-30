import json
import os

class Settings:
    def __init__(self):
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                self.volume = settings['volume']
                self.brightness = settings['brightness']
                self.branch = settings['branch']
                self.updatenow = settings['updatenow']
        except OSError:
            self.volume = 50
            self.brightness = 30
            self.branch = "main"
            self.updatenow = False
            self.save()

    def save(self):
        settings = {'volume': self.volume,
                    'brightness': self.brightness, 
                    'branch': self.branch,
                    'updatenow': self.updatenow
                    }
        with open('settings.json', 'w') as f:
            json.dump(settings, f)

    def brightnessselect(self, screen):
        screen.clear()
        M5TextBox(45, 59, "Brightness", lcd.FONT_DejaVu24, 0xFFFFFF, rotate=0)
        print("Brightness selected")
        brightnessgraph = M5ChartGraph(230, 0, 10, 135, 1, 0, 100, M5ChartGraph.BAR, 0xFFFFFF, 0x000000, 0.5, 5)
        brightnessgraph.addSample(screen.settings.brightness)
        debounce()

        while True:
            if btnB.isPressed():
                debounce()
                screen.increase_brightness()
                brightnessgraph.addSample(screen.settings.brightness)
                print("Brightness:", screen.settings.brightness)
                
            if btnA.isPressed():
                debounce()
                print("Brightness saved:", screen.settings.brightness)
                screen.settings.save()
                break

            sleep_ms(100)

    def volumeselect(self, screen):
        screen.clear()
        M5TextBox(45, 59, "Volume", lcd.FONT_DejaVu24, 0xFFFFFF, rotate=0)
        print("Volume selected")
        volumegraph = M5ChartGraph(230, 0, 10, 135, 1, 0, 100, M5ChartGraph.BAR, 0xFFFFFF, 0x000000, 0.5, 5)
        volumegraph.addSample(screen.settings.volume)
        debounce()

        while True:
            if btnB.isPressed():
                debounce()
                screen.settings.volume = screen.settings.volume + 10 if screen.settings.volume < 100 else 10
                volumegraph.addSample(screen.settings.volume)
                print("Volume:", screen.settings.volume)
                speaker.setVolume(screen.settings.volume)
                speaker.tone(1000, 100)

            if btnA.isPressed():
                debounce()
                print("Volume saved:", screen.settings.volume)
                screen.settings.save()
                break

            sleep_ms(100)

settings = Settings()

if os.stat('main.py')[6] < 20000:
    import updater
    updater.update(force=True, branch=settings.branch)
    import machine
    machine.reset()

if settings.updatenow:
    import updater
    settings.updatenow = False
    settings.save()
    updater.update(force=True, branch=settings.branch)
    import machine
    machine.reset()
