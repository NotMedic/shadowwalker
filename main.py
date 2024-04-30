from m5stack import btnA, btnB, btnC, lcd, speaker, M5pwr
from m5ui import M5ChartGraph, M5TextBox, setScreenColor
from time import time, sleep_ms
from libs.m5_espnow import M5ESPNOW

class BackException(Exception):
    pass

class Screen:
    def __init__(self, settings, width=240, height=135):
        self.settings = settings
        self._brightness = settings.brightness
        self.width = width
        self.height = height
        self.isdim = False
        self.rotation = lcd.LANDSCAPE
        lcd.setRotation(self.rotation)
        setScreenColor(0x000000)

    def clear(self):
        lcd.clear()

    def setScreenColor(self, color):
        setScreenColor(color)

    def setbrightness(self, brightness):
        if brightness == 0 and self.isdim:
            return
        self.settings.brightness = brightness
        M5pwr.brightness(self.settings.brightness)
        self.isdim = brightness == 0

    def increase_brightness(self):
        self.settings.brightness = self.settings.brightness + 10 if self.settings.brightness < 100 else 10
        self.setbrightness(self.settings.brightness)

    def dimscreen(self):
        if not self.isdim:
            print("dimming screen")
            self.clear()
            if player.playerclass == 'Mage':
                classinfo = player.playerclass + ", {} spells".format(player.spells)
            else:
                classinfo = player.playerclass
            playerinfo = "Name: {}\nChapter: {}\nClass: {}\nHealth: {}, {} potions\nArmor Class: {}\nExperience: {}\nNuyen: {}".format(player.name, player.chapter, classinfo, player.health, player.potions, player.armorclass, player.experience, player.nuyen)
            self.draw7lines(playerinfo)
            self.isdim = True

    def printmenu(self, text, title="Menu"):
        M5TextBox(0, 0, title, lcd.FONT_DejaVu24, 0xFFFFFF, rotate=0)

        lcd.drawCircle(-10, 68, 32, 0x000080, 0x000080)
        lcd.font(lcd.FONT_Arial16)
        lcd.print("Ok", 16, 55, 0xffffff, rotate=90)

        lcd.drawCircle(122, 145, 32, 0x000080, 0x000080)
        lcd.font(lcd.FONT_Arial16)
        lcd.print("sel", 107, 120, 0xffffff, rotate=0)

        lcd.font(lcd.FONT_DejaVu24)
        lcd.print(text, 45, 59, 0xffffff, rotate=self.rotation)

    def runmenu(self, menulist, timeout=10, title="Menu"):
        debounce()
        print("running menu: ", [item['text'] for item in menulist])
        self.clear()

        current_item_index = 0
        previous_item = None

        keepalive_timer = time()

        def draw_menu():
            self.clear()
            current_item = menulist[current_item_index]
            self.printmenu(current_item['text'], title)

        draw_menu()

        while True:
            current_item = menulist[current_item_index]
            if current_item != previous_item:
                draw_menu()
                previous_item = current_item

            if btnB.isPressed():
                current_item_index = (current_item_index + 1) % len(menulist)
                keepalive_timer = time()
                debounce()

            if btnC.isPressed():
                current_item_index = (current_item_index - 1) % len(menulist)
                keepalive_timer = time()
                debounce()

            if btnA.isPressed():
                try:
                    return_value = menulist[current_item_index]['function']()
                    print("return value:", return_value)
                    if return_value is not None:
                        return return_value
                    menulist[current_item_index]['function']()
                    keepalive_timer = time()
                    debounce()
                    debounce()
                    draw_menu()
                except BackException:
                    debounce()
                    keepalive_timer = time()
                    lcd.clear()
                    print("back exception, drawing menu")
                    draw_menu()
                    return
                sleep_ms(200)

            if time() - keepalive_timer >= timeout:
                print("timeout reached, exiting menu")
                break

    def keyboard(Title='Enter your text:', Subtitle='< = backspace > = Enter', MaxLength=12):
        lcd.clear()
        M5TextBox(0, 0, Title, lcd.FONT_DejaVu24, 0xFFFFFF, rotate=0)
        M5TextBox(0,24, Subtitle,lcd.FONT_Default, 0xFFFFFF, rotate=0)

        alphabet = [chr(i) for i in range(65, 91)] + [chr(i) for i in range(97, 123)] + ['_'] + ['<'] + ['>']
        entered_text = ""
        current_char_index = 0
        current_label_text = ""

        lcd.drawCircle(-10, 68, 32, 0x000080, 0x000080)
        lcd.font(lcd.FONT_Arial16)
        lcd.print("Ok", 16, 55, 0xffffff, rotate=90)

        lcd.drawCircle(122, 145, 32, 0x000080, 0x000080)
        lcd.font(lcd.FONT_Arial16)
        lcd.print("sel", 107, 120, 0xffffff, rotate=0)

        label0 = M5TextBox(45, 59, entered_text, lcd.FONT_DejaVu24, 0xFFFFFF, rotate=0)

        while True:
            new_text = (entered_text + alphabet[current_char_index] + ' ' * MaxLength)[:MaxLength]

            if current_label_text != new_text:
                label0.setText(new_text)
                current_label_text = new_text

            if btnB.isPressed():
                current_char_index = (current_char_index + 1) % len(alphabet)
                debounce()

            if btnC.isPressed():
                current_char_index = (current_char_index - 1) % len(alphabet)
                debounce()

            if btnA.isPressed():
                if alphabet[current_char_index] == '<':
                    entered_text = entered_text[:-1]
                elif alphabet[current_char_index] == '>':
                    label0.setText(entered_text)
                    return entered_text
                else:
                    entered_text += alphabet[current_char_index]
                debounce()

            if len(entered_text) >= MaxLength:
                return entered_text

    def draw_qr(self, qr):
        lcd.clear()
        lcd.qrcode(qr, 0, 0, 135, 5)

    def draw_qr_with_notes(self, qr, line1, line2, line3, line4, line5):
        lcd.clear()
        lcd.font(lcd.FONT_DefaultSmall, transparent=True)
        lcd.qrcode(qr, 0, 0, 135, 5)
        lcd.print(line1, 137, 0, 0xffffff)
        lcd.print(line2, 137, 18, 0xffffff)
        lcd.print(line3, 137, 36, 0xffffff)
        lcd.print(line4, 137, 54, 0xffffff)
        lcd.print(line5, 137, 72, 0xffffff)

    def draw7lines(self, text):
        lcd.clear()
        M5TextBox(0, 0, self.insert_newlines(text,22), lcd.FONT_DejaVu18, 0xFFFFFF, rotate=0)
        
    def insert_newlines(self, string, line_length):
        lines = string.split('\n')
        new_lines = []
        
        for line in lines:
            words = line.split(' ')
            current_line = ''
            
            for word in words:
                if len(current_line) + len(word) + 1 > line_length:
                    new_lines.append(current_line)
                    current_line = word
                else:
                    current_line = current_line + ' ' + word if current_line else word
            
            new_lines.append(current_line)
        
        return '\n'.join(new_lines)

    def draw_bet_menu(self, player, omega):
        bet_values = [5, 10, 25, 50, 100, 250, 500, 1000]
        bet = bet_values[0]
        lcd.clear()
        lcd.font(lcd.FONT_DejaVu24)
        lcd.print("Place Your Bet", 35, 0, 0xffffff)
        lcd.print("Omega: {}".format(omega), 35, 24, 0xffffff)
        lcd.print("Nuyen: {}".format(player.nuyen), 35, 48, 0xffffff)

        lcd.drawCircle(-10, 68, 32, 0x000080, 0x000080)
        lcd.font(lcd.FONT_Arial16)
        lcd.print("Ok", 16, 55, 0xffffff, rotate=90)

        lcd.drawCircle(122, 145, 32, 0x000080, 0x000080)
        lcd.font(lcd.FONT_Arial16)
        lcd.print("sel", 107, 120, 0xffffff, rotate=0)

        lcd.font(lcd.FONT_DejaVu24)
        lcd.print("Bet: {}".format(bet), 35, 72, 0xffffff)

        start_time = time()
        while True:
            if time() - start_time > 30:
                return None

            if btnB.isPressed():
                debounce()
                bet = bet_values[(bet_values.index(bet) + 1) % len(bet_values)]
                lcd.font(lcd.FONT_DejaVu24)
                lcd.fillRect(35, 72, 200, 24, 0x000000)
                lcd.print("Bet: {}".format(bet), 35, 72, 0xffffff)

            if btnA.isPressed():
                debounce()
                lcd.drawCircle(-10, 68, 32, 0x000000, 0x000000)
                lcd.drawCircle(122, 145, 32, 0x000000, 0x000000)
                M5TextBox(107, 120, "wait", lcd.FONT_Arial16, 0xFFFFFF, rotate=0)
                return bet

            if btnC.isPressed():
                debounce()
                return None

    
    def draw_blackjack(self, dealer_hand, player_hand, actions, highlighted_action="Hit"):
        suit_symbols = {
            'hearts': "\u25c6",
            'diamonds': "\u2666",
            'clubs': "\u2663",
            'spades': "\u2660"
        }

        def get_hand_value(hand):
            soft_value = 0
            hard_value = 0

            for card in hand:
                rank = card[0]
                if rank in 'JQK':
                    soft_value += 10
                    hard_value += 10
                elif rank == 'A':
                    hard_value += 1
                    if soft_value + 11 > 21:
                        soft_value += 1
                    else:
                        soft_value += 11
                else:
                    value = int(rank)
                    soft_value += value
                    hard_value += value

            return soft_value, hard_value

        dealer_display_value = get_hand_value(dealer_hand)[0] if get_hand_value(dealer_hand)[0] <= 21 else get_hand_value(dealer_hand)[1]
        player_display_value = get_hand_value(player_hand)[0] if get_hand_value(player_hand)[0] <= 21 else get_hand_value(player_hand)[1]

        lcd.clear()
        lcd.font(lcd.FONT_DejaVu18)
        lcd.print("Dealer: {}".format(dealer_display_value), 0, 0, 0xffffff)
        lcd.print("Player: {}".format(player_display_value), 120, 0, 0xffffff)

        for i, card in enumerate(dealer_hand):
            card_name, card_suit = card
            lcd.print("{} ".format(card_name), 0, 18 + i*18, 0xffffff)
            x, y = lcd.getCursor()
            lcd.font(lcd.FONT_UNICODE)
            lcd.print(suit_symbols[card_suit], x+ 8, y, 0xffffff)
            lcd.font(lcd.FONT_DejaVu18)

        for i, card in enumerate(player_hand):
            card_name, card_suit = card
            lcd.print("{} ".format(card_name), 120, 18 + i*18, 0xffffff)
            x, y = lcd.getCursor()
            lcd.font(lcd.FONT_UNICODE)
            lcd.print(suit_symbols[card_suit], x + 8, y, 0xffffff)
            lcd.font(lcd.FONT_DejaVu18)

        if actions:
            for i, action in enumerate(actions):
                if action == highlighted_action:
                    lcd.fillRect(i * 80, self.height - 18, 80, 18, color=0x000080)
                    M5TextBox(i * 80, self.height - 18, action, lcd.FONT_DejaVu18, 0xFFFFFF, rotate=0)
                    
                else:
                    lcd.fillRect(i * 80, self.height - 18, 80, 18, color=0x000000)
                    M5TextBox(i * 80, self.height - 18, action, lcd.FONT_DejaVu18, 0xFFFFFF, rotate=0)

            while True:
                if btnB.isPressed():
                    debounce()
                    highlighted_action = actions[(actions.index(highlighted_action) + 1) % len(actions)]

                    for i, action in enumerate(actions):
                        if action == highlighted_action:
                            lcd.fillRect(i * 80, self.height - 18, 80, 18, color=0x000080)
                            M5TextBox(i * 80, self.height - 18, action, lcd.FONT_DejaVu18, 0xFFFFFF, rotate=0)
                            
                        else:
                            lcd.fillRect(i * 80, self.height - 18, 80, 18, color=0x000000)
                            M5TextBox(i * 80, self.height - 18, action, lcd.FONT_DejaVu18, 0xFFFFFF, rotate=0)

                if btnA.isPressed():
                    debounce()
                    return highlighted_action
        else:
            lcd.drawCircle(122, 145, 32, 0x000080, 0x000080)
            while True:
                if btnB.isPressed():
                    lcd.drawCircle(122, 145, 32, 0x000000, 0x000000)
                    M5TextBox(107, 120, "wait", lcd.FONT_Arial16, 0xFFFFFF, rotate=0)
                    debounce()
                    break

