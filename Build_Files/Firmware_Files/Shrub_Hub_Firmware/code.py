#  File: code.py
#  Firmware: Shrub Hub
#  Developed by: Neil Squire Society / Makers Making Change Program
#  Version: v1.0.0 (15 Dec 2025)
#  License: GPL v3.0 or later
#
#  This is the firmware for the Shrub Hub, a low cost, easy to build three switch digital interface
#  that lets a user send keystrokes, mouse clicks, and media control commands to a connected device.
#  The device allows a user to change modes by holding down any switch for a set period of time, and supports switch chording.
#
#  The firmware has a editable settings section that can be used to change settings such as the number of modes, the LED
#  indicator colours for each mode, the amount of time a switch must be held down to switch mode, and the keystrokes used in
#  each mode. This section is clearly marked in the code, and changing anything outside of this section is not recommended.
#  Detailed instructions on how to change the settings can be found in the user guide.
#
#  Copyright (C) 2025 - 2026 Neil Squire Society
#  This program is free software: you can redistribute it and/or modify it under the terms of
#  the GNU General Public License as published by the Free Software Foundation,
#  either version 3 of the License, or (at your option) any later version.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <http://www.gnu.org/licenses/>

# The GitHub repository for this device can be found here, along with the documentation and all project files
# https://github.com/makersmakingchange/Shrub-Hub

# import libraries
import time
import board
import gc
import digitalio
import neopixel
import usb_hid
import microcontroller
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl # For media control
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.mouse import Mouse

# --- HID Keyboard, Mouse, and Media Control and Neopixel Setup ---
keyboard = Keyboard(usb_hid.devices)
mouse = Mouse(usb_hid.devices)
cc = ConsumerControl(usb_hid.devices)
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)

gc.collect()
## SETTINGS ====================================================================================================================
## DO NOT CHANGE ANYTHING ABOVE THIS LINE

#  This section contains the settings that can be changed in the Shrub Hub. Each setting has a short comment identifying it, and what it
#  does, more detailed instructions on each one and how best to change it can be found in the Shrub Hub User Guide, found here
#  https://github.com/makersmakingchange/Shrub-Hub/blob/main/Documentation/Shrub_Hub_User_Guide.pdf
#  Do not change any code outside of this marked settings section.

modeChangeTime = 4 #Number of seconds a switch must be held down to change the mode

numModes = 5 #Number of modes. If adding a new one, make sure to add a new colour in the colourMatrix

# These are the colours for each mode. Each colour is a list of three values, ordered red, green, blue.
# Online RGB calculators can be used to help you determine the correct values for each for a given colour.
# Each of the RGB values can be anywhere from 0 to 255.
# The three values need to be organized in a list with square brackets, seperated by commas, like this: [R, G, B]

colourMatrix = [[0, 128, 128], # Mode 1 = Teal
               [50, 0, 128],  # Mode 2 = Purple
               [50, 60, 0],   # Mode 3 = Yellow
               [0, 60, 0],    # Mode 4 = Green
               [120, 60, 0]]  # Mode 5 = Orange

# Keystrokes used for the different switch and mode combinations
# https://docs.circuitpython.org/projects/hid/en/latest/api.html
# Reference for changing these keycodes
# Keystrokes are stored in a two dimensional matrix of lists. The rows are the modes, and the columns are the buttons
# Each keystroke consists of an identifier, and a list of keycodes. If using a single keystroke, it still must be in a list
# The identifier 1 is used for keystrokes, 2 for mouse clicks, and 3 for media control
# Example valid entries: [1, [Keycode.TAB]], [1, [Keycode.GUI, Keycode.H]], [1, [Keycode.CONTROL, Keycode.SHIFT, Keycode.T]], [2, [Mouse.LEFT_BUTTON]]

# Detailed instructions on how to change the keystroke matrix can be found in the user guide, linked at the bottom of this comment.
# This is the hardest setting to change, make sure to read the user guide before making any changes to reduce the chances of making a mistake
# https://github.com/makersmakingchange/Shrub-Hub/blob/main/Documentation/Shrub_Hub_User_Guide.pdf

