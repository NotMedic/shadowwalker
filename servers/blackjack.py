import hashlib
import binascii
import json
import random
from time import time, sleep_ms
from libs.m5_espnow import M5ESPNOW
from hardware import sdcard
from m5stack import lcd, speaker

class Radio:
    def __init__(self):
        self.espnow = M5ESPNOW()
        self.espnow.espnow_init(13, 1)

    def send(self, mac, data):
        self.espnow.espnow_add_peer(mac, 1, 0, False)
        self.espnow.espnow_send_data(1, json.dumps(data))

    def broadcast(self, data):
        self.espnow.espnow_broadcast_data(json.dumps(data))

    def receive(self):
        mac, json_data = self.espnow.espnow_recv_str()
    
        if mac != '':
            #print("Radio received:", mac, json_data)
            data = json.loads(json_data)
            message = Message(self)
            message.source = mac
            message.action_type = data['action']
            message.payload(json.dumps(data['payload']))

            if message.action_type == "newplayer":
                if message.data['class'] in ['Samurai', 'Decker', 'Mage', 'Thug']:
                    player = Player(message.data['name'],message.data['class'], message.source, fromtemplate=True)

                    reply = Message()
                    reply.destination = message.source
                    reply.action('newplayerreply')
                    print(player.tojson())
                    reply.payload(player.tojson())
                    reply.send()

                    speaker.playWAV('/sd/cheer.wav', volume=100)

            else:
                return message
        
    def handleidle(self):
        message = self.receive()

        if message:
            if message.action_type == "newplayer":
                if message.data['class'] in ['Samurai', 'Decker', 'Mage', 'Thug']:
                    player = Player(message.data['name'],message.data['class'], message.source, fromtemplate=True)

                    reply = Message()
                    reply.destination = message.source
                    reply.action('newplayerreply')
                    print(player.tojson())
                    reply.payload(player.tojson())
                    reply.send()

                    speaker.playWAV('/sd/cheer.wav', volume=100)

    def probe(self):
        print('Probing for audience')

        message = Message()
        message.action('probe')
        message.payload('[""]')
        message.broadcast()
        players = []

        start_time = time()

        while True:
            if time() - start_time > 5:  # 5 seconds have passed
                break
            message = self.receive()
            if message and message.action_type == 'probereply':
                #print('Player found', message.source, message.data)
                player=Player().fromjson(json.dumps(message.data))
                print(player.name, player.playerclass)
                player.mac = message.source
                #print("Player Validated:", player.validate(player.mac))

                if (not any(p.mac == player.mac for p in players)) and player.validate(player.mac):
                    players.append(player)

            # elif message and message.action_type == "newplayer":
            #     if message.data['class'] in ['Samurai', 'Decker', 'Mage', 'Thug']:
            #         player = Player(message.data['name'],message.data['class'], message.source, fromtemplate=True)

            #         reply = Message()
            #         reply.destination = message.source
            #         reply.action('newplayerreply')
            #         print(player.tojson())
            #         reply.payload(player.tojson())
            #         reply.send()

        return players
            
class Message:
    def __init__(self, radio=Radio()):
        self.radio = radio
        self.source = None
        self.destination = None
        self.action_type = None 
        self.data = None

    def action(self, action):
        self.action_type = action

    def payload(self, data):
        try:
            self.data = json.loads(data)
        except ValueError:
            raise ValueError("Payload must be a valid JSON string")
        
    def send(self, destination=None, action=None, payload=None):
        destination = destination or self.destination
        action = action or self.action_type
        payload = json.loads(payload) if payload else self.data

        if not destination:
            raise ValueError("Destination must be set before sending message")
        if not action:
            raise ValueError("Action must be set before sending message")
        if not payload:
            raise ValueError("Payload must be set before sending message")

        packet = {'action': action, 'payload': payload}
        self.radio.send(destination, packet)

    def broadcast(self, action=None, payload=None):
        action = action or self.action_type
        payload = json.loads(payload) if payload else self.data

        if not action:
            raise ValueError("Action must be set before sending message")
        if not payload:
            raise ValueError("Payload must be set before sending message")

        packet = {'action': action, 'payload': payload}
        self.radio.broadcast(packet)
    
    def tojson(self):
        return json.dumps({'action': self.action_type, 'payload': self.data})

