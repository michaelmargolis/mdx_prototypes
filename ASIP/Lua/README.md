init.lua : the default auto-run file if uploaded to the ESP8266
 - sets the CMDFILE variable to the name of the file to run after connection (either Tcp2Serial.lua for the TCP bridge or allnOne.lua for MQTT. 
- Initializes  the lcd,
- runs tryConnect.lua
For testing purposes I prefer to set CMDFILE and run tryConnect manually so I don’t upload init.lua while code is under development

tryConnect: connect to configured access point and runs a file given in CMDFILE variable 
- checks if a global variable named CMDFILE has been set. If so then:
- sets the baud to 57600 
- tries to connect to the previously connected access point and if it can connect within four seconds then  it runs the lua  file set by the variable  CMDFILE
- if connection is not successful after 4 seconds then configServer.lua is run

configServer: - web server to select an access point for subsequent connection
- runs configServerInit.lua to switch to access point mode with a hard coded IP address and name. the name will be ASIP-XX-YY", where XX and YY are the last two bytes of this unit's MAC address 
- creates a web server that displays a form with buttons containing the SSID of all detected access points and two text input fields, one for the selected SSID, the other for the password.  When one of these buttons is pressed, the SSID is entered into a text field. The user should enter the password in the password field. 
There are two additional buttons labelled “Submit” and “Refresh”. Refresh will update the list of detected access points. Submit will send the SSID and PW to the ESP8266, which will configure itself to use the submitted values when it next tries to connect. After this, the ESP8266 is rebooted, which in normal use will run init.lua and connect to the access point and then run the program set in the CMDFILE (as described above)

Tcp2Serial.lua: - This is the TCP to serial bridge.
 Serial data is echoed to a hard coded socket (currently 5507), received packets on this socket are echoed to the serial port.

PubSubTest.lua: MQTT publish and subscribe test code
This is a subset of the allInOne.lua test code. Wifi connection code has been removed as this is handled in the code described above.  The broker IP address must be set in the variable named BROKER before running. (we can discuss how best to set this when deployed) 

