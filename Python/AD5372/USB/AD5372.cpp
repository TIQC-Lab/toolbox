#include <Windows.h>
#include "inc/CyAPI.h"
#include <stdio.h>

#pragma comment(lib,"lib/x64/CyAPI.lib")

CCyUSBDevice *USB = NULL;

bool Vendor_Request(UCHAR req, WORD val, WORD idx, UCHAR dir, long &len, UCHAR *buf)
{
	CCyControlEndPoint *pt = USB->ControlEndPt;
	pt->Target = TGT_DEVICE;
    pt->ReqType = REQ_VENDOR;
	pt->ReqCode = req;
	pt->Value = val;
	pt->Index = idx;
	pt->Direction = (dir > 0) ? DIR_FROM_DEVICE : DIR_TO_DEVICE;;
	return pt->Write(buf, len);
}

bool LoadRAM(char *fileName)
{	
	CCyControlEndPoint *pt = USB->ControlEndPt;
    UINT fwSize = 0;
    PUCHAR FwImage;
    FILE *FwImagePtr;    
    
    fopen_s(&FwImagePtr, fileName, "rb");
    if (FwImagePtr == NULL)
        return false;

    /* Find the length of the image */
    fseek (FwImagePtr, 0, SEEK_END);
    fwSize = ftell(FwImagePtr);
    fseek (FwImagePtr, 0, SEEK_SET);

    /* Allocate memory for the image */
    FwImage =  new UCHAR[fwSize];

    if (FwImage == NULL)
        return false;

    if (fwSize <= 0)
    {
        fclose (FwImagePtr);
        return false;
    }

    /* Read into buffer */
    fread (FwImage, fwSize, 1, FwImagePtr);
    fclose (FwImagePtr);

	long len = 1;
	UCHAR buf[1];

	buf[0] = 1;
	Vendor_Request(0xA0,0xE600,0,0,len,buf); // Halt

    pt->ReqCode = 0xA0;
    pt->Index = 0;

    int chunk = 2048;
    UCHAR buffer[2048];
	int FwOffset = 0;
    for (int i = FwOffset; i < fwSize; i += chunk)
    {
        pt->Value = i;
        long len = ((i + chunk) < fwSize) ? chunk : fwSize - i;
		memcpy(buffer, FwImage+i, len);
        if (!pt->Write(buffer, len)) return false;
	}

	buf[0] = 0;
	Vendor_Request(0xA0,0xE600,0,0,len,buf);

	if(FwImage)
		delete[] FwImage;

	return true;
}

#define DLL extern "C" __declspec(dllexport)

DLL bool AD5372_LDAC()
{
    long len = 0;
    return Vendor_Request(0xDE, 0, 0, 0, len, NULL);
}

DLL bool AD5372_SPI(int word)
{
    long len = 0;
    //printf("word = %X", word);
    return Vendor_Request(0xDD, word & 0xFFFF, (word >> 16) & 0xFF, 0, len, NULL);
}

DLL bool AD5372_DAC(int channel, double voltage)
{
    double vmax = 10;
    double vmin = -10;
    USHORT val = (USHORT)(0xFFFF * (voltage / (vmax - vmin) + 0.5));
    BYTE idx = (BYTE)(64 * 3 + 8 * ((channel >> 3) + 1) + (channel & 7));
    return AD5372_SPI((idx << 16) + val);
}

DLL bool AD5372_Reset()
{
	long len = 0;
    if (!Vendor_Request(0xDA, 0, 0, 0, len, NULL))
    {
        printf("reset failed!");
        return false;
    }
    if (!Vendor_Request(0xDB, 0, 0, 0, len, NULL))
    {
        printf("reset failed!");
        return false;
    }
    AD5372_SPI(0x022000);
    AD5372_LDAC();
    AD5372_SPI(0x032000);
    AD5372_LDAC();
    for (int i = 0; i < 32; ++i)
        AD5372_DAC(i, 0.0);
    AD5372_LDAC();
    return true;
}

#ifdef UNICODE
#define MAKEINTRESOURCEA_T(a, u) MAKEINTRESOURCEA(u)
#else
#define MAKEINTRESOURCEA_T(a, u) MAKEINTRESOURCEA(a)
#endif
BOOL GUIDFromString(LPCTSTR psz, LPGUID pguid)
{
    BOOL bRet = FALSE;

    typedef BOOL (WINAPI *LPFN_GUIDFromString)(LPCTSTR, LPGUID);
    LPFN_GUIDFromString pGUIDFromString = NULL;

    HINSTANCE hInst = LoadLibrary(TEXT("shell32.dll"));
    if (hInst)
    {
        pGUIDFromString = (LPFN_GUIDFromString) GetProcAddress(hInst, MAKEINTRESOURCEA_T(703, 704));
        if (pGUIDFromString)
            bRet = pGUIDFromString(psz, pguid);
        FreeLibrary(hInst);
    }

    if (!pGUIDFromString)
    {
        hInst = LoadLibrary(TEXT("Shlwapi.dll"));
        if (hInst)
        {
            pGUIDFromString = (LPFN_GUIDFromString) GetProcAddress(hInst, MAKEINTRESOURCEA_T(269, 270));
            if (pGUIDFromString)
                bRet = pGUIDFromString(psz, pguid);
            FreeLibrary(hInst);
        }
    }

    return bRet;
}

DLL bool AD5372_Open()
{
    GUID guid;
	GUIDFromString("{D2958cfd-f0e1-4752-8aff-06d5b4411024}",&guid); 
	USB = new CCyUSBDevice(NULL, guid);
	int devices = USB->DeviceCount();
	int vID, pID;
	int d = 0;
	do {
		// Open() automatically calls Close() if necessary
		USB->Open(d);
		vID = USB->VendorID;
		pID = USB->ProductID;
		//printf("VID = %04X, PID = %04X\n",vID,pID);
		if ((vID == 0x0456) && (pID == 0xB20F)) break;
		d++;
	} while (d < devices);
	if (d == devices) {
		printf("AD5372 is not connected!");
		return false;
	}
}

DLL bool AD5372_Init()
{
	if (!LoadRAM("AD537xSPI.bin")) {
		printf("downloading firmware failed!");
		return false;
	}
	long len = 0;
	if (!Vendor_Request(0xE0, 0, 0, 0, len, NULL))
    {
        printf("initialization failed!");
        return false;
    }
	return true;
}

int main(int argc, char **argv)
{
    AD5372_Open();
	AD5372_Init();
	AD5372_Reset();
	AD5372_DAC(0,argc > 1 ? atof(argv[1]) : 1.0);
	AD5372_LDAC();
	return 0;
}