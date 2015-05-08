dofile("configServerInit.lua")
apRefresh = 15 -- how many seconds between when we scan for updated AP info for the user
currentAPs = {}
apArray = {}

newssid = ""
newpw = ""

function listAPs_callback(t)
  if(t==nil) then
    return
  end
  currentAPs = t
end

function listAPs()
  wifi.sta.getap(listAPs_callback)  
end

function sendAPs(conn)
  print("send APs");
  apArray = {}
  for k,v in pairs(currentAPs) do
     table.insert(apArray,k) -- add to indexed table
     print(k)
  end
  conn:send('Access Points:\r\n\n')
  if(lastStatus ~= nil) then
    conn:send('Previous connection status: ' .. lastStatus ..'\r\n')
  end
  
  if(newssid ~= "") then
    conn:send('Upon reboot, unit will attempt to connect to SSID "' .. newssid ..'".\r\n')
  end
    
  --for ap,v in pairs(currentAPs) do  conn:send('  ' .. ap .. '\r\n')  end  
  for i,ssid in ipairs(apArray) do print(i, v)  conn:send(i,ssid..'\r\n') end
  conn:send('\nEnter desired SSID and press return\r\n')  
end

function incoming(conn, payload)
  print('incoming:' .. payload)  
  if (payload ~= nil) then    
     if(newssid == "") then
        if( currentAPs[payload]) then 
            newssid = payload
            print("New SSID: " .. newssid)
   --         conn.send('Enter password')
   --      else  
   --         conn.send('Invalid ssid')
        else
            print('payload did not match ssid')
        end 
     elseif(newpw == "") then
        newpw = payload
        print('configuring ' .. newssid .. ' with Password ' .. newpw)      
        wifi.sta.config(newssid, newpw)
  --      conn.send('to connect, type: reboot')
     else
        if payload == 'reboot' then
            conn:close()
            node.restart()
        else
            print(payload .. "reconfiguring")       
            newssid=""
            newpw=""    
            sendAPs(conn)
        end        
     end          
  end
end

function incomingTest(conn, pl)
  print(pl)
  conn:send("in recv")
end

-- start a periodic scan for other nearby APs
tmr.alarm(0, apRefresh*1000, 1, listAPs)
listAPs() -- and do it once to start with
-- Start telnet Server
sv=net.createServer(net.TCP, 180)
sv:listen(23, function(c) 
   sendAPs(c)
   c:on("receive", incoming)
   --c:on("receive", function(conn, pl)  print(pl) conn:send("in recv") end)
   --c:on("receive", incomingTest)
end)