class Player:
    def __init__(self, screen):
        try:
            with open('player.json', 'r') as f:
                self.fromjson(f.read())

        except OSError:
            print("Player file not found")
            self.build(screen)

    def save(self):
            print("Saving player to disk")
            with open('player.json', 'w') as f:
                f.write(self.tojson())

    def wipe(self):
        debounce()
        #Ask are you sure?
        lcd.clear()
        lcd.drawCircle(-10, 68, 32, 0x000080, 0x000080)
        lcd.font(lcd.FONT_Arial16)
        lcd.print("Ok", 16, 55, 0xffffff, rotate=90)
        M5TextBox(45, 59, "Are You Sure?", lcd.FONT_DejaVu24, 0xFFFFFF, rotate=0)
        while True:
            if btnA.isPressed():
                debounce()
                try:
                    import os
                    os.remove('player.json')
                except OSError:
                    pass
                import machine
                machine.reset()
            elif btnB.isPressed():
                debounce()
                break
            elif btnC.isPressed():
                debounce()
                break
        pass

            
    def fromjson(self, json_data):
        #print(json_data)
        player = json.loads(json_data)
        print(player)
        self.sig = player.get('sig')
        data = player.get('data')
        self.name = data.get('nm')
        self.playerclass = data.get('cl')
        self.skills = data.get('sklz')
        self.chapter = data.get('cp')
        self.experience = data.get('xp')
        self.health = data.get('hp')
        self.armorclass = data.get('ac')
        self.nuyen = data.get('ny')
        self.potions = data.get('pots')
        self.spells = data.get('splz')
    
    def tojson(self):
        data = {
            'nm': self.name,
            'cl': self.playerclass,
            'sklz': self.skills,
            'cp': self.chapter,
            'xp': self.experience,
            'hp': self.health,
            'ny': self.nuyen,
            'pots': self.potions,
            'splz': self.spells,
            'ac': self.armorclass
        }

        # Remove keys with None values
        data = {k: v for k, v in data.items() if v is not None}

        return json.dumps({
            'sig': self.sig,
            'data': data
        })
    
    def todict(self):
        data = {
            'nm': self.name,
            'cl': self.playerclass,
            'sklz': self.skills,
            'cp': self.chapter,
            'xp': self.experience,
            'hp': self.health,
            'ny': self.nuyen,
            'pots': self.potions,
            'splz': self.spells,
            'ac': self.armorclass
        }

        # Remove keys with None values
        data = {k: v for k, v in data.items() if v is not None}
        return {'sig': self.sig, 'data': data}

    def build(self, screen):
        print("Building player")
        # prompt for player name
        # prompt for player class
        while True:
            player_name = Screen.keyboard(Title='Enter your handle:')
            player_class_menu = [{'text': player_class, 'function': lambda player_class=player_class: player_class} for player_class in ['Decker', 'Samurai', 'Mage']]
            player_class = screen.runmenu(player_class_menu, title="Choose your class:")

            if player_name and player_class:  # Check if player_name and player_class are not None
                player = self.request(player_name, player_class)
                print(player)
                self.save()
                break  # Exit the loop
            else:
                print("Player name and class must be provided.")
        return player

    def request(self, player_name, player_class):
            print("requesting player")
            data = {}
            data['name'] = player_name
            data['class'] = player_class

            packet = {}
            packet['action'] = 'newplayer'
            packet['payload'] = data

            print("waiting for player reply")
            screen.draw7lines("Cloning Player...\nName: {}\nClass: {}".format(player_name, player_class))
            last_request_time = time()
            start_time = time()
            while True:
                current_time = time()
                if current_time - start_time >= 30:
                    print("Returning Unregistered Player")
                    self.fromjson(json.dumps({"data": {"nm": player_name, "cl": "UNSCANNABLE!", "cp": 0, "xp" : 0, "hp": 0, "ac": 0, "ny": 0, "pots" : 0}, "sig": "deadbeef"}))
                    return self
                if current_time - last_request_time >= 5:
                    print(current_time - start_time)
                    now.espnow_broadcast_data(json.dumps(packet))
                    last_request_time = current_time
                mac, json_data = now.espnow_recv_str()
                if mac != '':
                    print(mac, json_data)
                    reply = json.loads(json_data)
                    if reply['action'] == 'newplayerreply':
                        self.fromjson(json.dumps(reply['payload']))
                        return self
                    
    def actionmenu(self):
        return [{'text': skill, 'function': lambda skill=skill: skill} for skill in self.skills]