keystrokeMatrix = [[[1, [Keycode.ENTER]], [1, [Keycode.SPACE]], [1, [Keycode.TAB]], [1, [Keycode.BACKSPACE]], [1, [Keycode.ESCAPE]]], #teal, Mode 1
                   [[1, [Keycode.F1]], [1, [Keycode.F2]], [1, [Keycode.F3]], [1, [Keycode.F4]], [1, [Keycode.F5]]], #purple, Mode 2
                   [[2, [Mouse.LEFT_BUTTON]], [2, [Mouse.RIGHT_BUTTON]], [2, [Mouse.MIDDLE_BUTTON]], [2, [Mouse.LEFT_BUTTON]], [2, [Mouse.RIGHT_BUTTON]]], #yellow, Mode 3
                   [[1, [Keycode.F13]], [1, [Keycode.F14]], [1, [Keycode.F15]], [1, [Keycode.F16]], [1, [Keycode.F17]]], #green, Mode 4
                   [[3, [ConsumerControlCode.PLAY_PAUSE]], [3, [ConsumerControlCode.VOLUME_INCREMENT]], [3, [ConsumerControlCode.VOLUME_DECREMENT]], [3, [ConsumerControlCode.SCAN_NEXT_TRACK]], [3, [ConsumerControlCode.SCAN_PREVIOUS_TRACK]]]]#orange

# END OF SETTINGS ====================================================================================================================
## DO NOT CHANGE ANYTHING BELOW THIS LINE

DEBOUNCE_TIME = 0.05 #Seconds of delay after sampling the switches to allow for debouncing.
POLLING_RATE  = 0.02 #Delay in the main loop. Seconds between sampling the switches.

# --- Configure TRRS Pins ---
# Set TIP as a driven ground reference for external switches.
tip = digitalio.DigitalInOut(board.TIP)
tip.direction = digitalio.Direction.OUTPUT
tip.value = False # drive low (GND)

sleeve = digitalio.DigitalInOut(board.SLEEVE)
sleeve.direction = digitalio.Direction.INPUT
sleeve.pull = digitalio.Pull.UP

ring_2 = digitalio.DigitalInOut(board.RING_2)
ring_2.direction = digitalio.Direction.INPUT
ring_2.pull = digitalio.Pull.UP

ring_1 = digitalio.DigitalInOut(board.RING_1)
ring_1.direction = digitalio.Direction.INPUT
ring_1.pull = digitalio.Pull.UP

# This section sets the mode from memory on startup
if microcontroller.nvm[0] >= numModes: #If the stored value of mode is outside of the allowable range
    microcontroller.nvm[0]=0 # Reset stored value to the first mode
mode = microcontroller.nvm[0] # set the mode to the last stored value

gc.collect()

#Function Name: keystrokeCompiler
#       Inputs: A entry from the keystrokeMatrix, a list in the format [int, [keycode/mouseclick/mediacontrol]]
#      Outputs: None
#  Description: This function takes an entry from the keystroke matrix and uses it to send the corresponding entry
#               to the connected computer. It reads the first entry in the list to determine if it contains a keystroke,
#               mouse click, or a media control command, then sends each command in the second list to the connected computer.
def keystrokeCompiler(keystrokeEntry):
    # print("Compiling keystroke for entry: ", keystrokeEntry)
    key = keystrokeEntry[0] # this number says if its a keycode, mouse click, or media control
    code = keystrokeEntry[1] #this is the actual set of keycodes/mouse click/etc
    if key == 1:#if its a keystroke
        for e, i in enumerate(code):
            keyboard.press(code[e])#press every keystroke
        time.sleep(0.1)
        keyboard.release_all()#then release
    if key == 2:# if its a mouse click
        for e, i in enumerate(code):
            mouse.press(code[e])#click
        time.sleep(0.1)
        mouse.release_all()#then release
    if key == 3:#if its a media control
        for e, i in enumerate(code):
            cc.press(code[e])#press
        time.sleep(0.1)
        cc.release()#then release

#Function Name: setModeColour
#       Inputs: An integer representing the device mode
#      Outputs: None
#  Description: This function sets the colour of the TRRS NeoPixel. It takes the colourMatrix and uses the mode
#               to get the appropriate RGB list, and then sets the NeoPixel colour to those RGB values
def setModeColour(mode):#sets the neopixel colour based on mode
    pixel.fill(colourMatrix[mode])

