import mido
import time

import pygame
"""
gamepad MPE pitch wheel
"""
print(mido.get_output_names(), mido.get_input_names())

iport  = mido.open_input('MPKmini2 4')
oport = mido.open_output('seq 2')


pygame.init()

#initialise the joystick module
pygame.joystick.init()

#define screen size
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500

#create game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Joysticks")

#define font
font_size = 30
font = pygame.font.SysFont("Futura", font_size)

#function for outputting text onto the screen
def draw_text(text, font, text_col, x, y):
  img = font.render(text, True, text_col)
  screen.blit(img, (x, y))

#create clock for setting game frame rate
clock = pygame.time.Clock()
FPS = 100

#create empty list to store joysticks
joysticks = []

#create player rectangle
x = 200
y = 200
player = pygame.Rect(x, y, 100, 100)

#define player colour
col = "royalblue"


# MIDI
ref_note = 0
channel_0_pitch = ref_note % 12
channel_3 = (channel_0_pitch + 4) % 12
channel_5 = (channel_0_pitch + 7) % 12
channel_4 = (channel_0_pitch + 5) % 12
channel_0 = (channel_0_pitch) % 12

#game loop
run = True
while run:

  clock.tick(FPS)

  #update background
  screen.fill(pygame.Color("midnightblue"))

  #draw player
  player.topleft = (x, y)
  pygame.draw.rect(screen, pygame.Color(col), player)

  #event handler
  for msg in iport.iter_pending():
    # print(msg)
    if msg.type in ["note_on", "note_off"]:
        pitch =msg.note 
        channel = (pitch % 12 - channel_0_pitch) % 12
        nmsg = msg.copy(channel = channel)
        oport.send(nmsg)
        print(nmsg)

  for event in pygame.event.get():

    # print(event)
    if event.type == pygame.JOYDEVICEADDED:
      joy = pygame.joystick.Joystick(event.device_index)
      joysticks.append(joy)
    #quit program
    if event.type == pygame.QUIT:
      run = False

    for joys in joysticks:
      wheel0 = int(2**12*joys.get_axis(0))
      wheel1 = int(2**13*joys.get_axis(1))
      wheel2 = int(2**13*joys.get_axis(2))
      wheel3 = int(2**13*joys.get_axis(3))

      nmsg = mido.Message(type="pitchwheel", 
                          channel = channel_3, 
                          pitch = wheel0)
      oport.send(nmsg)
      nmsg = mido.Message(type="pitchwheel", 
                          channel = channel_5, 
                          pitch = wheel1)
      oport.send(nmsg)
      nmsg = mido.Message(type="pitchwheel", 
                          channel = channel_4, 
                          pitch = wheel2)
      oport.send(nmsg)
      nmsg = mido.Message(type="pitchwheel", 
                          channel = channel_0, 
                          pitch = wheel3)
      oport.send(nmsg)
      print(nmsg)
      
            
  #update display
  pygame.display.flip()

iport.close()
oport.close()
pygame.quit()