def blackjack_function():
    if player.playerclass == 'UNSCANNABLE!':
        screen.draw7lines("You're not registered. please go to to the conference area and then Settings->Wipe Player to register")
        lcd.drawCircle(122, 145, 32, 0x000080, 0x000080)
        lcd.print("ack", 107, 120, 0xffffff, rotate=0)

        while True:
            if btnB.isPressed():
                lcd.drawCircle(122, 145, 32, 0x000000, 0x000000)
                M5TextBox(107, 120, "wait", lcd.FONT_Arial16, 0xFFFFFF, rotate=0)
                debounce()
                return

    debounce()
    screen.clear()
    screen.draw7lines("Blackjack\nWaiting for Dealer\nBalance: {}\nGood Luck!".format(player.nuyen))
    while True:
        mac, data = now.espnow_recv_str()

        if btnC.isPressed():
            debounce()
            return

        if mac != '':
            # we have a packet to handle.
            print(mac, data)
            json_data = json.loads(data)

            if json_data['action'] == 'timer':
                timergraph = M5ChartGraph(230, 0, 10, 135, 1, 0, 30, M5ChartGraph.BAR, 0xFFFFFF, 0x000000, 0.5, 5)
                timergraph.addSample(json_data['payload'])

            if json_data['action'] == 'placeyourbets':
                #speaker.tone(1000, 100)
                omega = json_data['payload']['omega']
                bet = screen.draw_bet_menu(player, omega)
                if bet == None:
                    return
                playerdict = player.todict()
                playerdict['bet'] = bet
                packet = {'action': 'bet', 'payload': playerdict}
                print(mac, packet)

                now.espnow_add_peer(mac, 1, 0, False)
                now.espnow_send_data(1, json.dumps(packet))

            elif json_data['action'] == 'hitstayordouble':
                #speaker.tone(1000, 100)
                print(json_data['payload'])
                if json_data['payload']['actions']:
                    action = screen.draw_blackjack(json_data['payload']['dealer'], json_data['payload']['hand'], json_data['payload']['actions'])
                    print("Action", action)

                    packet = {'action': 'blackjackaction', 'payload': action}

                    print("Sending action:", packet)
                    now.espnow_add_peer(mac, 1, 0, False)
                    now.espnow_send_data(1, json.dumps(packet))
                else:
                    screen.draw_blackjack(json_data['payload']['dealer'], json_data['payload']['hand'], json_data['payload']['actions'])

            elif json_data['action'] == 'update':
                print("updating player")
                start_time = time()
                player.fromjson(json.dumps(json_data['payload']))
                player.save()

            elif json_data['action'] == 'status':
                screen.draw7lines(json_data['payload'])
                lcd.drawCircle(122, 145, 32, 0x000080, 0x000080)
                #speaker.tone(1000, 100)

                while True:
                    if btnB.isPressed():
                        lcd.drawCircle(122, 145, 32, 0x000000, 0x000000)
                        M5TextBox(107, 120, "wait", lcd.FONT_Arial16, 0xFFFFFF, rotate=0)
                        debounce()
                        break

            else:
                print("unknown packet state", mac, data)

            mac, data = None, None

