using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using CyUSB;
using System.Diagnostics;
using System.Reflection;

namespace ADI
{
    public class AD5372
    {
        public static CyFX2Device USB = null;

        //[DllExport("AD5372_Init")]
        public static bool Init()
        {
            CyConst.SetCustomerGUID("{89982a59-5eea-45aa-af97-52ec351018c2}", "{D2958cfd-f0e1-4752-8aff-06d5b4411024}");
            USBDeviceList usbDevices = new USBDeviceList(CyConst.DEVICES_CYUSB);
            USB = usbDevices[0x0456, 0xB20F] as CyFX2Device;
            if (USB == null)
            {
                Console.WriteLine("AD5372 is not connected!");
                return false;
            }
            if (!USB.LoadExternalRam("AD537xSPI.hex"))
            {
                Console.WriteLine("downloading firmware failed!");
                return false;
            }
            int len = 0;
            byte[] buf = null;
            if (!Vendor_Request(0xE0, 0, 0, 0, ref len, ref buf))
            {
                Console.WriteLine("initialization failed!");
                return false;
            }
            Reset();
            return true;
        }

        //[DllExport("AD5372_Reset")]
        public static bool Reset()
        {
            int len = 0;
            byte[] buf = null;
            if (!Vendor_Request(0xDA, 0, 0, 0, ref len, ref buf))
            {
                Console.WriteLine("reset failed!");
                return false;
            }
            if (!Vendor_Request(0xDB, 0, 0, 0, ref len, ref buf))
            {
                Console.WriteLine("reset failed!");
                return false;
            }
            SPI(0x022000);
            LDAC();
            SPI(0x032000);
            LDAC();
            for (int i = 0; i < 32; ++i)
                DAC(i, 0.0);
            LDAC();
            return true;
        }

        public static bool Vendor_Request(byte req, ushort val, ushort idx, byte dir, ref int len, ref byte[] buf)
        {
            CyControlEndPoint pt = USB.ControlEndPt;
            pt.Target = CyConst.TGT_DEVICE;
            pt.ReqType = CyConst.REQ_VENDOR;
            pt.ReqCode = req;
            pt.Value = val;
            pt.Index = idx;
            //Console.WriteLine("val = {0:X}, idx = {1:X}", val, idx);
            pt.Direction = (dir > 0) ? CyConst.DIR_FROM_DEVICE : CyConst.DIR_TO_DEVICE;
            return pt.XferData(ref buf, ref len);
        }

        //[DllExport("AD5372_LDAC")]
        public static bool LDAC()
        {
            int len = 0;
            byte[] buf = null;
            return Vendor_Request(0xDE, 0, 0, 0, ref len, ref buf);
        }

        //[DllExport("AD5372_SPI")]
        public static bool SPI(int word)
        {
            int len = 0;
            byte[] buf = null;
            //Console.WriteLine("word = {0:X}", word);
            return Vendor_Request(0xDD, (ushort)(word & 0xFFFF), (ushort)((word >> 16) & 0xFF), 0, ref len, ref buf);
        }

        //[DllExport("AD5372_DAC")]
        public static bool DAC(int channel, double voltage)
        {
            float vmax = 10;
            float vmin = -10;
            ushort val = (ushort)(0xFFFF * (voltage / (vmax - vmin) + 0.5));
            byte idx = (byte)(64 * 3 + 8 * ((channel >> 3) + 1) + (channel & 7));
            return SPI((idx << 16) + val);
        }

        [DllExport("AD5372_Init")]
        public static bool AD5372_Init()
        {
            try
            {
                return Init();
            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());
            }
            return false;
        }

        [DllExport("AD5372_Reset")]
        public static bool AD5372_Reset()
        {
            try
            {
                return Reset();
            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());
            }
            return false;
        }

        [DllExport("AD5372_LDAC")]
        public static bool AD5372_LDAC()
        {
            try
            {
                return LDAC();
            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());
            }
            return false;
        }

        [DllExport("AD5372_SPI")]
        public static bool AD5372_SPI(int word)
        {
            try
            {
                return SPI(word);
            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());
            }
            return false;
        }

        [DllExport("AD5372_DAC")]
        public static bool AD5372_DAC(int channel, double voltage)
        {
            try
            {
                return DAC(channel, voltage);
            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());
            }
            return false;
        }
    }
}