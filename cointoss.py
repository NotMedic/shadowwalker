from m5stack import *
from m5ui import *
from uiflow import *


def coin_flipper():
  import imu
  import random
  lcd.clear()
  print('Coin Flipper')

  imu0 = imu.IMU()

  # statetext = M5TextBox(6, 222, " ", lcd.FONT_DejaVu18, 0xff0000, rotate=270) #M5TextBox(6,20,"State",lcd.FONT_DejaVu18,0xff0000,rotate=0) 
  # result = M5TextBox(61, 180, " ", lcd.FONT_DejaVu40, 0x04f944, rotate=270) #M5TextBox(50,47,"Result",lcd.FONT_DejaVu40,0x04f944,rotate=0)
  # circle1 = M5Circle(70, 245, 32, 0x000080, 0x000080) #M5Circle(-10, 68, 32, 0x000080, 0x000080)
  # label0 = M5TextBox(55, 225, "EXIT", lcd.FONT_Default, 0xffffff, rotate=0) #M5TextBox(11, 55, "EXIT", lcd.FONT_Default, 0xffffff, rotate=90)

  statetext = M5TextBox(6,20,"Ready!",lcd.FONT_DejaVu18,0xff0000,rotate=0) 
  result = M5TextBox(50,47," ",lcd.FONT_DejaVu40,0x04f944,rotate=0)
  circle1 = M5Circle(-10, 68, 32, 0x000080, 0x000080)
  label0 = M5TextBox(11, 55, "EXIT", lcd.FONT_Default, 0xffffff, rotate=90)

  def flip():
    statetext.setText('Wait...')
    Heads = 1
    Tails = 2
    myflip = random.randint(1,2)
    if myflip == Heads:
      result.setText('HEADS')
      #print('HEADS')
    elif myflip == Tails:
      result.setText('TAILS')
      #print('TAILS')
    return myflip

  while True:
    if (imu0.acceleration[0]) > 1 or (imu0.acceleration[1]) > 1:
      flip()
      wait(2)
      statetext.setText('Ready!')

    if btnA.isPressed():
      lcd.clear()
      return

# Call the function
#cointoss.coin_flipper()