def brightness_function():
    debounce()
    print("Brightness selected")
    settings.brightnessselect(screen)
    debounce()
    raise BackException

def volume_function():
    debounce()
    print("Volume selected")
    settings.volumeselect(screen)
    debounce()
    raise BackException

def cointoss_function():
    debounce()
    print("Coin Toss selected")
    import cointoss
    cointoss.coin_flipper()
    debounce()
    raise BackException

def tarot_function():
    debounce()
    print("Tarot selected")
    import tarot
    tarot.tarot_reading()
    debounce()
    raise BackException

def debounce():
    while btnA.isPressed() or btnB.isPressed() or btnC.isPressed():
        pass
    return

def update_function():
    debounce()
    print("Update selected")
    settings.updatenow = True
    settings.save()
    import machine
    machine.reset()

def back_function():
    print("Back selected")
    debounce()
    raise BackException

def settingsmenu_function():
    debounce()
    screen.runmenu(settingsmenu, title="Settings")
    debounce()
    raise BackException

def gamesmenu_function():
    debounce()
    screen.runmenu(localgamesmenu, title="Games")
    debounce()
    raise BackException

def handle_idle_radio(player):
    mac, data = now.espnow_recv_str()

    if mac != '':
        # we have a packet to handle.
        print(mac, data)
        json_data = json.loads(data)

        if json_data['action'] == 'probe':
            handle_probe(mac, json_data, player)
        elif json_data['action'] == 'encounter':
            handle_encounter(mac, json_data, player)
        elif json_data['action'] == 'update':
            player.fromjson(json.dumps(json_data['payload']))
            player.save()
        elif json_data['action'] == 'getaction':
            #We were in an encounter, but got disconnected. Lets try to rejoin.
            json_data['payload']['name'] = "Rejoin?"
            json_data['payload']['summary'] = "Rejoin the encounter?"
            json_data['payload']['qr'] = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            json_data['payload']['timer'] = 15
            handle_encounter(mac, json_data, player)
        else:
            print("unknown packet state", mac, data)
        mac, data = None, None

