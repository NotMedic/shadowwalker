from hashlib import sha256
from binascii import hexlify
import json
from random import choice, randint
from time import time, sleep_ms
from libs.m5_espnow import M5ESPNOW
#from m5stack import speaker


class Encounter:
    def __init__(self, name, chapter, summary, intro_qrcode, outtro_qrcode, phases):
        self.name = name
        self.chapter = chapter
        self.summary = summary
        self.intro_qrcode = intro_qrcode
        self.outtro_qrcode = outtro_qrcode
        self.phases = phases
    
    @classmethod
    def fromjson(cls, data):
        print("loading encounter from json")
        # Create Phase objects from the phase data
        phases = []
        for phase in data['phases']:
            #print(phase)
            phase_obj = Phase.from_json(phase)
            phases.append(phase_obj)
        # Replace the phase data in the dictionary with the Phase objects
        data['phases'] = phases
        print("phases loaded")
        return cls(**data)

    def run(self, players):
        # Send the solicitation
        message = Message()
        message.action('encounter')

        payload = {}
        payload['name'] = self.name
        payload['summary'] = self.summary
        payload['timer'] = 90
        payload['qr'] = self.intro_qrcode
        message.payload(json.dumps(payload))
        print(payload)

        for player in players:
            message.destination = player.mac
            message.send()

        players = []

        print("sent the Encounter message broadcast")

        timer = payload['timer']
        start_time = time()

        #Wait for replies
        while True:
            if time() - start_time > timer:
                break
            message = radio.receive()
            if message and message.action_type == 'joinencounter':
                print('Player joined', message.source, message.data)
                player=Player().fromjson(json.dumps(message.data))
                #print(player.name, player.playerclass)
                player.mac = message.source
                #print("Player Validated:", player.validate(player.mac))

                #If the player doesn't already exist in the list, AND they're valid, add them to the list
                if (not any(p.mac == player.mac for p in players)) and player.validate(player.mac):
                    players.append(player)

        if not players:
            print("No players joined the encounter")
            return


        print("Players:", players)

        # Loop through each phase
        for phase in self.phases:
            #print("This is where we'd run the phases")
            status = phase.run(players)
            if status == "NoResponse":
                return

        # Display the outtro QR code
        print("Encounter Over")
        print("Remaining Players:", players)

        for player in players:
            if player.chapter == self.chapter and player.chapter < 6:
                player.chapter = self.chapter + 1

            if player.potions < 3:
                player.potions += 1

            if player.playerclass == 'Mage':
                if player.spells < 1:
                    player.spells = 1

            message = Message()
            message.destination = player.mac
            message.action('update')
            player.sig = player.sign(player.mac)
            message.payload(player.tojson())
            message.send()

        for player in players:
            message = Message()
            message.action('itsover')
            payload = {}
            payload['name'] = self.name
            payload['reward'] = "Information"
            payload['timer'] = 30
            payload['qr'] = self.outtro_qrcode
            message.payload(json.dumps(payload))
            message.send(player.mac)

        print(self.outtro_qrcode)       

