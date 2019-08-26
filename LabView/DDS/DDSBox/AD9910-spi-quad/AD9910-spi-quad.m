%% ͨѶЭ��
%�����ַ������ֽ�λ
% byte1 update 128
%       read   >128,=128+���ݳ���
%       write  ���ݳ��ȣ�ͨ����4��8
% byte2 �Ĵ�����ַ 0~32�����õ�ַ14 ��0x0E�����ǲ��β����Ĵ���
% byte3~ ����
%      data byte 1 2| 3 4| 5 6 7 8
%      data byte 1~2 ��ֵ����14λ�����2^14��Ӧ��ֵ��ֵ5V�����ֵ10V���������ݶ�Ӧ��byte1*128+byte2��/2^14 *5V
%      data byte 3~4 ��λ����16λ
%      data byte 5~8 Ƶ�ʲ���32λ�����ģ����1GHz��ʵ��ģ�����1GHz*��byte5*256^3+byte6*256^2+byte7*256+byte8)/2^32


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
fopen(com); %�����ʱ���ڱ���������ռ�ã��ᱨ����Ҫ������Ƭ��
pause(3);

for i=1:1
%AD9910 initialization
%��һλ update 128��write <=9;read >128,����λ�����ڵ�һλ-128
fwrite(com,[32*i+4,0,0,128,0,0],'uint8');%��һλ�գ�д���ڶ�λ4��д4λ������λ0���Ĵ�����ַ0��ʣ�µ���д�������
fwrite(com,[32*i+4,1,1,64,8,32],'uint8');%�Ĵ�����ַ1
fwrite(com,[32*i+4,2,29,63,65,200],'uint8');%�Ĵ�����ַ2
fwrite(com,[32*i+4,3,0,0,0,127],'uint8');%�Ĵ�����ַ3

%д�벨�Σ�8λ���ݣ���ַE
fwrite(com,[32*i+8,14,63,255,0,0,1,0,0,0],'uint8');%���ݳ���8���Ĵ�����ַE������Ƶ�ʣ���λ����ֵ
% fwrite(com,[32*i+8,15,63,255,0,0,2,0,0,0],'uint8');
% fwrite(com,[32*i+8,16,63,255,0,0,3,0,0,0],'uint8');
% fwrite(com,[32*i+8,17,63,255,0,0,4,0,0,0],'uint8');
% fwrite(com,[32*i+8,18,63,255,0,0,5,0,0,0],'uint8');
% fwrite(com,[32*i+8,19,63,255,0,0,6,0,0,0],'uint8');
% fwrite(com,[32*i+8,20,63,255,0,0,7,0,0,0],'uint8');
% fwrite(com,[32*i+8,21,63,255,0,0,64,0,0,0],'uint8');
fwrite(com,[32*i+128],'uint8');%update

% read�����ݳ���=136-128=8λ��14����ַE������Ƶ����λ��ֵ����
fwrite(com,[32*i+136,14],'uint8');
%
%    63-��ֵ 14λ
%    255-

%      0-��λ��16λ
%      0-

%      1 -
%      1 Ƶ�ʣ�15.���㷽���ǣ�AD9910Ƶ����32λ�Ĵ�����2^32
%      ��Ӧ1GHz,��������ÿһλ����һ���ֽڣ���2���Ƶ�8λ�����ֵ��2^8��������ֵ��1*2^0+1*2^8+1*2^16+1*2^24=freq,ʵ�����Ƶ��=1GHZ*freq/2^32,�˴���3.9MHz
%      1
%      1 -

% update
out = fread(com,8,'uint8')
end

fclose(com);