class Player:
    def __init__(self, name=None, playerclass=None, mac='', fromtemplate=False):
        self.allowed_attributes = {'template', 'sig', 'name', 'playerclass', 'skills', 'chapter', 'experience', 'health', 'armorclass', 'nuyen', 'potions', 'spells', 'vulnerableto', 'attackdie', 'damagedie'}
        
        if fromtemplate:
            self.template = self.TEMPLATES.get(playerclass, {'data': {}, 'sig': None})
            self.fromjson(self.template)
            self.name = name
            self.sig = self.sign(mac)
            
    def __setattr__(self, name, value):
        if name != "allowed_attributes" and name not in self.allowed_attributes:
            raise AttributeError('Invalid attribute: {}'.format(name))
        super().__setattr__(name, value)

    TEMPLATES = {'Samurai': '{"data": {"nm": "SwordRussr", "cl": "Samurai", "cp": 1, "xp": 100, "hp": 100, "ac": 12, "ny": 100, "pots": 3, "sklz": ["Attack", "Heal"]}, "sig": "12345678"}', 
                  'Decker': '{"data": {"nm": "DeckRussr", "cl": "Decker", "cp": 1, "xp": 100, "hp": 100, "ac": 10, "ny": 100, "pots": 3, "sklz": ["Attack", "Heal", "Hack"]}, "sig": "12345678"}', 
                    'Mage': '{"data": {"nm": "MageRussr", "cl": "Mage", "cp": 1, "xp": 100, "hp": 100, "ac": 8, "ny": 100, "pots": 3, "splz": 3, "sklz": ["Attack", "Heal", "Magic"]}, "sig": "12345678"}', 
                    'Thug': '{"data": {"nm": "ThugRussr", "cl": "Thug", "cp": 1, "xp": 100, "hp": 100, "ac": 14, "ny": 100, "pots": 3, "splz": ["Attack", "Heal", "Magic"]}, "sig": "12345678"}'}

    # DICE = {
    #     'Samurai': {'Attack': (1, 20), 'Damage': (3, 6), 'Heal': (1, 6)},
    #     'Decker':  {'Attack': (1, 20), 'Damage': (1, 6), 'Heal': (1, 6), 'Hack': (1, 20)},
    #     'Mage':    {'Attack': (1, 20), 'Damage': (1, 6), 'Heal': (1, 6), 'Magic': (4, 6), 'MagicDamage': (6, 6)},
    #     'Thug':    {'Attack': (1, 20), 'Damage': (1, 12), 'Heal': (1, 6)}
    # }

    @property
    def data(self):

        data = {
            'nm': self.name,
            'cl': self.playerclass,
            'sklz': self.skills,
            'cp': self.chapter,
            'xp': self.experience,
            'hp': self.health,
            'ac': self.armorclass,
            'ny': self.nuyen,
            'pots': self.potions
        }

        if self.playerclass == 'Mage':
            data['splz'] = self.spells

        return data

    def fromjson(self, json_data):
        #print('loading player from json')
        #print(json_data)
        player = json.loads(json_data)
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
        self.vulnerableto = data.get('vulnerableto')
        self.attackdie = data.get('attackdie')
        self.damagedie = data.get('damagedie')
        #print("Loaded Player {}".format(self.name))
        return self

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
            'ac': self.armorclass,
        }

        # Remove keys with None values
        data = {k: v for k, v in data.items() if v is not None}

        return json.dumps({
            'sig': self.sig,
            'data': data
        })
    
    def sign(self, mac):
        secretkey = "1zxc2asd3qwe"

        def sort_object(o):
            if isinstance(o, dict):
                return {k: sort_object(o[k]) for k in sorted(o.keys())}
            if isinstance(o, list):
                return sorted(sort_object(x) for x in o)
            else:
                return o

        data = self.data
        data = {k: v for k, v in data.items() if v is not None}
        sorted_dict = sort_object(data)
        sorted_dict_string = json.dumps(sorted_dict)
        sha_signature = hashlib.sha256((secretkey + mac + sorted_dict_string).encode())
        return binascii.hexlify(sha_signature.digest()).decode()[:8]
    
    def validate(self, mac):
        return self.sig == self.sign(mac)
          
    # def roll(self, action):
    #     if action == 'Attack' and self.attackdie is not None:
    #         num_dice, num_sides = self.attackdie
    #     elif action == 'Damage' and self.damagedie is not None:
    #         num_dice, num_sides = self.damagedie
    #     else:
    #         num_dice, num_sides = self.DICE.get(self.playerclass, {}).get(action, (1, 6))
    #     count = sum(random.randint(1, num_sides) for _ in range(num_dice))
    #     return count, num_dice, num_sides
    
    # def attack(self, target):
    #     print('{} attacks {}'.format(self.name, target.name))
    #     playerroll, num_dice, num_sides = self.roll("Attack")
        
    #     if playerroll == num_dice * num_sides:
    #         crit = True
    #     else :
    #         crit = False

    #     if playerroll == num_dice:
    #         critfail = True
    #     else:
    #         critfail = False

    #     if hasattr(self,'mac'):
    #         status = 'Attacking {}\n'.format(target.name)
    #     else:
    #         status = '{} Attacks You!\n'.format(self.name)

    #     status += 'Attack {}d{}: {}/{}\n'.format(num_dice, num_sides, playerroll, target.armorclass)
    #     print(status)
    #     if playerroll >= target.armorclass:
    #         damage, num_dice, num_sides = self.roll("Damage")
    #         if crit:
    #             damage *= 2
    #             status += 'CRIT! '
    #         target.health -= damage
    #         if target.health < 0:
    #             target.health = 0
    #         #status = status + '{} does {} damage to {}\n'.format(self.name, damage, target.name)
    #         status = status + 'Damage {}d{}: {}\n'.format(num_dice, num_sides, damage)
    #         print(status)
            
    #         print('{} Health: {}'.format(target.name, target.health))
    #     else:
    #         status = status + 'Miss!\n'
    #         print(status)

    #     if hasattr(self,'mac'):
    #         status += '{} Health: {}\nYour Health: {}\n'.format(target.name, target.health, self.health)
    #     else:
    #         status += '{} Health: {}\nYour Health: {}\n'.format(self.name, self.health, target.health)

    #     if target.health <= 0:
    #         status = status + '{} is defeated\n'.format(target.name)

    #         if hasattr(self,'mac') and not target.nuyen == 0: #This means we're a real human player
    #             self.nuyen += target.nuyen
    #             #status = status + '{} has gained {} nuyen from target.name\n'.format(self.name, target.nuyen)
    #             target.nuyen = 0
    #         print(status)

    #         if hasattr(self,'mac') and not target.experience == 0: #This means we're a real human player
    #             self.experience += target.experience
    #             #status = status + '{} has gained {} experience from target.name\n'.format(self.name, target.nuyen)
    #         print(status)

    #     return status
            
    # def hack(self, target):
    #     print('{} hacks {}'.format(self.name, target.name))
    #     playerroll, num_dice, num_sides = self.roll("Hack")

    #     if playerroll == num_dice * num_sides:
    #         crit = True
    #     else :
    #         crit = False

    #     if playerroll == num_dice:
    #         critfail = True
    #     else:
    #         critfail = False

    #     status = 'Hacking {}\nHack {}d{}: {}/{}\n'.format(target.name, num_dice, num_sides, playerroll, target.armorclass)
    #     print(status)
    #     if playerroll >= target.armorclass:
    #         damage, num_dice, num_sides = self.roll("Damage")

    #         if crit:
    #             damage *= 2
    #             status += 'CRIT! '
    #         target.health -= damage
    #         if target.health < 0:
    #             target.health = 0
    #         status = status + 'Damage {}d{}: {}\n'.format(num_dice, num_sides, damage)
    #         print(status)
            
    #         print('{} has {} health left'.format(target.name, target.health))
    #     else:
    #         status = status + 'Miss!\n'
    #         print(status)

    #     if hasattr(self,'mac'):
    #         status += '{} Health: {}\nYour Health: {}\n'.format(target.name, target.health, self.health)
    #     else:
    #         status += '{} Health: {}\nYour Health: {}\n'.format(self.name, self.health, target.health)
        
    #     return status
    
    # def magic(self, target):
    #     if self.spells > 0:
    #         print('{} casts a spell on {}'.format(self.name, target.name))
    #         playerroll, num_dice, num_sides = self.roll("Magic")

    #         if playerroll == num_dice * num_sides:
    #             crit = True
    #         else :
    #             crit = False

    #         if playerroll == num_dice:
    #             critfail = True
    #         else:
    #             critfail = False

    #         status = 'Magic on {}\nMagic {}d{}: {}/{}\n'.format(target.name, num_dice, num_sides, playerroll, target.armorclass)
    #         print(status)
    #         self.spells -= 1
    #         if playerroll >= target.armorclass:
    #             if crit:
    #                 damage *= 2
    #                 status += 'CRIT! '
            
    #             damage, num_dice, num_sides = self.roll("MagicDamage")
    #             target.health -= damage
    #             if target.health < 0:
    #                 target.health = 0
    #             status = status + 'Damage {}d{}: {}\n'.format(num_dice, num_sides, damage)
    #             print(status)
    #             print('{} has {} health left'.format(target.name, target.health))
    #         else:
    #             status = status + 'Miss!\n'
    #             print(status)
    #     else:
    #         status = 'Casting Magic on {}\n{} has no spells left\n'.format(target.name, self.name)

    #     if hasattr(self,'mac'):
    #         status += '{} Health: {}\nYour Health: {}\n'.format(target.name, target.health, self.health)
    #     else:
    #         status += '{} Health: {}\nYour Health: {}\n'.format(self.name, self.health, target.health)
    #     return status
            
    # def heal(self, target):
    #     if target.health < 100:
    #         if self.potions > 0:
    #             self.potions -= 1
    #             target.health += 10
    #             if target.health > 100:
    #                 target.health = 100
    #             status = 'Healing: {}\n{}\'s Health: {}'.format(target.name, target.name, target.health)
    #             print(status)
    #         else:
    #             status = 'Healing: {}\n{} has no potions left'.format(target.name, self.name)
    #             print(status)
    #     else:
    #         status = 'Healing: {}\n{}\'s health is already full'.format(target.name, target.name)
    #         print(status)
    #     return status