def handle_encounter(mac, json_data, player):
    speaker.tone(1000, 1000)
    screen.isdim = False
    print('handling encounter')
    print(json_data)
    print(json_data['payload']['name'])
    print(json_data['payload']['summary'])
    screen.draw7lines(json_data['payload']['name'] + "\n" + json_data['payload']['summary'] + "\n")

    start_time = time()
    counter = json_data['payload']['timer']
    timergraph = M5ChartGraph(230, 0, 10, 135, 1, 0, counter, M5ChartGraph.BAR, 0xFFFFFF, 0x000000, 0.5, 5)
    timergraph.addSample(start_time - time() + counter)
    last_sample_time = time()

    lcd.drawCircle(122, 145, 32, 0x000080, 0x000080)
    M5TextBox(107, 120, "In!", lcd.FONT_Arial16, 0xFFFFFF, rotate=0)

    while True:
        current_time = time()
        if current_time - last_sample_time >= 1:
            timergraph.addSample(start_time - current_time + counter)
            last_sample_time = current_time
        if time() - start_time > counter:
            print("didn't join in time. returning.")
            lcd.clear()
            return
        
        if btnB.isPressed():
            debounce()
            print("Joining Encounter")
            packet = {'action': 'joinencounter', 'payload': player.todict()}
            print(mac, packet)

            now.espnow_add_peer(mac, 1, 0, False)
            now.espnow_send_data(1, json.dumps(packet))
            break

    print("displaying QR code")
    # lcd.qrcode(json_data['qr'], 0, 0, 135, 3)
    screen.draw_qr_with_notes(json_data['payload']['qr'], "", "", "", "", "")

    while True:
        current_time = time()
        if current_time - last_sample_time >= 1:
            timergraph.addSample(start_time - current_time + counter)
            last_sample_time = current_time

        if time() - start_time > counter - 1:
            break

    print("waiting for encounter messages")
    start_time = time()
    while True:
        if time() - start_time > 180:
            print("No encounter packets in 120 seconds, exiting encounter")
            lcd.clear()
            return
        mac, data = now.espnow_recv_str()

        if mac != '':
            # we have a packet to handle.
            print(mac, data)
            json_data = json.loads(data)

            if json_data['action'] == 'getaction':
                speaker.tone(1000, 100)
                start_time = time()

                actionlist = [{'text': skill, 'function': lambda skill=skill: skill} for skill in json_data['payload'].keys()]
                print("Action List:", actionlist)
                action = screen.runmenu(actionlist, title="Choose an action", timeout=20)

                print("Action", action)
                if action == None:
                    print("No action selected, continuing encounter")
                    continue

                targetlist = [{'text': skill, 'function': lambda skill=skill: skill} for skill in json_data['payload'][action]]
                print("Target List", targetlist)
                target = screen.runmenu(targetlist, title="Choose a target", timeout=10)

                if target == None:
                    print("No target selected, exiting encounter")
                    return

                payload = {action: target}
                packet = {}
                packet['action'] = 'actionreply'
                packet['payload'] = payload
                print("Sending packet:", packet)

                screen.clear()
                print(mac, packet)
                now.espnow_add_peer(mac, 1, 0, False)
                now.espnow_send_data(1, json.dumps(packet))
                mac, data = None, None

            elif json_data['action'] == 'update':
                start_time = time()
                player.fromjson(json.dumps(json_data['payload']))
                player.save()

            elif json_data['action'] == 'status':
                start_time = time()
                screen.draw7lines(json_data['payload'])
                lcd.drawCircle(122, 145, 32, 0x000080, 0x000080)
                lcd.print("ack", 107, 120, 0xffffff, rotate=0)

                while True:
                    if btnB.isPressed():
                        lcd.drawCircle(122, 145, 32, 0x000000, 0x000000)
                        M5TextBox(107, 120, "wait", lcd.FONT_Arial16, 0xFFFFFF, rotate=0)
                        debounce()
                        break

            elif json_data['action'] == 'itsover':
                start_time = time()
                screen.draw_qr_with_notes(json_data['payload']['qr'], "", "", "", "", "")
                sleep_ms(20000)
                return
            
            elif json_data['action'] == 'encounter':
                start_time = time()
                print("Repeated Encounter Message. Ignoring")
                mac, data = None, None

            else:
                print("unknown packet", mac, data)
                mac, data = None, None

