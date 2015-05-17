print(node.heap())
dofile("configServerInit.lua")
print(node.heap())
apRefresh = 15 -- how many seconds between when we scan for updated AP info for the user
currentAPs = {}

newssid = ""

function listAPs_callback(t)
  if(t==nil) then
    return
  end
  currentAPs = t
end

function listAPs()
  wifi.sta.getap(listAPs_callback)
end

function sendPage(conn)
  print("send page");
  conn:send('HTTP/1.1 200 OK\n\n')
  conn:send('<!DOCTYPE HTML>\n<html>\n<head><meta content="text/html; charset=utf-8">\n<title>Device Configuration</title></head>\n<body>\n<form action="/" method="POST">\n')

  if(lastStatus ~= nil) then
    conn:send('<br/>Previous connection status: ' .. lastStatus ..'\n')
  end
  
  if(newssid ~= "") then
    conn:send('<br/>After reboot, unit will attempt to connect to SSID "' .. newssid ..'".\n')
  end
    
  conn:send('<br/><br/>\n\n<table>\n<tr><th>Select Access Point:</th></tr>\n')

  for ap,v in pairs(currentAPs) do
    conn:send('<tr><td><input type="button" style="min-width: 120px;" onClick=\'document.getElementById("ssid").value = "' .. ap .. '"\' value="' .. ap .. '"/></td></tr>\n')
  end
  
  conn:send('</table>\n\nSSID: <input type="text" id="ssid" name="ssid" value=""><br/>\nPassword: <input type="text" name="passwd" value=""><br/>\n\n')
  conn:send('<br/>Press Submit to update and reboot<br/><br/>')
  conn:send('<input type="submit" value="Submit"/>\n<input type="button" onClick="window.location.reload()" value="Refresh"/>\n<br/>')
  conn:send('</form>\n</body></html>')
  
end

function url_decode(str)
  local s = string.gsub (str, "+", " ")
  s = string.gsub (s, "%%(%x%x)",
      function(h) return string.char(tonumber(h,16)) end)
  s = string.gsub (s, "\r\n", "\n")
  return s
end

function incoming_connection(conn, payload)
  if (string.find(payload, "GET /favicon.ico HTTP/1.1") ~= nil) then
    print("GET favicon request")
  elseif (string.find(payload, "GET / HTTP/1.1") ~= nil) then
    print("GET received")
    sendPage(conn)
  else
    print("POST received")
    local blank, plStart = string.find(payload, "\r\n\r\n");
    if(plStart == nil) then
      return
    end
    payload = string.sub(payload, plStart+1)
    print(payload)
    args={}
    args.passwd=""
    -- parse all POST args into the 'args' table
    for k,v in string.gmatch(payload, "([^=&]*)=([^&]*)") do
      args[k]=url_decode(v)
      print(args[k])
    end
    if(args.ssid ~= nil and args.ssid ~= "") then
      print("New SSID: " .. args.ssid)
      print("Password: " .. args.passwd)
      newssid = args.ssid
      wifi.sta.config(args.ssid, args.passwd)
      print("Rebooting to connect to ".. args.ssid)
      conn:close()
      node.restart()
    end   
    conn:send('HTTP/1.1 303 See Other\n')
    conn:send('Location: /\n')
  end
end

-- start a periodic scan for other nearby APs
tmr.alarm(0, apRefresh*1000, 1, listAPs)
listAPs() -- and do it once to start with
  
-- Now we set up the Web Server
srv=net.createServer(net.TCP)
srv:listen(80,function(sock)
  sock:on("receive", incoming_connection)
  sock:on("sent", function(sock) 
    sock:close()
  end)
end)