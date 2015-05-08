WebServerConfig contains a serial to tcp bridge for point-to-point ASIP over a tcp socket.
This code will try and connect to the previously connected access point. The IP address and connection status is displayed on an LCD.
If the esp8266 cannot connect to the ap, it switches from station mode to AP mode, reports its SSID on the LCD and provides a web page that displays all access points in range.
The user can select one of these and enter a password to connect. If connection is successful, this is stored in the esp as the current access point.

The fragment named telnetConfig.lua is work in progress for a config utility using telnet instead of a web browser

The code is not tested, documented or complete and should not be reproduced.