def handle_update(mac, json_data):
    print('handling update')

    player.fromjson(json_data['payload'])
    print(player)
    print("saving player")

    #with open('player.json', 'w') as f:
    #    json.dump(player, f)

def handle_probe(mac, json_data, player):
    print('handling probe')

    packet = {'action': 'probereply', 'payload': player.todict()}
    print(mac, packet)
    now.espnow_add_peer(mac, 1, 0, False)
    now.espnow_send_data(1, json.dumps(packet))

screen = Screen(settings)

now = M5ESPNOW()
now.espnow_init(13, 1)

player = Player(screen)
print("Player loaded: ", player.name, player.playerclass)

mainmenu = [{'text': 'Games', 'function': gamesmenu_function},
            {'text': 'Settings', 'function': settingsmenu_function},
            {'text': 'Back', 'function': back_function}
]

localgamesmenu = [{'text': 'Blackjack', 'function': blackjack_function},
                  {'text': 'Coin Toss', 'function': cointoss_function},
                  {'text': 'Tarot', 'function': tarot_function},
                  {'text': 'Back', 'function': back_function}
]

settingsmenu = [{'text': 'Brightness', 'function':brightness_function},
                #{'text': 'Volume', 'function': volume_function},
                {'text': 'Update', 'function': update_function},
                {'text': 'Wipe Player', 'function': player.wipe},
                {'text': 'Back', 'function': back_function}
]
screen.runmenu(mainmenu, title="Main Menu")

while True:
    screen.dimscreen()
    handle_idle_radio(player)

    if btnA.isPressed():
        debounce()
        print("button A pressed")
        print("brightening screen")
        screen.setbrightness(screen.settings.brightness)
        print("running main menu")
        screen.runmenu(mainmenu, title="Main Menu")

    sleep_ms(200)