class Blackjack:
    def shuffle(self, lst):
        random.seed(int.from_bytes(os.urandom(4), 'big'))
        for i in range(len(lst)-1, 0, -1):
            j = random.randrange(i + 1)  # Get a random index
            lst[i], lst[j] = lst[j], lst[i]  # Swap elements at i and j

    def generate_shoe(self, num_decks):
        # Step 1: Define the ranks, suits and values of a card
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['hearts', 'diamonds', 'clubs', 'spades']

        # Step 2: Create a list for a single deck of cards
        deck = [(rank, suit) for rank in ranks for suit in suits]

        # Step 3: Multiply the single deck by 6 to simulate a 6 deck shoe
        shoe = deck * num_decks

        # Step 1: Shuffle the shoe
        self.shuffle(shoe)
        return shoe

    def calculate_omega(self, shoe):
        count = 0
        for card in shoe:
            rank = card[0]
            if rank in ['2', '3', '7']:
                count -= 1
            elif rank in ['4', '5', '6']:
                count -= 2
            elif rank in ['9']:
                count += 1
            elif rank in ['10', 'J', 'Q', 'K']:
                count += 2
            elif rank in ['8', 'A']:
                pass

        # Calculate the number of decks remaining in the shoe
        decks_remaining = len(shoe) / 52

        # Calculate the true count
        true_count = count / decks_remaining if decks_remaining else 0

        return round(true_count, 2)
    
    def get_hand_value(self, hand):
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

    def run(self, radio):
        radio.handleidle()

        #Generate Shoe
        print("Generating Shoe")
        num_decks = 6
        shoe = self.generate_shoe(num_decks)

        try:
            with open ('housebalance.txt', 'r') as f:
                runningbalance = int(f.read())
        except:
            runningbalance = 0


        while True:
            radio.handleidle()
            roundlog = {}
            house = 0

            if len(shoe) < 52:
                print("Shuffling Shoe")
                shoe = self.generate_shoe(num_decks)

            print('Soliciting Bets')
            omega = self.calculate_omega(shoe)
            roundlog['omega'] = omega
            roundlog['cardsleft'] = len(shoe)
            lcd.clear()
            lcd.font(lcd.FONT_DejaVu24)
            lcd.print("Omega:{} Cards:{}\n".format(omega, len(shoe)), 0, 0)
            lcd.print("House: {}\n".format(runningbalance))
            lcd.font(lcd.FONT_DejaVu18)
            roundlog['players'] = []

            message = Message()
            message.action('placeyourbets')
            payload = {"omega": omega}
            message.payload(json.dumps(payload))
            message.broadcast()
            players = []

            start_time = time()
            last_timer_packet = 0
            bet_timer = 15

            while True:
                if time() - start_time > bet_timer:
                    break

                remaining_time = bet_timer - (time() - start_time)
                
                if remaining_time % 5 == 0 and len(players) > 0 and (time() - last_timer_packet >= 1) and remaining_time > 0:
                    for player in players:
                        message = Message()
                        message.action('timer')
                        message.payload(json.dumps(remaining_time))
                        message.destination = player.mac
                        message.send()
                    last_timer_packet = time()

                message = radio.receive()
                if message and message.action_type == 'bet':
                    player=Player().fromjson(json.dumps(message.data))
                    player.bet = message.data['bet']
                    if player.bet < 0:
                        player.bet = player.bet * -1
                    player.mac = message.source
                    if (not any(p.mac == player.mac for p in players)) and player.validate(player.mac) and player.bet <= 1000: #Tilver and Princess Fix
                        players.append(player)
                        print("{} has a balance of {} and bets {}".format(player.name, player.nuyen, player.bet))
                        lcd.print("{} {} {}\n".format((player.name + ' ' * 10)[:10], (str(player.nuyen) + ' ' * 9)[:9], (str(player.bet) + ' ' * 4)[:4]))

                        player.nuyen -= player.bet
                        house += player.bet

                        reply = Message()
                        reply.destination = player.mac
                        reply.action('update')
                        player.sig = player.sign(player.mac)
                        reply.payload(player.tojson())
                        reply.send()

                elif message is not None:
                    print("Unknown packet", message)

            if len(players) == 0:
                print("No players")
                continue

            #print("Player Bets:")
            for player in players:
                player.cards = []
                #print (player.name, player.bet)

            dealer = []

            shoe.pop()

            for _ in range(2):
                for player in players:
                    player.cards.append(shoe.pop())
                dealer.append(shoe.pop())

            for player in players:
                hand = player.cards
                print("{}'s hand: {}".format(player.name, hand))

            print("Dealer's cards: {}".format(dealer))

            #Check for Dealer BlackJack
            #print("Checking for Dealer BlackJack")
            if self.get_hand_value(dealer)[0] == 21:
                print("Dealer has BlackJack! {}".format(dealer))
                for player in players:
                    if self.get_hand_value(player.cards)[0] == 21:
                        print("{} has BlackJack, it's a push. They get their bet of {} back".format(player.name, player.bet))
                        
                        message = Message()
                        message.action('status')
                        message.destination = player.mac
                        message.payload(json.dumps("You both have BlackJack. It's a Push. Your balance is now {} nuyen".format(player.nuyen)))
                        message.send()

                        player.nuyen += player.bet
                        house -= player.bet

                        message = Message()
                        message.destination = player.mac
                        message.action('update')
                        player.sig = player.sign(player.mac)
                        message.payload(player.tojson())
                        message.send()

                    else:
                        message = Message()
                        message.action('hitstayordouble')
                        message.destination = player.mac
                        payload = {}
                        payload['hand'] = player.cards
                        payload['dealer'] = dealer
                        payload['actions'] = []
                        message.payload(json.dumps(payload))
                        message.send()

                        print("{} loses and now has {} nuyen".format(player.name, player.nuyen))
                        message = Message()
                        message.action('status')
                        message.destination = player.mac
                        message.payload(json.dumps("Dealer has BlackJack. You lose. Your balance is now {} nuyen".format(player.nuyen)))
                        message.send()

                    roundlog['players'].append({'name': player.name, 'balance': player.nuyen, 'bet': player.bet, 'hand': player.cards})
                roundlog['dealer'] = dealer
                roundlog['house'] = house
                runningbalance += house

                print(json.dumps(roundlog))
                with open('/sd/log.txt', 'a') as log:
                    log.write(json.dumps(roundlog) + '\n')

                with open ('housebalance.txt', 'w') as f:
                    f.write(str(runningbalance))
                continue

            #Check for BlackJack
            #print("Checking for Player BlackJack")
            for player in players:
                if self.get_hand_value(player.cards)[0] == 21:
                    print("{} has BlackJack! {}".format(player.name, player.cards))
                    player.nuyen += player.bet + (player.bet * 3 // 2)
                    house -= player.bet + (player.bet * 3 // 2)
                    print("{} now has {} nuyen".format(player.name, player.nuyen))

                    message = Message()
                    message.destination = player.mac
                    message.action('update')
                    player.sig = player.sign(player.mac)
                    message.payload(player.tojson())
                    message.send()

                    message = Message()
                    message.action('hitstayordouble')
                    message.destination = player.mac
                    payload = {}
                    payload['hand'] = player.cards
                    payload['dealer'] = [dealer[0]]
                    payload['actions'] = []
                    message.payload(json.dumps(payload))
                    message.send()
                    
                    message = Message()
                    message.action('status')
                    message.destination = player.mac
                    message.payload(json.dumps("BlackJack!. You win! Your balance is now {} nuyen".format(player.nuyen)))
                    message.send()

                    roundlog['players'].append({'name': player.name, 'balance': player.nuyen, 'bet': player.bet, 'hand': player.cards})
                    players.remove(player)

            if len(players) == 0:
                print("All players have busted or have BlackJack")
                roundlog['dealer'] = dealer
                roundlog['house'] = house
                runningbalance += house

                print(json.dumps(roundlog))
                with open('/sd/log.txt', 'a') as log:
                    log.write(json.dumps(roundlog) + '\n')

                with open ('housebalance.txt', 'w') as f:
                    f.write(str(runningbalance))
                continue #Is this right?

            #Send Player Action 
            #print("Sending Player Action")
            for player in players:
                message = Message()
                message.action('hitstayordouble')
                message.destination = player.mac
                payload = {}
                payload['hand'] = player.cards
                payload['dealer'] = [dealer[0]]
                payload['actions'] = ['Hit', 'Stay', 'Double']
                message.payload(json.dumps(payload))
                message.send()

            #Wait for Player Actions
            
            playeractions = {}

            for player in players:
                playeractions[player.mac] = None

            start_time = time()
            last_timer_packet = 0
            action_timer = 30

            while True:
                if time() - start_time > action_timer:
                    for player in players:
                        if playeractions[player.mac] is None:
                            print("Player {} has timed out".format(player.name))
                            players.remove(player)
                    break

                remaining_time = action_timer - (time() - start_time)
                
                if remaining_time % 5 == 0 and len(players) > 0 and (time() - last_timer_packet >= 1) and remaining_time > 0:
                    #print("Remaining Time:", remaining_time)
                    for player in players:
                        message = Message()
                        message.action('timer')
                        message.payload(json.dumps(remaining_time))
                        message.destination = player.mac
                        message.send()
                    last_timer_packet = time()

                if len(playeractions) != 0 and all(action in ['Stay', 'Bust'] for action in playeractions.values()):
                    print("All players have stayed or doubled")
                    break
                message = radio.receive()
                if message and message.action_type == 'blackjackaction':
                    player = None

                    for folk in players:
                        if folk.mac == message.source:
                            player = folk
                            print("Player is", player.name)

                    #print('Player Action', message.source, message.data)
                    playeractions[message.source] = message.data

                    if message.data == 'Stay':
                        print('{} stays'.format(player.name))
                    
                        reply = Message()
                        reply.action('hitstayordouble')
                        reply.destination = message.source
                        payload = {}
                        payload['hand'] = player.cards
                        payload['dealer'] = [dealer[0]]
                        payload['actions'] = []
                        reply.payload(json.dumps(payload))
                        reply.send()

                    elif message.data == 'Double':
                        player.nuyen -= player.bet
                        house += player.bet
                        player.bet = player.bet * 2

                        reply = Message()
                        reply.action('update')
                        reply.destination = player.mac
                        player.sig = player.sign(player.mac)
                        reply.payload(player.tojson())
                        reply.send()

                        print('{} doubles their bet to {}'.format(player.name, player.bet))
                        player.cards.append(shoe.pop())
                        
                        print(player.cards)
                        if self.get_hand_value(player.cards)[1] > 21:
                            print('{} busts'.format(player.name))
                            # player.nuyen -= player.bet
                            # house += player.bet
                            print("{} loses {}, and now has {} nuyen".format(player.name, player.bet, player.nuyen))
                            playeractions[message.source] = 'Bust'

                            # reply = Message()
                            # reply.destination = message.source
                            # reply.action('update')
                            # player.sig = player.sign(player.mac)
                            # reply.payload(player.tojson())
                            # reply.send()

                            reply = Message()
                            reply.action('hitstayordouble')
                            reply.destination = message.source
                            payload = {}
                            payload['hand'] = player.cards
                            payload['dealer'] = dealer
                            payload['actions'] = []
                            reply.payload(json.dumps(payload))
                            reply.send()

                            reply = Message()
                            reply.destination = message.source
                            reply.action('status')
                            reply.payload(json.dumps("Bust!\nYou have {} nuyen".format(player.nuyen)))
                            reply.send()

                            roundlog['players'].append({'name': player.name, 'balance': player.nuyen, 'bet': player.bet, 'hand': player.cards})
                            players.remove(player)

                        else:
                            playeractions[message.source] = 'Stay'

                            reply = Message()
                            reply.action('hitstayordouble')
                            reply.destination = message.source
                            payload = {}
                            payload['hand'] = player.cards
                            payload['dealer'] = [dealer[0]]
                            payload['actions'] = []
                            reply.payload(json.dumps(payload))
                            reply.send()

                    elif message.data == 'Hit':
                        print('{} hits'.format(player.name))
                        player.cards.append(shoe.pop())

                        print(player.cards)
                        if self.get_hand_value(player.cards)[1] > 21:
                            print('{} busts'.format(player.name))
                            # player.nuyen -= player.bet
                            # house += player.bet
                            print("{} loses {}, and now has {} nuyen".format(player.name, player.bet, player.nuyen))
                            playeractions[message.source] = 'Bust'

                            # reply = Message()
                            # reply.destination = message.source
                            # reply.action('update')
                            # player.sig = player.sign(player.mac)
                            # reply.payload(player.tojson())
                            # reply.send()

                            reply = Message()
                            reply.action('hitstayordouble')
                            reply.destination = message.source
                            payload = {}
                            payload['hand'] = player.cards
                            payload['dealer'] = dealer
                            payload['actions'] = []
                            reply.payload(json.dumps(payload))
                            reply.send()

                            reply = Message()
                            reply.destination = message.source
                            reply.action('status')
                            reply.payload(json.dumps("Bust!\nYou have {} nuyen".format(player.nuyen)))
                            reply.send()

                            roundlog['players'].append({'name': player.name, 'balance': player.nuyen, 'bet': player.bet, 'hand': player.cards})
                            players.remove(player)

                        else:
                            reply = Message()
                            reply.action('hitstayordouble')
                            reply.destination = message.source
                            payload = {}
                            payload['hand'] = player.cards
                            payload['dealer'] = [dealer[0]]
                            payload['actions'] = ['Hit', 'Stay']
                            reply.payload(json.dumps(payload))
                            reply.send()

                elif message is not None:
                    print("Unknown packet", message)

            if len(players) == 0:
                roundlog['dealer'] = dealer
                roundlog['house'] = house
                runningbalance += house

                print(json.dumps(roundlog))
                with open('/sd/log.txt', 'a') as log:
                    log.write(json.dumps(roundlog) + '\n')

                with open ('housebalance.txt', 'w') as f:
                    f.write(str(runningbalance))
                continue #Is this right?

            #Dealer's Turn
            #print("Dealer's Turn")
            while True:
                soft_value, hard_value = self.get_hand_value(dealer)
                if hard_value < 17 or (soft_value < 17 and soft_value != hard_value):
                    #print("Dealer hits")
                    dealer.append(shoe.pop())
                    print("Dealer Hits: {}".format(dealer))

                    if self.get_hand_value(dealer)[1] > 21:
                        print("Dealer Busts")
                        break
                else:
                    break

            roundlog['dealer'] = dealer
            #print(dealer)

            for player in players:
                reply = Message()
                reply.action('hitstayordouble')
                reply.destination = player.mac
                payload = {}
                payload['hand'] = player.cards
                payload['dealer'] = dealer
                payload['actions'] = []
                reply.payload(json.dumps(payload))
                reply.send()

            #Determine Winner
            print("Determining Winner")
            dealer_soft_value, dealer_hard_value = self.get_hand_value(dealer)
            print("Dealer Count: {} {}".format(dealer_soft_value, dealer_hard_value))
            
            sleep_ms(2000)

            for player in players:
                player_soft_value, player_hard_value = self.get_hand_value(player.cards)
                print("{} Count: {} {}".format(player.name, player_soft_value, player_hard_value))
            
                # Use the highest value that is less than or equal to 21
                dealer_value = dealer_soft_value if dealer_soft_value <= 21 else dealer_hard_value
                player_value = player_soft_value if player_soft_value <= 21 else player_hard_value

                if player_value > 21:
                    print("{} busts".format(player.name))
                    
                elif dealer_value > 21:
                    print("Dealer Busts")
                    print("{} wins".format(player.name))
                    player.nuyen += player.bet * 2
                    house -= player.bet * 2
                    print("{} now has {} nuyen".format(player.name, player.nuyen))

                    message = Message()
                    message.destination = player.mac
                    message.action('update')
                    player.sig = player.sign(player.mac)
                    message.payload(player.tojson())
                    message.send()

                    message = Message()
                    message.destination = player.mac
                    message.action('status')
                    message.payload(json.dumps("Dealer Busts!\n{} now has {} nuyen".format(player.name, player.nuyen)))
                    message.send()
            
                elif player_value > dealer_value and player_value <= 21:
                    print("{} wins".format(player.name))
                    player.nuyen += player.bet * 2
                    house -= player.bet * 2
                    print("{} now has {} nuyen".format(player.name, player.nuyen))
                    
                    message = Message()
                    message.destination = player.mac
                    message.action('update')
                    player.sig = player.sign(player.mac)
                    message.payload(player.tojson())
                    message.send()

                    message = Message()
                    message.destination = player.mac
                    message.action('status')
                    message.payload(json.dumps("Win!\nYou have {} nuyen".format(player.nuyen)))
                    message.send()

                elif player_value == dealer_value:
                    print("{} has a push".format(player.name))

                    player.nuyen += player.bet
                    house -= player.bet
                    
                    message = Message()
                    message.destination = player.mac
                    message.action('update')
                    player.sig = player.sign(player.mac)
                    message.payload(player.tojson())
                    message.send()

                    message = Message()
                    message.destination = player.mac
                    message.action('status')
                    message.payload(json.dumps("Push.\nYour bet has been returned and you have {} nuyen".format(player.nuyen)))
                    message.send()

                else:
                    print("{} loses".format(player.name))
                    # player.nuyen -= player.bet
                    # house += player.bet
                    print("{} now has {} nuyen".format(player.name, player.nuyen))
                    
                    # message = Message()
                    # message.destination = player.mac
                    # message.action('update')
                    # player.sig = player.sign(player.mac)
                    # message.payload(player.tojson())
                    # message.send()

                    message = Message()
                    message.destination = player.mac
                    message.action('status')
                    message.payload(json.dumps("Lose!\nYou have {} nuyen".format(player.nuyen)))
                    message.send()

                roundlog['players'].append({'name': player.name, 'balance': player.nuyen, 'bet': player.bet, 'hand': player.cards})

            roundlog['house'] = house
            runningbalance += house
            
            print(json.dumps(roundlog))
            with open('/sd/log.txt', 'a') as log:
                log.write(json.dumps(roundlog) + '\n')

            with open ('housebalance.txt', 'w') as f:
                f.write(str(runningbalance))

radio = Radio()

print("Server is running")

while True:
    try:
        blackjack = Blackjack()
        blackjack.run(radio)
    except Exception as e:
        lcd.clear()
        lcd.print("Server has stopped")
        lcd.print(str(e))
        with open('/sd/crash.log', 'a') as log:
            log.write(str(e) + '\n')
        print(e)