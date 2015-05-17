--BROKER    = "192.168.0.102"
PORT      = 1883
CLIENT_ID = "esp8266"

function launch()
  print("WiFI connected. Trying to launch MQTT.")
  print("IP Address: " .. wifi.sta.getip())
  print("Broker: " .. BROKER)

  m = mqtt.Client(CLIENT_ID, 120, "user", "password")
  count = 0 
  secs = 0 
  connection_att = 1
  
  m:on("connect", function(con) end)

  m:on("offline", function(con)
    print ("MQTT: Offline: trying to connect again.")
    -- m:close()
    --client:connect(BROKER, 1883, 0, function(conn)
    print(node.heap())
    --client:subscribe("/topic",0, function(conn) print("MQTT: subscribe success") end)
    tmr.alarm(2, 10000, 0, function()
      m:connect(BROKER, PORT, 0, function() 
        connection_att = connection_att + 1
        print("MQTT: successfully reconnected, attempt n. "..connection_att) 
        pubsub()
      end)
    end)
  end)

  m:on("message", function(conn, topic, data)
    print(topic .. ":" )
    if data ~= nil then
      print(data)
    end
  end)

  m:connect(BROKER, 1883, 0, function(conn)
    print("MQTT: Connected at first attempt.")
    pubsub()
  end)
end

function pubsub()
    m:subscribe("/#",0, function(conn) print("MQTT: subscribe success") end)
    --m:publish("/topic","hello",0,0, function(conn) print("sent") end)
    tmr.alarm (1, 1000, 1, function (conn)
      count = count + 1
      secs = count  -- modify this expression to convert count to secs based on interval             
      msg = "Alive for "..secs.." seconds"
      print("memory="..node.heap())
      --m:publish("/topic",msg ,0,0, function(conn) print("Message sent") end)  
      m:publish("/topic",msg ,0,0, nil)         
    end)
end

if(BROKER == nil or BROKER == "") then
    print("set BROKER IP address")
else    
    launch()
end
