SOCKET_PORT = 1234

buffer = ""

function run()
  sv = net.createServer(net.TCP)
  sv:listen(SOCKET_PORT,function(c)
    c:on("receive", function(c, pl)
      print(pl)
      -- uart.write(0,pl)
      if pl == "close" then -- not working, why?
        c:close()
      end
    end)
    function s_output(str)
      if(c~=nil) then c:send(str) end
    end
    -- uart.on("data", s_output, 0)
    c:send("hello world")
    --c:on("sent",function(c) c:close() end) -- it closes the connection just after the send
  end)
end

run()

