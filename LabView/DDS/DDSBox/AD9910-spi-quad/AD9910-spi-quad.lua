local pprint = require'pprint'
pprint.defaults.show_all=true
pprint.defaults.use_tostring=true

local ffi = require "ffi"
ffi.cdef "int Sleep(int);"
os.del_us = ffi.C.Sleep
require'ul_serial'

local dds = {}

function bytes2str(bytes)
    local s = {}
    for i = 1,#bytes do
        s[i] = string.char(bytes[i])
    end
    return table.concat(s)
end

function str2bytes(str)
    local b = {}
    for i = 1,#str do
        b[i] = str:byte(i)
    end
    return b
end

function spi9910(port,offset,command,register,data)
    if command:sub(1,1) == 'w' then
        local bytes = {offset+#data,register}
        for _,v in ipairs(data) do
            bytes[#bytes+1] = v
        end
        port:write(bytes2str(bytes))
    elseif command:sub(1,1) == 'u' then
        port:write(bytes2str{128+offset})
    elseif command:sub(1,1) == 'r' then
        port:write(bytes2str{128+offset+data,register})
        port:waitRX(data,100)
        return str2bytes(port:read())
    end
end

function dds.reset(port,channel)
    spi9910(port,32*channel,'w',0,{0,128,0,0})
    spi9910(port,32*channel,'w',1,{1,64,8,32})
    spi9910(port,32*channel,'w',2,{29,63,65,200})
    spi9910(port,32*channel,'w',3,{0,0,0,127})
    spi9910(port,32*channel,'u')
end

function int2arr(val,length)
    val = math.floor(val+0.5)
    local arr = {}
    for i=0,length-1 do
        local mask=bit.lshift(0xFF,8*i)
        arr[i+1] = bit.rshift(bit.band(val,mask),8*i)
    end
    return arr
end

function arr2int(arr)
    val = 0
    for i=1,#arr do
        val = bit.bor(val,bit.lshift(arr[i],8*(i-1)))
    end
    return val
end

function join_array(...)
    local arg = {...}
    local t={}
    for i=1,#arg do
        local array = arg[i]
        if type(array) == 'table' then
            for j = 1, #array do
                t[#t+1] = array[j]
            end
        else
            t[#t+1] = array
        end
    end
    return t
end
  
function dds.parameter(port,channel,profile,frequency,amplitude,phase)
    local reg = 0xE + profile
    local fb = 4294967.296
    local ab = 16383
    local pb = 65535
    if frequency then
        local data = join_array(int2arr(ab*amplitude,2),int2arr(0.5*pb*phase,2),int2arr(fb*frequency,4))
        spi9910(port,32*channel,'w',reg,data)
        spi9910(port,32*channel,'u')
    else
        local data = spi9910(port,32*channel,'r',reg,8)
        return {arr2int({data[5],data[6],data[7],data[8]})/fb,arr2int({data[1],data[2]})/ab,2*arr2int({data[3],data[4]})/pb}
    end
end

port=io.Serial:open{'com4'}
for i=0,3 do
    dds.reset(port,i)
end
dds.parameter(port,1,0,200,1,0)
os.del_us(200)
pprint(dds.parameter(port,1,0))
port:close()