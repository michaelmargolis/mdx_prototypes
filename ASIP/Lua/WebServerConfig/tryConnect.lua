--CMDFILE = "Tcp2SerialLcd.lua"   -- File to be executed after connection
timeout = 4 -- seconds to wait for connect before going to AP mode
               
statuses = {[0]="Idle",
            [1]="Connecting",
            [2]="Wrong password",
            [3]="AP not found",
            [4]="Connect fail",
            [5]="Got IP",
            [255]="Not in STATION mode"}
            
checkCount = 0

function printText(text, line)  -- default if LCD not connected
  print("!"..text)      
end
 
function checkStatus()
  checkCount = checkCount + 1
  local s=wifi.sta.status()
  print("Status = " .. s .. " (" .. statuses[s] .. ")")
  printText("Status = " .. statuses[s], 3)
  --printText(statuses[s], 3)
  if(s==5) then -- successful connect
    launchApp()
    return
  elseif(s==2 or s==3 or s==4) then -- failed
    startServer(statuses[s])
    return
  end
  if(checkCount >= timeout) then
    startServer("timeout")
    return
  end
end

function launchApp()
  cleanup()
  printText("Starting..", 5)  
  dofile(CMDFILE)
end

function startServer(status)  
  printText(status,3)
  cleanup()
  printText("switching to AP mode", 5) 
  --print("network not found, switching to AP mode")
  dofile('configServer.lua')
end

function cleanup()
  -- stop our alarm
  tmr.stop(0)
  -- nil out all global vars we used
  timeout = nil
  statuses = nil
  checkCount = nil
  -- nil out any functions we defined
  checkStatus = nil
  launchApp = nil
  startServer = nil
  cleanup = nil
  -- take out the trash
  collectgarbage()
  -- pause a few ms to allow garbage to collect and free up heap
  tmr.delay(2000)
end

if(CMDFILE == nil or CMDFILE == "") then
    print("set CMDFILE to the executable Lua file")
else    
    uart.setup(0,57600,8,0,1,0)
    -- make sure we are trying to connect as clients
    wifi.setmode(wifi.STATION)
    wifi.sta.autoconnect(1)
    -- every second, check our status
    tmr.alarm(0, 1000, 1, checkStatus)
end    