#Function Name: incrementMode
#       Inputs: None
#      Outputs: None
#  Description: This function increases the mode by one. If the mode is greater than the number of modes, it resets
#               it to the first mode. The mode is then saved to non volatile memory and then updates the NeoPixel colour
def incrementMode():#move to the next mode
    global mode
    mode = mode + 1 #increase the mode
    if mode > (numModes-1): #if you go over the number of modes
        mode = 0 #start back at the beginning
    microcontroller.nvm[0]= mode #storing mode in memory to save between reboots
    setModeColour(mode) #update the LED
    # print("Mode:", mode)

#Function Name: switchDetection
#       Inputs: None
#      Outputs: An integer that represents the switch or combination of switches that is currently pressed.
#  Description: This function reads the value of the tip, ring 1, and sleeve of the TRRS jack. If any of them read low instead of high,
#               they have been pressed. Based on the combination of switches that have been pressed, it returns a value from 1-7. If no
#               switches have been pressed, it returns a value of 0
def switchDetection():
#    print("switchDetection")
    pressedSwitch = 0 #start with no switch pressed
    if (not ring_1.value) or (not ring_2.value) or (not sleeve.value): #if any of the switches have been pressed
        time.sleep(DEBOUNCE_TIME) #debounce
        if (ring_1.value) and (not ring_2.value) and (sleeve.value): #if just ring 2 switch pressed
            pressedSwitch = 1
        elif (not ring_1.value) and (ring_2.value) and (sleeve.value): #if just ring 1 switch pressed
            pressedSwitch = 2
        elif (ring_1.value) and (ring_2.value) and (not sleeve.value): #if just sleeve switch pressed
            pressedSwitch = 3
        elif (not ring_1.value) and (not ring_2.value) and (sleeve.value): #if ring 1 and ring 2 switches pressed
            pressedSwitch = 4
        elif (not ring_1.value) and (ring_2.value) and (not sleeve.value): #if sleeve and ring 1 switches pressed
            pressedSwitch = 5
        elif (ring_1.value) and (not ring_2.value) and (not sleeve.value): #if ring 2 and sleeve switches pressed
            pressedSwitch = 6
        elif (not ring_1.value) and (not ring_2.value) and (not sleeve.value): #if all switches pressed
            pressedSwitch = 7
    # print("pressedSwitch: ", pressedSwitch)
    return pressedSwitch

#Function Name: handleSwitch
#       Inputs: An integer that represents the switch or combination of switches that is currently pressed.
#      Outputs: None
#  Description: This function determines how long a switch has been held down and either switches the mode or sends a keystroke to the
#               keystrokeCompiler. When a button is first pressed, the LED is turned off. If it is held for more than the mode change time,
#               the LED will turn back on to indicate. When the switch is released, if it was held for more than the mode change time, the
#               mode will change and no other action will be taken. If it was held for less than the mode change time, it uses the mode and
#               the pressed switch to determine the correct entry from the keystrokeMatrix, and sends it to the keystrokeCompiler. Switches 6
#               and seven are currently unused, these switches are ignored if pressed.
def handleSwitch(inputSwitch):
    global mode
    if inputSwitch != 0:
        startTime = time.monotonic()#note the time when the switch was pressed
        pixel.fill((0, 0, 0))  # turn off led
        # print("Start Time: ", startTime)
        while switchDetection() == inputSwitch:#while the switch is pressed down
            if time.monotonic() - startTime > modeChangeTime: #if held for more than 4 seconds
                setModeColour(mode) #turn the LED back on
            time.sleep(0.5) # wait to give user time to release chorded switches
            continue
        endTime = time.monotonic()#note when switch was released
        # print("End Time: ", endTime)
        # print("Time Delta: ", (endTime - startTime))
        if endTime - startTime > modeChangeTime:#if held for more than 4 seconds
            incrementMode() #change the mode
            # print("Changing Mode")
        else:# if switch was not held for more than 4 seconds
            # print("Calling keystrokeCompiler with mode, switch: ", mode, ", ", inputSwitch)
            # currently throws error if 6 or 7 pressed, so filter them out
            setModeColour(mode)
            if (inputSwitch != 6) and (inputSwitch != 7): #ignore switch 6 or 7 since we don't use them
                keystrokeCompiler(keystrokeMatrix[mode][inputSwitch-1]) #send the appropriate HID packet
            else:
                keystrokeCompiler(keystrokeMatrix[mode][0])

setModeColour(mode)#on startup, activate the LED

while True: #main loop
    handleSwitch(switchDetection()) #check if a switch has been pressed
    time.sleep(POLLING_RATE)  # delay slightly so not constantly sampling
