#include <Arduino.h>

const int SPI_SCLK =13;
const int SPI_SDIO = 11;

const int OSK = 19;
const int PR2 = 32;

const int SPI_CSB[4] = {17,9,8,26};
const int MASTER_RESET[4] = {16,23,7,31};
const int PR0[4] = {18,29,6,4};
const int PR1[4] = {0,30,20,3};
const int IO_UPDATE[4] = {1,2,21,24};

/*const int SPI_CSB = 17;
const int MASTER_RESET = 16;
const int PR0 = 18;
const int PR1 = 0;
const int IO_UPDATE = 1;*/

/*const int SPI_CSB = 9;
const int MASTER_RESET = 23;
const int PR0 = 29;
const int PR1 = 30;
const int IO_UPDATE = 2;*/

/*const int SPI_CSB = 8;
const int MASTER_RESET = 7;
const int PR0 = 6;
const int PR1 = 20;
const int IO_UPDATE = 21;*/

/*const int SPI_CSB = 26;
const int MASTER_RESET = 31;
const int PR0 = 4;
const int PR1 = 3;
const int IO_UPDATE = 24;*/

void write1_writen(int slave, int instruction, int n, byte* data) {//instruction:address ,data: what you want to write
      digitalWrite(SPI_SCLK, LOW); // ensure clock pin LOW when we start
      digitalWrite(SPI_CSB[slave], LOW);
      
      shiftOut(SPI_SDIO, SPI_SCLK, MSBFIRST, instruction);
      for (int i = 0; i < n; ++i) shiftOut(SPI_SDIO, SPI_SCLK, MSBFIRST, data[i]);
      
      digitalWrite(SPI_CSB[slave], HIGH);
};

void write1_readn(int slave, int instruction, int n, byte *data) {
      digitalWrite(SPI_SCLK, LOW); // ensure clock pin LOW when we start
      digitalWrite(SPI_CSB[slave], LOW);
      //shiftOut(SPI_SDIO, SPI_SCLK, MSBFIRST, (instruction >> 8)); // high byte
      shiftOut(SPI_SDIO, SPI_SCLK, MSBFIRST, instruction); // low byte
      
      pinMode(SPI_SDIO, INPUT);
      for (int i = 0; i < n; ++i) data[i] = shiftIn(SPI_SDIO, SPI_SCLK, MSBFIRST);
      
      digitalWrite(SPI_CSB[slave], HIGH);
      pinMode(SPI_SDIO, OUTPUT);  
};
static void update(int slave) {
    digitalWrite(IO_UPDATE[slave], HIGH);
    delay(1);
    digitalWrite(IO_UPDATE[slave], LOW);
}

void setup() {
    Serial.begin(9600);

    pinMode(OSK,OUTPUT);
    //pinMode(PR2,OUTPUT);
    //digitalWrite(PR2,LOW);
    pinMode(PR2,INPUT);
    pinMode(SPI_SCLK, OUTPUT);
    pinMode(SPI_SDIO, OUTPUT);

    digitalWrite(OSK,HIGH);
    digitalWrite(SPI_SCLK, LOW);
      
    for (int i = 0; i < 4; ++i) {
      pinMode(MASTER_RESET[i],OUTPUT);
      pinMode(SPI_CSB[i],OUTPUT);
      pinMode(IO_UPDATE[i],OUTPUT);
      //pinMode(PR0[i],OUTPUT);
      //pinMode(PR1[i],OUTPUT);
      //digitalWrite(PR0[i],LOW);
      //digitalWrite(PR1[i],LOW);
      pinMode(PR0[i],INPUT);
      pinMode(PR1[i],INPUT);

      digitalWrite(MASTER_RESET[i],HIGH);
      delay(1);
      digitalWrite(MASTER_RESET[i],LOW);// this master reset from high to low, reset to default setting of the device
      delay(1);
  
      digitalWrite(SPI_CSB[i],HIGH); // deactivate
      digitalWrite(IO_UPDATE[i],LOW);
    } 
}

byte state = 0, slave = 0, len = 0, pos = 0, data[9];
void loop() {  
  while (Serial.available()) {
    byte b = Serial.read();
    //Serial.write(b);
    
    if (state == 0) {
      slave = (b & 0x60) >> 5;
      len = b & 0x1F;
      if (b & 0x80)  {//判断2进制第一位是否为1，即>=128 or1000 0000or 0x80    read or update      
        //如果update b=0x80,len=0,如果 read b>80,通常是84 或 88，所以 len=4或者8
        if (len == 0)//判断b如果等于128
          update(slave);
        else //如果b大于128， read
          state = 1;
      } else  { // 如果b<128 write,此处是数据位数
        state = 2;
        ++len;
        pos = 0;
      }
    } else if (state == 1) {
      write1_readn(slave, b | 0x80, len, data);//此时b为传过来的第二位，即地址，b|80表示地址位字节的第一位设为1，后面的bit照抄地址位,详见说明书P48，表示读操作和地址位
      for (int i = 0; i < len; ++i)//读取信息
        Serial.write(data[i]);
      state = 0;
    } else if (state == 2) {
       data[pos] = b;
       if (++pos == len) {
          write1_writen(slave,data[0],len-1,data+1);//???
          state = 0;
       }
    }
  }
}
