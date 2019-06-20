 # MySensors Text Protocol

MySensors `S_INFO` sensor was not  designed to use in multi-line text displays. 

With a workaround over `V_TEXT ` messages it is possible select a row and column before print the text. Also, this method is a way to send extra commands over MySensors `V_TEXT` to the display.

The solution used adds a 2-byte header to the message `V_TEXT` sent with MySensors. When the sensor receives a `V_TEXT` the first 2 bytes must be processed as follow:

* When  byte 1  <  ASCII('A'),  the display executes one of the following commands:

| ASCII byte 1 value | ASCII  byte 2 value |                |
| ------ | --------- | -------------- |
| '0'  | '0' / '1' | Display OFF/ON |
| '1'  | N         | Set BackLight (N is an integer number 0-9) |
| '2'  | '0' / '1' | Cursor ON/OFF  |
| '3'  |       - ' | Clear Screen   |
| '4'  | '0' / '1' | Blink cursor OFF/ON  |

* When byte 1 >= ASCII('A')  the text is printed at some Col and Row. Row and Col are calculated from the first 2 bytes received being the first byte is the Row and the second the Col. The offset is the ASCII character 'A' therefore the string 'AA' correspond with  (0,0) position.

## Arduino code

The following piece of code is also in the example [gatewayserial.ino](../arduino-mysensors/gatewayserial/gatewayserial.ino) and it an example of processing `V_TEXT` messages:

```cpp
/* Function to convert the V_TEXT received to LCD command/text */
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


// MySensors message callback
void receive(const MyMessage &message)
{
  // The message is for display and it type is V_TEXT (47)
  if(message.sensor == CHILD_DISPLAY && message.type == V_TEXT)    
    write2LCD(message.getString());
}
```

To test a display in a MySensors network  you can use the python example at [tests/mysensors-display.py](../tests/mysensors-display.py)

Be careful with `V_TEXT`  message due the protocol limits size to 25 bytes, there are only 23 bytes left for text.
