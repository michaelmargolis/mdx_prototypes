--curr = 0
--wifi_ok = false
--
--function isWiFiConnected(trynum) 
--  ip = wifi.sta.getip()
--  if (curr<trynum) then
--    if wifi.sta.status() == 5 and ip~=nil  then 
--      print("Connected! Ip is "..ip)
--      wifi_ok = true
--    else 
--      curr = curr + 1
--      print(curr)
--      tmr.alarm(0,2500000,0,isWiFiConnected(trynum))
--    end
--  else
--    -- wifi_ok = false
--    print("Impossible to connect. Max number of attempt reached.")
--  end 
--end
--
----function connectWiFi() 
----  wifi.setmode(wifi.STATION); 
----  wifi.sta.config(SSID,PASSWORD);  
----  wifi.sta.connect(); 
----  connection_check() 
----end
--
--function configWiFi(ssid,pwd)  
--  wifi.setmode(wifi.STATION) 
--  wifi.sta.config(ssid,pwd) 
--  -- wifi.sta.connect() 
--end
--
--function connect(ssid,pwd,trynum)
--  ip = wifi.sta.getip()
--  if ((ip == nil) or  (ip == "0.0.0.0")) then
--    configWiFi(ssid,pwd)
--    print("Connection data "..ssid.." "..pwd)
--    tmr.alarm(0,2500000,0,isWiFiConnected(trynum))
----  while (wifi_conn == false and curr < trynum) do
----    print("Iteration: "..curr)
----    configWiFi(ssid,pwd)
----    wifi_conn = isWiFiConnected()
----    curr = curr + 1
----  end
--    return wifi_ok
--  else 
--    return true
--  end
--end
--
----SSID = "CSD1000"
----PWD = "Concorde"
----wifi_attempts = 10
----connect("CSD1000","Concorde",wifi_attempts)

SSID    = "CSD1000"
APPWD   = "Concorde"
CMDFILE = "mqtt_utils.lua"   -- File that is executed after connection
-- CMDFILE = "tcpip_socket.lua" -- file with simple tcp/ip socket

-- Some control variables
wifiTrys     = 0      -- Counter of trys to connect to wifi
NUMWIFITRYS  = 200    -- Maximum number of WIFI Testings while waiting for connection

-- Change the code of this function that it calls your code.
function launch()
  print("Connected to WIFI!")
  print("IP Address: " .. wifi.sta.getip())
  tmr.alarm(0, 1000, 0, function() dofile(CMDFILE) end )  -- Zero as third parameter. Call once the file.
end  -- !!! Increase the delay to like 10s if developing mqtt.lua file otherwise firmware reboot loops can happen

function checkWIFI() 
  if ( wifiTrys > NUMWIFITRYS ) then
    print("Sorry. Not able to connect")
  else
    ipAddr = wifi.sta.getip()
    if ( ( ipAddr ~= nil ) and  ( ipAddr ~= "0.0.0.0" ) )then
      -- lauch()        -- Cannot call directly the function from here the timer... NodeMcu crashes...
      tmr.alarm( 1 , 500 , 0 , launch )
    else
      -- Reset alarm again
      tmr.alarm( 0 , 2500 , 0 , checkWIFI)
      --print("Checking WIFI..." .. wifiTrys)
      wifiTrys = wifiTrys + 1
    end 
  end 
end

print("-- Starting up! ")
-- uart.setup(0,57600,8,0,1)
-- Lets see if we are already connected by getting the IP
ipAddr = wifi.sta.getip()
if ( ( ipAddr == nil ) or  ( ipAddr == "0.0.0.0" ) ) then
  -- We aren't connected, so let's connect
  print("Configuring WIFI....")
  wifi.setmode( wifi.STATION )
  wifi.sta.config( SSID , APPWD)
  print("Waiting for connection")
  tmr.alarm( 0 , 2500 , 0 , checkWIFI )  -- Call checkWIFI 2.5S in the future.
else
 -- We are connected, so just run the launch code.
 launch()
end