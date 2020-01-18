/******************** COPYRIGHT 2016 OnEasyBelectronics ********************
* File Name          : readme.pdf
* Version            : V1.5
* Date               : 15-Aug-2016
* Description        : read me file for USB2UIS board
********************************************************************************
Release-2016-08-15.zip

This release consists of the following:
***************
      ********************************************************************************
       - This readme file: ([EXTRACT PATH]\readme.pdf)
      ******************************************************************************** 
       + DOC :([EXTRACT PATH]\DOC\)

         - Usb2UIS转接板用户手册.pdf       : USER Manual (Chinese)
         - USB2UIS user manual.pdf         : USER Manual (English)
         - Lib user manual.pdf             : Lib function USER Manual (English)        
      ********************************************************************************
       + APP :([EXTRACT PATH]\APP\)
       
         - Usb2ish_pro.exe                 : USB2UIS application program (Chinese)
         - Usb2ish_pro_en.exe              : USB2UIS application program (Chinese)
         - HybridEdit.ocx                  : USB2UIS active file
         - Usb2ish.dll                     : USB2UIS dll file
      ********************************************************************************
       + LIB :([EXTRACT PATH]\LIB\)

          + Linux  : ([EXTRACT PATH]\LIB\Linux)
            
            - libUSB2UIS.so                : the lib file of linux system
            - install.sh                   : shell file for installing libusb2uis.so
          
          + Window : ([EXTRACT PATH]\LIB\Window\)
  
            + XXX   :([EXTRACT PATH]\LIB\Window\VB[VC]\32bit[64bit]\)
              
              - usb2uis.dll                : the dynamic link library file of window system
              - usb2uis.lib                : the static link library file of window system
      ********************************************************************************
       + DRIVER :([EXTRACT PATH]\DRIVER\)
          
          + ish : ([EXTRACT PATH]\DRIVER\ish)  
            
            + XXX : ([EXTRACT PATH]\DRIVER\(window Platform)\32bit[64bit]\)
            
              - usb2ish.cat                : the cat file of driver
              - usb2ish.inf                : the inf file of driver
              - usb2ish.sys                : the sys file of driver
              - WdfCoInstaller01009.dll    : the dll file for installing driver

          + uart : ([EXTRACT PATH]\DRIVER\uart)  
           
           + XXX : ([EXTRACT PATH]\DRIVER\(window Platform)\32bit[64bit]\)
             
             usb2uart.cat                  : the cat file of driver
             usb2uart.inf                  : the inf file of driver
             
      ********************************************************************************
      + FIRMWARE :([EXTRACT PATH]\FIRMWARE\) 
        
          - USB2ISH_FM_BXX.bin              : the firmware file to upgrade Basic type 
          - USB2ISH_FM_MXX.bin              : the firmware file to upgrade Extended type
          
      ********************************************************************************
      + DEMO :([EXTRACT PATH]\DEMO\)  
       
          + qt-creator301 : ([EXTRACT PATH]\DEMO\qt-creator301) 
          
            - I2C_RW _DEMO_V01.zip         : the compressed demo file for I2C read/write using Qt in the linux 
            - SPI_RW _DEMO_V01.zip         : the compressed demo file for SPI,PWM,GPIO read/write in the linux 
      
          + VS2010 : ([EXTRACT PATH]\DEMO\VS2010) 
            
             + VB  : ([EXTRACT PATH]\DEMO\VS2010\VB) 
               
                - SPI_RW.zip               : the compressed demo file for SPI read/write using VS2010 VB in the window
                - I2C_RW.zip               : the compressed demo file for I2C read/write using VS2010 VB in the window               
                
             + VC  : ([EXTRACT PATH]\DEMO\VS2010\VC) 
             
                - I2C_RW_APP_M00_05.zip    : the compressed demo file for I2c read/write using VS2010 VC in the window
                - SPI_RW_APP_M00_07.zip    : the compressed demo file for SPI read/write using VS2010 VC in the window
           
             + cbc2009  : ([EXTRACT PATH]\DEMO\cbc2009) 
 
                - RF_RW_APP_M00_07.zip     : the compressed demo file for nRF2401 module read/write using c++ builder 2009 in the window

             + labview2012  : ([EXTRACT PATH]\DEMO\labview2012) 
             
               - I2C_RW.zip    : the compressed demo file for I2c read/write using labview2012 in the window
               - SPI_RW.zip    : the compressed demo file for SPI read/write using labview2012 in the window
               - GPIO_RW.zip   : the compressed demo file for GPIO read/write using labview2012 in the window 
     
       + OTHER :([EXTRACT PATH]\OTHER\)
    
         - UartAssist.zip                 : a window tool soft for usb2uart test

Supported OS
***************

       + Window XP, Vista,7 ,8 ,10 (x86 & x64 Windows platforms)
       + Linux 

How to use (I2c,SPI,GPIO)
***************

       1- plug-in the USB2UIS board

       2- install driver

       3- run usb2ish_Pro.exe or usb2ish_Pro_en.exe as administrator
          
       4- Use it !


******************* COPYRIGHT 2016 OnEasyB electronics *****END OF FILE******

