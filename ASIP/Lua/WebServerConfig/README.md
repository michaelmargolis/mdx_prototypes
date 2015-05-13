This code attempts to connect to a previously connected access point and if successful, runs Tcp2SerialLCD
If it can't connect, it runs configServerInit to start up an access point and then runs ConfigServer to create a web server that enables selection of another access point to connect to.

Tcp2SerialLCD.lua is a TCP to Serial bridge. Serial messages are echoed to a connected TCP client. TCP packets received from the client are echoed to the serial port.

The TCP address and various status messages are displayed on an OLED LCD connected using I2C

telnetConfig.lua is an alternative to the web server interface for selecting access an access point. This code is not yet complete