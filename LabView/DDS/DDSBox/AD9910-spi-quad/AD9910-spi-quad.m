%% 通讯协议
%输入字符串，字节位
% byte1 update 128
%       read   >128,=128+数据长度
%       write  数据长度，通常是4或8
% byte2 寄存器地址 0~32，常用地址14 （0x0E），是波形参数寄存器
% byte3~ 数据
%      data byte 1 2| 3 4| 5 6 7 8
%      data byte 1~2 幅值参数14位，最大2^14对应幅值幅值5V，峰峰值10V，输入数据对应（byte1*128+byte2）/2^14 *5V
%      data byte 3~4 相位参数16位
%      data byte 5~8 频率参数32位，最大模拟量1GHz，实际模拟输出1GHz*（byte5*256^3+byte6*256^2+byte7*256+byte8)/2^32


% Instrument Connection

% Find a serial port object.
com = instrfind('Type', 'serial', 'Port', 'COM4', 'Tag', '');

% Create the serial port object if it does not exist
% otherwise use the object that was found.
if isempty(com)
    com = serial('COM4');
else
    fclose(com);
    com = com(1);
end

% Connect to instrument object, obj1.
fopen(com); %如果此时串口被其他程序占用，会报错，需要重启单片机
pause(3);

for i=1:1
%AD9910 initialization
%第一位 update 128；write <=9;read >128,数据位数等于第一位-128
fwrite(com,[32*i+4,0,0,128,0,0],'uint8');%第一位空：写；第二位4：写4位；第三位0：寄存器地址0；剩下的是写入的数据
fwrite(com,[32*i+4,1,1,64,8,32],'uint8');%寄存器地址1
fwrite(com,[32*i+4,2,29,63,65,200],'uint8');%寄存器地址2
fwrite(com,[32*i+4,3,0,0,0,127],'uint8');%寄存器地址3

%写入波形，8位数据，地址E
fwrite(com,[32*i+8,14,63,255,0,0,1,0,0,0],'uint8');%数据长度8，寄存器地址E，控制频率，相位，幅值
% fwrite(com,[32*i+8,15,63,255,0,0,2,0,0,0],'uint8');
% fwrite(com,[32*i+8,16,63,255,0,0,3,0,0,0],'uint8');
% fwrite(com,[32*i+8,17,63,255,0,0,4,0,0,0],'uint8');
% fwrite(com,[32*i+8,18,63,255,0,0,5,0,0,0],'uint8');
% fwrite(com,[32*i+8,19,63,255,0,0,6,0,0,0],'uint8');
% fwrite(com,[32*i+8,20,63,255,0,0,7,0,0,0],'uint8');
% fwrite(com,[32*i+8,21,63,255,0,0,64,0,0,0],'uint8');
fwrite(com,[32*i+128],'uint8');%update

% read，数据长度=136-128=8位，14：地址E，读出频率相位幅值数据
fwrite(com,[32*i+136,14],'uint8');
%
%    63-幅值 14位
%    255-

%      0-相位，16位
%      0-

%      1 -
%      1 频率，15.计算方法是，AD9910频率是32位寄存器，2^32
%      对应1GHz,输入数据每一位代表一个字节，即2进制的8位，最大值是2^8，所以数值是1*2^0+1*2^8+1*2^16+1*2^24=freq,实际输出频率=1GHZ*freq/2^32,此处是3.9MHz
%      1
%      1 -

% update
out = fread(com,8,'uint8')
end

fclose(com);
