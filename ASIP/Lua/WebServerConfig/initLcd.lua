-- init oled lcd

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
printText("LCD ready",1)