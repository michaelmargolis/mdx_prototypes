-- SSID = "CSD1000"
-- PWD = "Concorde"
-- wifi_attempts = 10

local function main() 

  dofile("wifi_utils.lua")
  --tmr.delay(15000000)
  -- if connect(SSID,PWD,wifi_attempts) then
    --dofile("mqtt_utils.lua")
    -- print("Debug")
    -- tmr.alarm(0, 20000, 1, function() dofile("mqtt_utils") end) -- repeat with stop: allow avoidance of flash in case of issue
    -- print("Debug 2")
    -- while true do
      
    -- end
  -- else
    -- return false
  -- end
end

-- setting correct baud rate for the asip
-- uart.setup(0,57600,8,0,1)
main()


