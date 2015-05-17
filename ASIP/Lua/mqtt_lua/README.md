The main difference between the two folder is that the mqtt_wifi_allinone try to use only a single file to perform everything, while in the mqtt_wifi_basic/src I tried to maintain a modular approach. The mqtt_wifi_basic also contain a first draft of tcp socket, but it's not needed for mqtt. Anyway, the version in which I performed the last tests was the mqtt_wifi_allinone.

**Intended functionality**
They both try to perform the following steps:
- connect the wifi
- connect to the mqtt broker
- subscribe to a topic 
- the allinone also publish a message every five seconds

**Symptoms**
Common symptoms: The program connects successfully to the wifi, and then connects successfully also to the broker. But, the connection to the mqtt broker fails after about one minute. 
Only in the allInOne: after the connection failed, the program successfully reconnect to the broker. But, after about 3 minutes, it crashes for a PANIC error and the ESP restarts. Notice that the mqtt connection failed more than once.