class Phase:
    def __init__(self, name, reward, enemies, allies, status):
        self.name = name
        self.reward = reward
        self.enemies = enemies
        self.allies = allies
        self.status = status
  
    @classmethod
    def from_json(cls, data):
        # Create Player objects from the enemy data
        enemies = []
        allies = []
        if data.get('enemies') is not None:
            for enemy in data['enemies']:
                player = Player().fromjson(json.dumps(enemy))
                print("Successfully Loaded", player.name, "Attack Die", player.attackdie, "Damage Die", player.damagedie)
                enemies.append(player)
            # Replace the enemy data in the dictionary with the Player objects
            data['enemies'] = enemies
        else:
            data['enemies'] = []

        if data.get('allies') is not None:
            for ally in data['allies']:
                player = Player().fromjson(json.dumps(ally))
                print("Successfully Loaded", player.name, "Attack Die", player.attackdie, "Damage Die", player.damagedie)
                allies.append(player)
            # Replace the enemy data in the dictionary with the Player objects
            data['allies'] = allies
        else:
            data['allies'] = []

        return cls(**data)
    
    def generateactionlist(self, players):
        possibleactions = {}
        for enemy in self.enemies:
            #print("Enemy: ", enemy.name, enemy.vulnerableto)
            for vulnerability in enemy.vulnerableto:
                if vulnerability not in possibleactions:
                    possibleactions[vulnerability] = []
                possibleactions[vulnerability].append(enemy.name)
        
        for player in players:
            if player.health < 100:
                if 'Heal' not in possibleactions:
                    possibleactions['Heal'] = []
                possibleactions['Heal'].append(player.name)

        return possibleactions
    
    def sendplayergetactionlist(self, player, actionlist):
        #valid_actions = {action: targets for action, targets in actionlist.items() if action in player.skills}
        valid_actions = {}
        for action, targets in actionlist.items():
            if action in player.skills:
                if action == 'Heal' and player.potions == 0:
                    continue
                if action == 'Magic' and player.spells == 0:
                    continue
                valid_actions[action] = targets

        count = 0

        if valid_actions:
            #print("Player {} has this list of actions and targets {}".format(player.name, valid_actions))
            message = Message()
            message.action_type = 'getaction'
            message.data = valid_actions
            message.destination = player.mac
            #print("Get Action List for {} is {}".format(player.name, message.data))
            message.send()
            count = count + 1
        else:
            message = Message()
            message.action_type = 'status'
            message.data = "There's nothing for you to do.".format(player.name)
            message.destination = player.mac
            #print("Player {} has no valid actions".format(player.name))
            message.send()

        return count

    def run(self, players):
        # print('Starting phase:', self.name)
        # print('Players:', players)
        # print('Enemies:', self.enemies)
        # print('Status:', self.status)
        # print('Reward:', self.reward)

        #Generate the summary of the enemies
        summary = "Enemy Summary\nName       HP      AC\n"
        for enemy in self.enemies:
            summary += "{} {} {}".format((enemy.name + ' ' * 10)[:10], (str(enemy.health) + ' ' * 7)[:7], (str(enemy.armorclass) + ' ' * 2)[:2] + '\n')

        #Send the summary to the players
        for player in players:
            message = Message()
            message.destination = player.mac
            message.action('status')
            message.payload(json.dumps(summary))
            message.send()

        # enemy_groups = [self.enemies[i:i+4] for i in range(0, len(self.enemies), 4)]

        # for enemy_group in enemy_groups:
        #     summary = "Enemy Summary\nName       HP      AC\n"
        #     for enemy in enemy_group:
        #         summary += "{} {} {}".format((enemy.name + ' ' * 10)[:10], (str(enemy.health) + ' ' * 7)[:7], (str(enemy.armorclass) + ' ' * 2)[:2] + '\n')

        #     # Send the summary to the players
        #     for player in players:
        #         message = Message()
        #         message.destination = player.mac
        #         message.action('status')
        #         message.payload(json.dumps(summary))
        #         message.send()

        retrycount = 0
        round = 0
        while len(self.enemies) > 0 and len(players) > 0:
            round = round + 1
            roundlog = {}
            roundlog['round'] = round
            roundlog['players'] = []
            roundlog['allies'] = []
            roundlog['enemies'] = []
            
            #print("getting action lists")
            actionlist = self.generateactionlist(players)
            playeractioncount = 0

            #Send the appropriate action list to each player
            for player in players:
                #print(player.name, player.health)
                #print("Player", player.name, "has", player.health, "health")
                print("Sending {} the action list".format(player.name))
                playeractioncount += self.sendplayergetactionlist(player, actionlist)
            
            print("Player Action Count:", playeractioncount)

            #wait for their replies
            start_time = time()
            playeractions = {}
            #wait for replies
            while True:
                if time() - start_time > 30 or len(playeractions) == playeractioncount :
                    break
                message = radio.receive()
                if message and message.action_type == 'actionreply':
                    for player in players:
                        if player.mac == message.source:
                            player = player
                            break
                        else:
                            print("Who the fuck is this?", message.source)
                    #print("Player is", player.name)

                    #print('Player Action', message.source, message.data)

                    if message.source in playeractions:
                        print("we've already recieved an action from {}".format(message.source))
                        continue

                    playeractions[message.source] = message.data

                    #print("Player Actions", playeractions)
                    #print("Player mac", message.source)

                    playeraction = playeractions.get(message.source)

                    if playeraction:
                        #print("we have player action", playeraction)
                        action = list(playeraction.keys())[0]
                        target = list(playeraction.values())[0]
                        for enemy in self.enemies:
                            if enemy.name == target:
                                target = enemy
                                break
                        if isinstance(target, str):
                            print("No enemy found with name {}, checking players".format(target))
                            for folk in players:
                                if folk.name == target:
                                    target = folk
                                    break

                        if isinstance(target, str):
                            print("No enemy or player found with name {}, maybe an old packet?".format(target))
                            continue
                        #else:
                            #print(player.name, action, target.name)

                        if action == 'Hack':
                            status, playerlog = player.hack(target)
                        elif action == 'Heal':
                            status, playerlog = player.heal(target)
                        elif action == 'Attack':
                            status, playerlog = player.attack(target)
                        elif action == 'Magic':
                            status, playerlog = player.magic(target)

                        roundlog['players'].append(playerlog)

                        message = Message()
                        message.destination = player.mac
                        message.action('status')
                        message.payload(json.dumps(status))
                        message.send()

            #See WTF they're doing
            print(playeractions)

            if not playeractions:
                print("No player action responses")
                retrycount += 1
                if retrycount > 3:
                    print("No player actions after 3 retries")
                    return "NoResponse"
            else:
                retrycount = 0

            #Process Ally actions
            print("Processing Ally Actions")
            print("Allies", self.allies)
            for ally in self.allies:
                target = None
                for enemy in self.enemies:
                    if enemy.name == "Blackwall ICE": #Hack because of memory usage.
                        target = enemy
                        break
                    else:
                        target = choice(self.enemies)
                print("Ally", ally.name, "attacks", target.name)
                status, playerlog = ally.attack(target)

                roundlog['allies'].append(playerlog)

                message = Message()
                message.action('status')
                message.payload(json.dumps(status))

                for player in players:
                    message.destination = player.mac
                    message.send()
            
            #Process Enemy Action
            print("Processing Enemy Actions")
            for enemy in self.enemies:
                #print("Enemy", enemy.name, enemy.health)
                if enemy.health > 0:
                    # vulnerable_players = [player for player in players if any(skill in enemy.vulnerableto for skill in player.skills)]
                    # if vulnerable_players:
                    #     target = choice(vulnerable_players)
                    # else:
                    #     print("No players vulnerable to enemy, picking a random target instead")
                    #     target = choice(players)

                    target = choice(players)
                    print("Enemy", enemy.name, "attacks", target.name)
                    status, playerlog = enemy.attack(target)
                    message = Message()
                    message.destination = target.mac
                    message.action('status')
                    message.payload(json.dumps(status))
                    message.send()
                    
                    roundlog['enemies'].append(playerlog)

                else:
                    print("Enemy", enemy.name, "is dead")
                    self.enemies.remove(enemy)
                    print("Enemies left", len(self.enemies))

            print(roundlog)
            with open('log.txt', 'a') as f:
                f.write(json.dumps(roundlog) + '\n')

            for player in players:
                if player.health <= 0:
                    #Give them credit for the chapter, but remove them from the encounter
                    #if player.chapter == self.chapter:
                    player.chapter = player.chapter + 1
                    
                    #Give them half their health back, but remove half their money
                    player.health = 50
                    player.nuyen = player.nuyen // 2

                    #Send the player an update
                    player.sig = player.sign(player.mac)
                    message = Message()
                    message.destination = player.mac
                    message.action('update')
                    message.payload(player.tojson())
                    message.send()

                    message = Message()
                    message.destination = player.mac
                    message.action('status')
                    message.payload(json.dumps("You're knocked out. It cost you half your nuyen, but you gained half your health back."))
                    message.send()
                    players.remove(player)
                
                else:
                    message = Message()
                    message.destination = player.mac
                    message.action('update')
                    player.sig = player.sign(player.mac)
                    print(player.tojson())
                    message.payload(player.tojson())
                    message.send()

            start_time = time()
            while True:
                current_time = time()
                elapsed_time = current_time - start_time
                if elapsed_time > 5:
                    break

        print("Phase Over")
        for player in players:
            if self.reward.get('xp'):
                experience = self.reward.get('xp') // len(players)
                print('Distributing XP', experience, 'to', player.name)
                player.experience += experience

                message = Message()
                message.destination = player.mac
                message.action('status')
                message.payload(json.dumps("You have gained {} experience.".format(experience)))
                message.send()  

            if self.reward.get('ny'):
                nuyen = self.reward.get('ny') // len(players)
                print('Distributing Nuyen', nuyen, 'to', player.name)
                player.nuyen += nuyen

                message = Message()
                message.destination = player.mac
                message.action('status')
                message.payload(json.dumps("You have gained {} nuyen.".format(nuyen)))
                message.send()

            message=Message()
            message.destination = player.mac
            message.action('update')
            player.sig = player.sign(player.mac)
            message.payload(player.tojson())
            message.send()

            message = Message()
            message.destination = player.mac
            message.action('status')
            message.payload(json.dumps(self.status))
            message.send()    

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
            print("Radio received:", mac, json_data)
            data = json.loads(json_data)
            message = Message(self)
            message.source = mac
            message.action_type = data['action']
            message.payload(json.dumps(data['payload']))
            return message
        
    def handleidle(self):
        message = self.receive()

        if message:
            # print("Message", message.source, message.action_type, message.data)

            if message.action_type == "newplayer":
                if message.data['class'] in ['Samurai', 'Decker', 'Mage', 'Thug']:
                    player = Player(message.data['name'],message.data['class'], message.source, fromtemplate=True)

                    reply = Message()
                    reply.destination = message.source
                    reply.action('newplayerreply')
                    print(player.tojson())
                    reply.payload(player.tojson())
                    reply.send()

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
                print(player.name, player.playerclass, player.chapter)
                player.mac = message.source
                #print("Player Validated:", player.validate(player.mac))

                if (not any(p.mac == player.mac for p in players)) and player.validate(player.mac):
                    players.append(player)

            elif message and message.action_type == "newplayer":
                if message.data['class'] in ['Samurai', 'Decker', 'Mage', 'Thug']:
                    player = Player(message.data['name'],message.data['class'], message.source, fromtemplate=True)

                    reply = Message()
                    reply.destination = message.source
                    reply.action('newplayerreply')
                    print(player.tojson())
                    reply.payload(player.tojson())
                    reply.send()

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

    TEMPLATES = {'Samurai': '{"data": {"nm": "Samurai", "cl": "Samurai", "cp": 1, "xp": 100, "hp": 100, "ac": 12, "ny": 100, "pots": 3, "sklz": ["Attack", "Heal"]}, "sig": "12345678"}', 
                  'Decker': '{"data": {"nm": "Decker", "cl": "Decker", "cp": 1, "xp": 100, "hp": 100, "ac": 10, "ny": 100, "pots": 3, "sklz": ["Attack", "Heal", "Hack"]}, "sig": "12345678"}', 
                    'Mage': '{"data": {"nm": "Mage", "cl": "Mage", "cp": 1, "xp": 100, "hp": 100, "ac": 8, "ny": 100, "pots": 3, "splz": 3, "sklz": ["Attack", "Heal", "Magic"]}, "sig": "12345678"}', 
                    'Thug': '{"data": {"nm": "Thug", "cl": "Thug", "cp": 1, "xp": 100, "hp": 100, "ac": 14, "ny": 100, "pots": 3, "splz": ["Attack", "Heal", "Magic"]}, "sig": "12345678"}'}

    DICE = {
        'Samurai': {'Attack': (1, 20), 'Damage': (3, 6), 'Heal': (1, 6)},
        'Decker':  {'Attack': (1, 20), 'Damage': (1, 6), 'Heal': (1, 6), 'Hack': (1, 20), 'HackDamage': (1, 8)},
        'Mage':    {'Attack': (1, 20), 'Damage': (1, 6), 'Heal': (1, 6), 'Magic': (4, 6), 'MagicDamage': (6, 6)},
        'Thug':    {'Attack': (1, 20), 'Damage': (1, 12), 'Heal': (1, 6)}
    }

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
        sha_signature = sha256((secretkey + mac + sorted_dict_string).encode())
        return hexlify(sha_signature.digest()).decode()[:8]
    
    def validate(self, mac):
        return self.sig == self.sign(mac)
          
    def roll(self, action):
        if action == 'Attack' and self.attackdie is not None:
            num_dice, num_sides = self.attackdie
        elif action == 'Damage' and self.damagedie is not None:
            num_dice, num_sides = self.damagedie
        else:
            num_dice, num_sides = self.DICE.get(self.playerclass, {}).get(action, (1, 6))
        count = sum(randint(1, num_sides) for _ in range(num_dice))
        return count, num_dice, num_sides
    
    def attack(self, target):
        print('{} attacks {}'.format(self.name, target.name))
        playerroll, num_dice, num_sides = self.roll("Attack")
        damage = 0
        
        if playerroll == num_dice * num_sides:
            crit = True
        else :
            crit = False

        if playerroll == num_dice:
            critfail = True
        else:
            critfail = False

        if hasattr(self,'mac'):
            status = 'Attack: {}\n'.format(target.name)
        else:
            status = '{} attacks {}\n'.format(self.name, target.name)

        status += 'Attack {}d{}: {}/{}\n'.format(num_dice, num_sides, playerroll, target.armorclass)
        print(status)
        if playerroll >= target.armorclass:
            damage, num_dice, num_sides = self.roll("Damage")
            if crit:
                damage *= 2
                status += 'CRIT! '
            target.health -= damage
            if target.health < 0:
                target.health = 0
            #status = status + '{} does {} damage to {}\n'.format(self.name, damage, target.name)
            status = status + 'Damage {}d{}: {}\n'.format(num_dice, num_sides, damage)
            print(status)
            
            print('{} Health: {}'.format(target.name, target.health))
        else:
            status = status + 'Miss!\n'
            print(status)

        if hasattr(self,'mac'):
            status += '{} Health: {}\nYour Health: {}\n'.format(target.name, target.health, self.health)
        else:
            status += '{} Health: {}\n{} Health: {}\n'.format(self.name, self.health, target.name, target.health)

        if target.health <= 0:
            status = status + '{} is defeated\n'.format(target.name)

            if hasattr(self,'mac') and not target.nuyen == 0: #This means we're a real human player
                print('{} has gained {} nuyen from {}\n'.format(self.name, target.nuyen, target.name))
                self.nuyen += target.nuyen
                #status = status + '{} has gained {} nuyen from target.name\n'.format(self.name, target.nuyen)
                message = Message()
                message.destination = self.mac
                message.action('status')
                message.payload(json.dumps("You have gained {} Nuyen".format(target.nuyen)))
                message.send()
                target.nuyen = 0
            print(status)

            if hasattr(self,'mac') and not target.experience == 0: #This means we're a real human player
                print('{} has gained {} experience from {}\n'.format(self.name, target.experience, target.name))
                self.experience += target.experience
                #status = status + '{} has gained {} experience from target.name\n'.format(self.name, target.nuyen)
                message = Message()
                message.destination = self.mac
                message.action('status')
                message.payload(json.dumps("You have gained {} experience".format(target.experience)))
                message.send()
                target.experience = 0
            print(status)

        playerlog = {}
        playerlog['name'] = self.name
        playerlog['health'] = self.health
        playerlog['action'] = 'Attack'
        playerlog['target'] = target.name
        playerlog['attackroll'] = playerroll
        playerlog['damage'] = damage

        return status, playerlog
            
    def hack(self, target):
        print('{} hacks {}'.format(self.name, target.name))
        playerroll, num_dice, num_sides = self.roll("Hack")
        damage = 0

        if playerroll == num_dice * num_sides:
            crit = True
        else :
            crit = False

        if playerroll == num_dice:
            critfail = True
        else:
            critfail = False

        status = 'Hack: {}\nHack {}d{}: {}/{}\n'.format(target.name, num_dice, num_sides, playerroll, target.armorclass)
        print(status)
        if playerroll >= target.armorclass:
            damage, num_dice, num_sides = self.roll("HackDamage")

            if crit:
                damage *= 2
                status += 'CRIT! '
            target.health -= damage
            if target.health < 0:
                target.health = 0
            status = status + 'Damage {}d{}: {}\n'.format(num_dice, num_sides, damage)
            print(status)
            
            print('{} has {} health left'.format(target.name, target.health))
        else:
            status = status + 'Miss!\n'
            print(status)

        if hasattr(self,'mac'):
            status += '{} Health: {}\nYour Health: {}\n'.format(target.name, target.health, self.health)
        else:
            status += '{} Health: {}\n{} Health: {}\n'.format(self.name, self.health, target.name, target.health)

        if target.health <= 0:
            status = status + '{} is defeated\n'.format(target.name)

            if hasattr(self,'mac') and not target.nuyen == 0: #This means we're a real human player
                print('{} has gained {} nuyen from {}\n'.format(self.name, target.nuyen, target.name))
                self.nuyen += target.nuyen
                #status = status + '{} has gained {} nuyen from target.name\n'.format(self.name, target.nuyen)
                target.nuyen = 0
            print(status)

            if hasattr(self,'mac') and not target.experience == 0: #This means we're a real human player
                print('{} has gained {} experience from {}\n'.format(self.name, target.experience, target.name))
                self.experience += target.experience
                #status = status + '{} has gained {} experience from target.name\n'.format(self.name, target.nuyen)
                target.experience = 0
            print(status)

        playerlog = {}
        playerlog['name'] = self.name
        playerlog['health'] = self.health
        playerlog['action'] = 'Hack'
        playerlog['target'] = target.name
        playerlog['attackroll'] = playerroll
        playerlog['damage'] = damage
        
        return status, playerlog
    
    def magic(self, target):
        damage = 0
        playerroll = 0
        if self.spells > 0:
            print('{} casts a spell on {}'.format(self.name, target.name))
            playerroll, num_dice, num_sides = self.roll("Magic")

            if playerroll == num_dice * num_sides:
                crit = True
            else :
                crit = False

            if playerroll == num_dice:
                critfail = True
            else:
                critfail = False

            status = 'Magic: {}\nMagic {}d{}: {}/{}\n'.format(target.name, num_dice, num_sides, playerroll, target.armorclass)
            print(status)
            self.spells -= 1
            if playerroll >= target.armorclass:
                if crit:
                    damage *= 2
                    status += 'CRIT! '
            
                damage, num_dice, num_sides = self.roll("MagicDamage")
                target.health -= damage
                if target.health < 0:
                    target.health = 0
                status = status + 'Damage {}d{}: {}\n'.format(num_dice, num_sides, damage)
                print(status)
                print('{} has {} health left'.format(target.name, target.health))
            else:
                status = status + 'Miss!\n'
                print(status)
        else:
            status = 'Magic: {}\n{} has no spells left\n'.format(target.name, self.name)

        if hasattr(self,'mac'):
            status += '{} Health: {}\nYour Health: {}\nSpells Left: {}\n'.format(target.name, target.health, self.health, self.spells)
        else:
            status += '{} Health: {}\nYour Health: {}\n'.format(self.name, self.health, target.health)

        if target.health <= 0:
            status = status + '{} is defeated\n'.format(target.name)

            if hasattr(self,'mac') and not target.nuyen == 0: #This means we're a real human player
                print('{} has gained {} nuyen from {}\n'.format(self.name, target.nuyen, target.name))
                self.nuyen += target.nuyen
                #status = status + '{} has gained {} nuyen from target.name\n'.format(self.name, target.nuyen)
                target.nuyen = 0
            print(status)

            if hasattr(self,'mac') and not target.experience == 0: #This means we're a real human player
                print('{} has gained {} experience from {}\n'.format(self.name, target.experience, target.name))
                self.experience += target.experience
                #status = status + '{} has gained {} experience from target.name\n'.format(self.name, target.nuyen)
                target.experience = 0
            print(status)

        playerlog = {}
        playerlog['name'] = self.name
        playerlog['health'] = self.health
        playerlog['action'] = 'Magic'
        playerlog['target'] = target.name
        playerlog['attackroll'] = playerroll
        playerlog['damage'] = damage

        return status, playerlog
            
    def heal(self, target):
        if target.health < 100:
            if self.potions > 0:
                self.potions -= 1
                target.health += 10
                if target.health > 100:
                    target.health = 100
                status = 'Healing: {}\n{}\'s Health: {}'.format(target.name, target.name, target.health)
                print(status)
            else:
                status = 'Healing: {}\nNo potions left'.format(target.name, self.name)
                print(status)
        else:
            status = 'Healing: {}\n{}\'s health is already full'.format(target.name, target.name)
            print(status)

        return status, None

radio = Radio()
last_probe_time = 0

# # # Load the JSON data
with open('encounter.json') as f:
    encounter_json = json.load(f)

# # # Create an Encounter instance from the JSON data
encounter = Encounter.fromjson(encounter_json)

while True:
    radio.handleidle()

    current_time = time()
    if current_time - last_probe_time >= 30:
        #speaker.tone(1500, 250)
        audience = radio.probe()
        print("Audience:", audience)
        last_probe_time = current_time

        print("Length:", len(audience))

        minplayers = 4

        #See if we have enough players to start the encounter
        if len([player for player in audience if player.chapter == encounter.chapter]) >= minplayers:
            print("{} players".format(len(audience)))
            #Remove players who are not in the current chapter
            audience = [player for player in audience if player.chapter == encounter.chapter]
            encounter.run(audience)

    sleep_ms(200)