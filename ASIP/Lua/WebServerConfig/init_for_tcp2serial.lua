CMDFILE = "Tcp2SerialLcd.lua"   -- File to be executed after connection
timeout = 20 -- seconds to wait for connect before going to AP mode
               
statuses = {[0]="Idle",
            [1]="Connecting",
            [2]="Wrong password",
            [3]="AP not found",
            [4]="Connect fail",
            [5]="Got IP",
            [255]="Not in STATION mode"}
            
checkCount = 0
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
  -- pause a few seconds to allow garbage to collect and free up heap
  tmr.delay(5000)
end

-- LCD code
t = { " ", " "," "," "," "," " } -- 6 blank lines of text
-- setup I2c and connect display
function init_i2c_display()
     -- SDA and SCL can be assigned freely to available GPIOs
     --sda = 5 -- GPIO14
     --scl = 6 -- GPIO12
     sda = 3 -- GPIO0
     scl = 4 -- GPIO2
     sla = 0x3c
     i2c.setup(0, sda, scl, i2c.SLOW)
     disp = u8g.ssd1306_128x64_i2c(sla)
end

-- lcd configure
function lcdPrepare()
     disp:setFont(u8g.font_6x10)
     disp:setFontRefHeightExtendedText()
     disp:setDefaultForegroundColor()
     disp:setFontPosTop()
end

function refreshScreen()
     disp:firstPage()
     repeat
         for k,v in pairs(t) do
             disp:drawStr(0,(k-1)*11, v)       
         end
     until disp:nextPage() == false
end     

function printText(text, line)  -- line 1 is first line
     t[line] = text
     refreshScreen()      
end

init_i2c_display()
lcdPrepare()

-- make sure we are trying to connect as clients
wifi.setmode(wifi.STATION)
wifi.sta.autoconnect(1)
-- every second, check our status
tmr.alarm(0, 1000, 1, checkStatus)