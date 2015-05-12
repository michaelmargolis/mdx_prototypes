BROKER = "192.168.0.101"
CLIENT_ID = "esp8266"

--topic_sub = "/asip/"..CLIENT_ID.."/in"
--topic_pub = "/asip/"..CLIENT_ID.."/out"
topic_sub = "/#"
topic_pub = "/asip/"
buff = ""
connected = false

m = mqtt.Client(CLIENT_ID, 50)
-- m:connect(BROKER, 1883, 0, function(conn)
--  print("Mqtt Connected to:" .. Broker)
--  mqtt_sub()
--  end)

-- setup Last Will and Testament (optional)
-- Broker will publish a message with qos = 0, retain = 0, data = CLIENT_ID.."offline" 
-- to topic "/lwt" if client don't send keepalive packet
m:lwt("/lwt", CLIENT_ID.." offline", 0, 0)

m:on("connect", function(con) print("Mqtt connected\n") end)
-- m:on("offline", function(con)  print ("Mqtt offline")   end)
-- m:on("message", function(conn, topic, data) print(data) end)

m:on("offline", function(conn)
  print ("reconnecting...")
  print(node.heap())
  print("IP Address: ")
  print(wifi.sta.getip())
  tmr.alarm(1, 1000, 0, function()
    m:connect("BROKER", 1883, 0, function(c) run() end)
  end)
end)

-- on publish message receive event
m:on("message", function(conn, topic, data)
  if data ~= nil then
    print(topic .. ":" ..data)
    --uart.write(0,pl)
  end
end)

--function mqtt_sub()
--	m:subscribe(topic_sub,0, function(conn)
--		print("Mqtt Subscribed to "..topic_sub)
--		end)
--end

function run()
  --tmr.alarm(2,1000,1,function(conn)
  print("connected")
  m:subscribe(topic_sub,0, function(conn)
    -- m:publish(topic_pub,"hello",0,0, function(conn) print("sent") end)
  -- end)
  end)
end

--uart.on("data",'\n', function(data)
--  buff=buff..data
--  pos=0
--  repeat
--    pos=string.find(buff,"\n")
--    if pos then
--      msg = string.sub(buff,1,pos)
--      if global_m~=nil then
--        global_m:publish(topic_pub,msg,0,0, function(c) end)
--      end
--      if( pos < string.len(buff)) then
--        buff = string.sub(buff, pos+1)
--      else
--        buff =""
--      end
--    end
--  until pos == nil -- no more newlines
--end, 0)

tmr.alarm(0, 1000, 1, function()
  if wifi.sta.status() == 5 then
    tmr.stop(0)
    m:connect(BROKER, 1883, 0, function(conn)
      print("connected")
      -- m:subscribe(topic_sub,0, function(c) end)
      run()
    end)
  end
end)

--repeat
--  if wifi.sta.status() == 5 then
--    m:connect(BROKER, 1883, 0, function(conn)
--      print("connected")
--      m:subscribe(topic_sub,0, function(c) end)
--      -- run()
--    end)
--    connected = true
--  end
--until connected == false
