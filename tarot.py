from m5stack import *
from m5ui import *
from uiflow import *     
import random

#setScreenColor(0x111111)

def tarot_reading():
    import random
    lcd.clear()
    # result5 = M5TextBox(10, 180, " ", lcd.FONT_DejaVu18, 0x04f944, rotate=270)
    # result4 = M5TextBox(33, 180, " ", lcd.FONT_DejaVu18, 0x04f944, rotate=270)
    # result3 = M5TextBox(55, 180, " ", lcd.FONT_DejaVu18, 0x04f944, rotate=270)
    # result2 = M5TextBox(77, 180, " ", lcd.FONT_DejaVu18, 0x04f944, rotate=270)
    # result1 = M5TextBox(99, 180, " ", lcd.FONT_DejaVu18, 0x04f944, rotate=270)
    #circle1 = M5Circle(70, 245, 32, 0x000080, 0x000080)
    #label0 = M5TextBox(55, 225, "EXIT", lcd.FONT_Default, 0xffffff, rotate=0)

    result5 = M5TextBox(50, 23, " ", lcd.FONT_DejaVu18, 0x04f944, rotate=0)
    result4 = M5TextBox(50, 41, " ", lcd.FONT_DejaVu18, 0x04f944, rotate=0)
    result3 = M5TextBox(50, 59, " ", lcd.FONT_DejaVu18, 0x04f944, rotate=0)
    result2 = M5TextBox(50, 77, " ", lcd.FONT_DejaVu18, 0x04f944, rotate=0)
    result1 = M5TextBox(50, 95, " ", lcd.FONT_DejaVu18, 0x04f944, rotate=0)
    circle1 = M5Circle(-10, 68, 32, 0x000080, 0x000080)
    label0 = M5TextBox(11, 55, "Exit", lcd.FONT_Default, 0xffffff, rotate=90)

    cardCount = 5
    lineNum = 0

    def create_tarot_deck():
        suits = ['Cups', 'Pentacles', 'Swords', 'Wands']
        minor_arcana = [{'name': "{} of {}".format(value, suit), 'suit': suit, 'drawn': False}
                        for suit in suits for value in range(1, 15)]
        major_arcana = [{'name': card, 'suit': 'Major Arcana', 'drawn': False}
                        for card in ['The Fool', 'The Magician', 'The High Priestess', 'The Empress', 
                                    'The Emperor', 'The Hierophant', 'The Lovers', 'The Chariot', 
                                    'Strength', 'The Hermit', 'Wheel of Fortune', 'Justice', 
                                    'The Hanged Man', 'Death', 'Temperance', 'The Devil', 'The Tower', 
                                    'The Star', 'The Moon', 'The Sun', 'Judgement', 'The World']]
        
        return major_arcana + minor_arcana

    def draw_card(deck):
        available_cards = [card for card in deck if not card['drawn']]
        if not available_cards:
            return None  # No more cards to draw

        drawn_card = random.choice(available_cards)
        drawn_card['drawn'] = True
        return drawn_card

    def reset_deck(deck):
        for card in deck:
            card['drawn'] = False

    tarot_deck = create_tarot_deck()
    
    while cardCount > 0:
        if cardCount == 5:
            resultout = result5
        elif cardCount == 4:
            resultout = result4
        elif cardCount == 3:
            resultout = result3
        elif cardCount == 2:
            resultout = result2
        else:
            resultout = result1

        cardCount = cardCount - 1
        print(cardCount)
        drawn_card = draw_card(tarot_deck)

        if drawn_card:
            resultout.setText(drawn_card['name'])
            wait(2)
            #print("Drawn card: {}".format(drawn_card['name']))
        else:
            print("No more cards to draw")

        while cardCount == 0:
            print("Waiting on button press to exit...")
            while True:
                if btnA.isPressed():
                    lcd.clear()
                    return

    # Resetting the deck
    reset_deck(tarot_deck)