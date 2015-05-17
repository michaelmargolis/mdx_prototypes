-- tcp server for ASIP with LCD

timeout = 30 -- 30 secs 
sv=net.createServer(net.TCP,timeout)
ip = "IP "..wifi.sta.getip()
printText(ip, 1)
print(wifi.sta.getip())
global_c = nil
printText("Ready",5)

-- tcp code
sv:listen(5507, function(c)
	if global_c~=nil then
		global_c:close()
	end
	global_c=c
    printText("Connected", 5)
	c:on("receive",function(sck,pl)	uart.write(0,pl) end)
	c:on("disconnection",function(c) printText("Disconnected", 5) end)
end)

buff = ""
uart.on("data",'\n', function(data)
    buff=buff..data
    pos=0
    repeat
        pos=string.find(buff,"\n")
        if pos then
            msg = string.sub(buff,1,pos)  
            if global_c~=nil then
                global_c:send(msg)
            end                 
            if( pos < string.len(buff)) then
                buff = string.sub(buff, pos+1)
            else
                buff =""
            end
        end  
     until pos == nil -- no more newlines     
end, 0)