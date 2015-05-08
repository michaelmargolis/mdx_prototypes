This prototype is a gateway between the pubnub data provider and MQTT.
run t.bat to connect to the live data feed at Hastings pier
the output data consists of three comma separated fields:
time (epoch), tide height in cm, wave height in cm
the time value is only updated once per second, a time of -1 means use the previously sent time
