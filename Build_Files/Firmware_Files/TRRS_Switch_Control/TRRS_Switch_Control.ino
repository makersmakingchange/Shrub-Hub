/*
 * This code goes with the Adafruit TRRS Trinkey
 * https://www.adafruit.com/product/5954
 * 
 * Connect from 2 to 3 Assistive Technology Buttons and connect it
 * to an iOS or android device using Switch Control
 * 
 * See learn.adafruit.com for details.
 * 
 * All files in his package are open source under Creative Commons CC BY-SA
 * 
 * Developed by Chris Young cy_borg5@cyborg5.com
 * http://tech.cyborg5.com/
 * 
 */
#include <Keyboard.h>
#include <HID.h>
#include <Adafruit_NeoPixel.h>

//Sometimes when you reboot a computer, the attached board glitches.
//Use the SleepyDog library to detect a lockup and reboot if necessary.
#define USE_SLEEPY 1
#if (USE_SLEEPY)
  #include <Adafruit_SleepyDog.h>
#endif

#define MY_DEBUG 0        //change to 1 to turn on debug output to serial monitor
/*
 * Characters to be sent to switch controlled device.
 * You can modify the values to suit your needs.
 */

#define ENTER         10
#define SPACE         32
#define TAB           9
#define BACKSPACE     8
#define ESCAPE        27

#define F1            194
#define F2            195
#define F3            196
#define F4            197
#define F5            198

#define ONE           166
#define TWO           167
#define THREE         168
#define FOUR          169
#define FIVE          170

#define F13           240
#define F14           241
#define F15           242
#define F16           243
#define F17           244

#define LED_BRIGHTNESS           150    
#define LED_PIN                  1  


/***************************
 * Global Variables
 ***************************/
uint8_t Current_Buttons;  //The most recent results from Read_Buttons()
#include "my_stuff.h"
#include "my_inputs.h"

int switchOne[4]   = {ENTER, F1, ONE, F13};
int switchTwo[4]   = {SPACE, F2, TWO, F14};
int switchThree[4] = {TAB, F3, THREE, F15};
int switchFour[4]  = {BACKSPACE, F4, FOUR, F16};
int switchFive[4]  = {ESCAPE, F5, FIVE, F17};



struct rgbColorCode {
    int r;    // red value 0 to 255
    int g;   // green value
    int b;   // blue value
 };

//Color structure 
typedef struct { 
  uint8_t colorNumber;
  String colorName;
  rgbColorCode colorCode;
} colorStruct;

//Color properties 
const colorStruct colorProperty[] {
    {1,"Green",{60,0,0}},
    {2,"Pink",{0,50,40}},
    {3,"Yellow",{60,50,0}},    
    {4,"Orange",{20,60,0}},
    {5,"Blue",{0,0,60}},
    {6,"Red",{0,60,0}},
    {7,"Purple",{0,50,128}},
    {8,"Teal",{128,0,128}}       
};

//Setup NeoPixel LED
Adafruit_NeoPixel ledPixels = Adafruit_NeoPixel(1, PIN_NEOPIXEL, NEO_GRB + NEO_KHZ800);

void Send_Keypress(uint8_t c) {
  Keyboard.press(c);  DEBUG_PRINT("Pressed="); DEBUG_PRINTLN(c);
  delay(100);//de-bounce
  while(Current_Buttons) {  //Keep reading until button designer longer pressed
    Read_Buttons ();
  }
  Keyboard.release(c);;  DEBUG_PRINT("Released="); DEBUG_PRINTLN(c);
};
/*
 * Initialize everything
 */


//***UPDATE RGB LED COLOR FUNCTION***//

void updateLedColor(int modeColour, uint8_t ledBrightness) {
    if(modeColour == 0){
      Serial.println(" Mode: 0 \n Set Colour: Teal");
      ledPixels.setPixelColor(0, 0,128,128);//teal
    }
    else if(modeColour == 1){
      Serial.println(" Mode: 1 \n Set Colour: Purple");
      ledPixels.setPixelColor(0, 50,0,128);//purple
    }
    else if(modeColour == 2){
      Serial.println(" Mode: 2 \n Set Colour: Yellow");
      ledPixels.setPixelColor(0, 50,60,0);//yellow
    }
    else if(modeColour == 3){
      Serial.println(" Mode: 3 \n Set Colour: Green");
      ledPixels.setPixelColor(0, 0,60,0);//green
    }
    else{
      Serial.println(" Error \n Set Colour: Red");
      ledPixels.setPixelColor(0, 200,0,0);//emergency red
    }
    ledPixels.setBrightness(ledBrightness);
    ledPixels.show();
}

void setup() {
  #if (MY_DEBUG)
    Serial.begin(9600);while (! Serial) {};
  #endif
  #if (USE_SLEEPY)
    int countdownMS = Watchdog.enable(20000);
    //DEBUG_PRINT("Watchdog Enabled=");DEBUG_PRINTLN(countdownMS);
  #endif
  ledPixels.begin();                                                           //Start NeoPixel
  updateLedColor(mode,LED_BRIGHTNESS);
  Keyboard.begin();
  Initialize_Buttons();
}
/*
 * does everything of course
 */
void loop() {
  if(Read_Buttons()) {
    updateLedColor(mode,LED_BRIGHTNESS);  
    switch(Current_Buttons) {
      case PUSHED_RIGHT:  
        Send_Keypress(switchOne[mode]);
        break;
      case PUSHED_LEFT:   
        Send_Keypress(switchThree[mode]);
        break;
      case PUSHED_SELECT: 
        Send_Keypress(switchTwo[mode]);
        break;
      case PUSHED_UP:     
        Send_Keypress(switchFive[mode]);
        break;
      case PUSHED_DOWN:   
        Send_Keypress(switchFour[mode]);
        break;
    };
  };
  #if (USE_SLEEPY)
    Watchdog.reset();
  #endif
}
