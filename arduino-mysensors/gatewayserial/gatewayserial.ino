/** A mysensors gateway with a LCD Text Display
 *
 * LCD Driver: https://github.com/mathertel/LiquidCrystal_PCF8574
 *
 * You must setup the ROWS and COLS definitions
 *
 *
*/

#include <Wire.h>
#include <LiquidCrystal_PCF8574.h>

/** Setup Mysensors **********************/

//#define MY_DEBUG

// 2524 Mhz (RF24 channel 125)
#define MY_RF24_CHANNEL 124
#define MY_RADIO_RF24
//#define MY_RF24_PA_LEVEL RF24_PA_LOW
#define MY_GATEWAY_SERIAL
#include <MySensors.h>


//#define MY_NODE_ID 1
#define   CHILD_DISPLAY 1

// 0x3f is de I2C display address, you can use a I2C scanner to find out.
LiquidCrystal_PCF8574 lcd(0x3f);
// Is mandatory set ROWS and COLS in the LCD initialization
#define LCD_COLS 20
#define LCD_ROWS 4

void setup()
{
  int error;

  Wire.begin();
  Wire.beginTransmission(0x3f);
  error = Wire.endTransmission(); // error==0 OK!

  // Begin is neccesary to correct print rows and cols
  lcd.begin(LCD_COLS,LCD_ROWS); // initialize the lcd

  lcd.setBacklight(255);

  write2LCD("AAWaiting controller ");
  lcd.cursor();
  lcd.blink();
}

/* Function to convert the V_TEXT received to LCD */

void write2LCD(char *s)
{
  uint8_t param;

  if(strlen(s) < 2) // Not valid command
    return;

  if(s[0] >= 'A' && s[1] >= 'A')
  {
    // Print text at some position
    lcd.setCursor(s[0] - 'A' , s[1] - 'A');
    lcd.print((s+2));
  }
  else switch(s[0]) // Process other commands
  {
    case '0':
      s[1] == '0' ? lcd.noDisplay() : lcd.display();
      break;
    case '1':
      param = s[1] - '0';
      lcd.setBacklight(param);
      break;
    case '2':
      s[1] == '0' ? lcd.noCursor() : lcd.cursor();
      break;
    case '3':
      lcd.clear();
      break;
    case '4':
      s[1] == '0' ? lcd.noBlink() : lcd.blink();
      break;
  }

}

void presentation()
{
  sendSketchInfo("Controller Display LCD","1.0");
  present(CHILD_DISPLAY, S_INFO);
}

void receive(const MyMessage &message)
{

  if(message.sensor == CHILD_DISPLAY && message.type == V_TEXT)
  {
    // The message is for display and it type is V_TEXT (47)
    write2LCD(message.getString());
  }

}

void loop()
{


}
