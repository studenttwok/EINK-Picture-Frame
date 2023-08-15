import time
import spidev
import RPi.GPIO
import struct
from PIL import Image
import numpy as np

#Commands
IT8951_TCON_SYS_RUN = 0x0001
IT8951_TCON_SLEEP = 0x0003
IT8951_TCON_REG_RD = 0x0010
IT8951_TCON_REG_WR = 0x0011
IT8951_TCON_LD_IMG = 0x0020
IT8951_TCON_LD_IMG_AREA = 0x0021
IT8951_TCON_LD_IMG_END = 0x0022
USDEF_I80_CMD_DPY_AREA = 0x0034
USDEF_I80_CMD_GET_DEV_INFO = 0x0302
USDEF_I80_CMD_DPY_BUF_AREA = 0x0037	# Refer to ite_display_i80_example.c, There is only one image buffer in IT8951 so far.
USDEF_I80_CMD_VCOM = 0x0039

#Memory Converter Registers
LISAR = 0x0200 + 0x0008

#Update Parameter Setting Register
LUTAFSR = 0x1000 + 0x0224

# Pin
RST_PIN  = 17
CS_PIN   = 8
BUSY_PIN = 24

GPIO = RPi.GPIO
SPI = spidev.SpiDev()

########## GPIO and SPI ##########
def init_spi_and_gpio():
    SPI.open(0, 1)
    SPI.max_speed_hz = 12000000
    SPI.lsbfirst = False
    SPI.mode = 0b00

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(RST_PIN, GPIO.OUT)
    GPIO.setup(CS_PIN, GPIO.OUT)
    GPIO.setup(BUSY_PIN, GPIO.IN)
    GPIO.output(CS_PIN, 1)

def deinit_api_and_gpio():
    print("Module Exit")
    digital_write(CS_PIN, 0)
    digital_write(RST_PIN, 0)
    SPI.close()
    GPIO.output(RST_PIN, 0)
    GPIO.output(CS_PIN, 0)
    GPIO.cleanup([RST_PIN, CS_PIN, BUSY_PIN])

def digital_write(pin, value):
    GPIO.output(pin, value)

def digital_read(pin):
    return GPIO.input(pin)

def delay_ms(delaytime):
    time.sleep(delaytime / 1000.0)

# void LCDWaitForReady() from reference
def EPD_IT8951_ReadBusy():
    ulData = digital_read(BUSY_PIN)
    while (ulData == 0):
       ulData = digital_read(BUSY_PIN)

# Command 2 bytes 0xFFFF
def EPD_IT8951_WriteCommand(Command, shouldUp = True):
    # Set Preamble for Write Command
    # UWORD Write_Preamble = 0x6000
    EPD_IT8951_ReadBusy()
    digital_write(CS_PIN, 0)
    SPI.writebytes([0x60, 0x00])
    EPD_IT8951_ReadBusy()
    SPI.writebytes([msb(Command), lsb(Command)])
    #SPI.writebytes([0x60, 0x00, msb(Command), lsb(Command)])
    if shouldUp:
        digital_write(CS_PIN, 1)

# Wait for TCON ready
def EPD_IT8951_WaitForDisplayReady():
    #Check IT8951 Register LUTAFSR => NonZero Busy, Zero - Free
    ulData = EPD_IT8951_ReadReg(LUTAFSR)
    while( ulData != 0): #LUTAFSR, skip dummer return for 1
        ulData = EPD_IT8951_ReadReg(LUTAFSR)


# Buff 2 byte (0xFFFF)
def EPD_IT8951_WriteData(Buff):
    # UWORD Write_Preamble = 0x0000;
    #print("WriteData")
    #print(Buff)

    EPD_IT8951_ReadBusy()
    digital_write(CS_PIN, 0)
    SPI.writebytes([0x00, 0x00])
    EPD_IT8951_ReadBusy()
    SPI.writebytes([msb(Buff), lsb(Buff)])
    digital_write(CS_PIN, 1)

'''
# slow but reliable
# Buff is List of 2 byte [0x1111,0x2222]
def EPD_IT8951_WriteNData(Buff):
    # UWORD Write_Preamble = 0x0000;
    #print("WriteNData")
    #print(Buff)

    EPD_IT8951_ReadBusy()
    digital_write(CS_PIN, 0)
    SPI.writebytes([0x00, 0x00])

    for i in range(0, len(Buff)):
        EPD_IT8951_WriteNData
        SPI.writebytes([ msb(Buff[i]), lsb(Buff[i]) ])

    digital_write(CS_PIN, 1)
'''

# Buff is List of 2 byte [0x1111,0x2222]
def EPD_IT8951_WriteNData(Buff):
    # UWORD Write_Preamble = 0x0000;
    #print("WriteNData")
    #print(Buff)
    startTs = time.time()
    print(startTs)

    EPD_IT8951_ReadBusy()
    digital_write(CS_PIN, 0)
    SPI.writebytes([0x00, 0x00])


    # batch write
    batchSize = 1024
    totalLength = len(Buff)
    totalBatchNumber = int(totalLength / batchSize)
    if totalLength % batchSize != 0:
        totalBatchNumber += 1
    for i in range(0, totalBatchNumber):
        endIdx = (i * batchSize) + batchSize
        if endIdx > totalLength:
            endIdx = totalLength

        tmpBuffer = Buff[(i * batchSize):endIdx]
        #print(i*batchSize)
        #print(endIdx)
        tmpBuffer2 = []
        for j in range(0, len(tmpBuffer)):
            #EPD_IT8951_WriteNData
            tmpBuffer2+= [msb(tmpBuffer[j]), lsb(tmpBuffer[j])]

        SPI.writebytes(tmpBuffer2)

    digital_write(CS_PIN, 1)

    endTs = time.time()
    print(endTs)
    print("Used: %.2f"%((endTs-startTs)))



# return A WORD, 0xFFFF
def EPD_IT8951_ReadData():
    # UWORD Write_Preamble = 0x1000;
    #print("ReadData")

    EPD_IT8951_ReadBusy()
    digital_write(CS_PIN, 0)

    SPI.writebytes([0x10, 0x00])
    EPD_IT8951_ReadBusy()
    dummy = SPI.readbytes(2)
    EPD_IT8951_ReadBusy()
    result = SPI.readbytes(2)
    digital_write(CS_PIN, 1)

    return (result[0]<<8 | result[1])
    ## Read,  return as 2 bytes in list [0xAA, 0xBB]
    #return result

# NoOfWordToRead, don't count the dummy
def EPD_IT8951_ReadNData(NoOfWordToRead):
    # UWORD Write_Preamble = 0x1000;
    #print("ReadNData")

    EPD_IT8951_ReadBusy()
    digital_write(CS_PIN, 0)

    SPI.writebytes([0x10, 0x00])
    EPD_IT8951_ReadBusy()

    dummy = SPI.readbytes(2)
    #EPD_IT8951_ReadBusy()

    results = []
    for i in range(0, NoOfWordToRead):
        EPD_IT8951_ReadBusy()
        result = SPI.readbytes(2)
        results += result

    digital_write(CS_PIN, 1)
    return results

# Arg_Cmd is Word, Arg_Buf is list of word [0xFFFF, 0XFFFF]
def EPD_IT8951_WriteMultiArg(Arg_Cmd, Arg_Buf):
    EPD_IT8951_WriteCommand(Arg_Cmd)
    for i in range(0, len(Arg_Buf)):
        EPD_IT8951_WriteData(Arg_Buf[i])

# RegAddr is Word
def EPD_IT8951_ReadReg(RegAddr):
    #print("====Read Reg====")
    EPD_IT8951_WriteCommand(IT8951_TCON_REG_RD)	#IT8951_TCON_REG_RD 0x0010
    EPD_IT8951_WriteData(RegAddr)
    Reg_Value = EPD_IT8951_ReadData()
    #print("=== End Read Reg ===")
    return Reg_Value

# RegAddr is Word, RegValue is Word
def EPD_IT8951_WriteReg(RegAddr, RegValue):
    #print("====Write Reg====")
    EPD_IT8951_WriteCommand(IT8951_TCON_REG_WR) #IT8951_TCON_REG_RD 0x0010
    EPD_IT8951_WriteData(RegAddr)
    EPD_IT8951_WriteData(RegValue)
    #print("=== End Write Reg ===")

# VOM is 1 word(2bytes)
def EPD_IT8951_GetVCOM():
    EPD_IT8951_WriteCommand(USDEF_I80_CMD_VCOM)
    EPD_IT8951_WriteData(0x0000)
    VCOM = EPD_IT8951_ReadData()
    return VCOM

def EPD_IT8951_SetVCOM(VCOM):
    EPD_IT8951_WriteCommand(USDEF_I80_CMD_VCOM)
    EPD_IT8951_WriteData(0x0001)
    EPD_IT8951_WriteData(VCOM)

def swap_string(a):
    a[0::2], a[1::2] = a[1::2], a[0::2]
    return a

def pack_pixels(buf, pixel_format):
    """
    Take a buffer where each byte represents a pixel, and pack it
    into 16-bit words according to pixel_format.
    """
    buf = np.array(buf, dtype=np.ubyte)

    if pixel_format == 3: #PixelModes.M_8BPP
        rtn = np.zeros((buf.size//2,), dtype=np.uint16)
        rtn |= buf[1::2]
        rtn <<= 8
        rtn |= buf[::2]

    elif pixel_format == 0: #PixelModes.M_2BPP
        rtn = np.zeros((buf.size//8,), dtype=np.uint16)
        for i in range(7, -1, -1):
            rtn <<= 2
            rtn |= buf[i::8] >> 6
    elif pixel_format == 1: #PixelModes.M_3BPP
        rtn = np.zeros((buf.size//4,), dtype=np.uint16)
        for i in range(3, -1, -1):
            rtn <<= 4
            rtn |= (buf[i::4] & 0xFE) >> 4
    elif pixel_format == 2: #PixelModes.M_4BPP
        rtn = np.zeros((buf.size//4,), dtype=np.uint16)
        for i in range(3, -1, -1):
            rtn <<= 4
            rtn |= buf[i::4] >> 4
    else:
        rtn = None

    return rtn.tolist()

def msb(indata):
    return ((indata>>8) & 0xff)

def lsb(indata):
    return (indata & 0xff)

def epd_reset():
    #print("Reset EPD")
    digital_write(RST_PIN, 1)
    delay_ms(200)
    digital_write(RST_PIN, 0)
    delay_ms(10)
    digital_write(RST_PIN, 1)
    delay_ms(200)

def epd_start():
    #print("Run EPD")
    EPD_IT8951_WriteCommand(IT8951_TCON_SYS_RUN)

def epd_sleep():
    #print("Sleep")
    EPD_IT8951_WriteCommand(IT8951_TCON_SLEEP)

def epd_get_system_info():
    #print("GetSystemInfo")
    EPD_IT8951_WriteCommand(USDEF_I80_CMD_GET_DEV_INFO)
    Buf = EPD_IT8951_ReadNData(20)
    #print(Buf)
    sysInfoResult = struct.unpack(">4H16s16s", bytes(Buf))
    #print(sysInfoResult)

    sysInfo = dict()
    sysInfo['panelW'] = sysInfoResult[0]
    sysInfo['panelH'] = sysInfoResult[1]
    sysInfo['imgBufAddrL'] = sysInfoResult[2]
    sysInfo['imgBufAddrH'] = sysInfoResult[3]
    sysInfo['fwVersion'] = "".join(swap_string(list(sysInfoResult[4].decode('iso-8859-1'))))
    sysInfo['lutVersion'] = "".join(swap_string(list(sysInfoResult[5].decode('iso-8859-1'))))
    sysInfo['imgBufAddr'] = sysInfo['imgBufAddrH']*65536 + sysInfo['imgBufAddrL']

    #print(sysInfo)
    return sysInfo

def epd_enable_i80_format():
    #print("Enable i80")
    EPD_IT8951_WriteReg(IT8951_TCON_REG_WR, 0x0001)

# vcom is a float value, eg: -1.6
def epd_update_vcom(vcom):
    #print("VCOM")
    vcom_internal = int(abs(vcom)*1000)
    current_vcom = int(EPD_IT8951_GetVCOM())
    if (current_vcom != vcom_internal):
        #print(CurrentVCOM)
        EPD_IT8951_SetVCOM(vcom_internal)

def epd_set_buffer_memory_address(sysInfo):
    #print("Write Buffer Address")
    EPD_IT8951_WriteReg(LISAR+2, sysInfo['imgBufAddrH'])
    EPD_IT8951_WriteReg(LISAR, sysInfo['imgBufAddrL'])

def epd_refresh_region(x, y, w, h, mode):
    print("Display Whole")
    args2 = [
        x,
        y,
        w,
        h,
        mode
    ]
    EPD_IT8951_WriteMultiArg(USDEF_I80_CMD_DPY_AREA, args2)


def epd_load_image_buffer(imgBuf, imgInfo):
    # Wait for TCON Ready
    EPD_IT8951_WaitForDisplayReady()

    # Start load image start command  (Partial update)
    print("Start Load Image Area")
    args = [
        (imgInfo['endian_type'] << 8) | (imgInfo['pixel_format'] << 4) | imgInfo['rotate_mode'],
        imgInfo['x'],
        imgInfo['y'],
        imgInfo['width'],
        imgInfo['height']
    ]
    EPD_IT8951_WriteMultiArg(IT8951_TCON_LD_IMG_AREA, args)

    # transfer buffer to device
    # Packed formwat
    print("Write Image Data")
    EPD_IT8951_WriteNData(imgBuf)

    # Load Image End
    print("Load Img End")
    EPD_IT8951_WriteCommand(IT8951_TCON_LD_IMG_END)

def epd_load_image_file_to_device(filepath, x, y):
    # Prepare the image buffer
    imgBuf = Image.open(filepath).convert('L')
    width = imgBuf.width
    height = imgBuf.height
    imgBuf = pack_pixels(list(imgBuf.tobytes()), 2)

    # construct the imgInfo
    imgInfo = dict()
    imgInfo['rotate_mode'] = 0
    imgInfo['endian_type'] = 0 # LITTLE
    imgInfo['pixel_format'] = 2 #M_4BPP (16 bit 2^4 Grey scale)
    imgInfo['x'] = x
    imgInfo['y'] = y
    imgInfo['width'] = width
    imgInfo['height'] = height
    epd_load_image_buffer(imgBuf, imgInfo)

    return imgInfo

def epd_load_and_center_image_file_to_device(filepath, sysInfo):
    canvas = Image.new("L", (sysInfo['panelW'], sysInfo['panelH']), 0xff)
    imgBuf = Image.open(filepath).convert('L')

    # check long length
    # assume it is loadscape
    scale = canvas.width / imgBuf.width
    if (imgBuf.height > imgBuf.width):
        # port
        # calculate the scale
        scale = canvas.height / imgBuf.height

    imgBuf = imgBuf.resize((int(imgBuf.width * scale), int(imgBuf.height * scale)))

    #imgBuf.thumbnail((sysInfo['panelW'], sysInfo['panelH']))

    # scalee and paste the file
    x = int((sysInfo['panelW'] - imgBuf.width) / 2)
    y = int((sysInfo['panelH'] - imgBuf.height) / 2)
    canvas.paste(imgBuf, (x,y))

    # Prepare the image buffer
    imgBuf = canvas.convert('L')
    width = imgBuf.width
    height = imgBuf.height
    imgBuf = pack_pixels(list(imgBuf.tobytes()), 2)

    # construct the imgInfo
    imgInfo = dict()
    imgInfo['rotate_mode'] = 0
    imgInfo['endian_type'] = 0 # LITTLE
    imgInfo['pixel_format'] = 2 #M_4BPP (16 bit 2^4 Grey scale)
    imgInfo['x'] = 0
    imgInfo['y'] = 0
    imgInfo['width'] = sysInfo['panelW']
    imgInfo['height'] = sysInfo['panelH']
    epd_load_image_buffer(imgBuf, imgInfo)

    return imgInfo


# color ex: 0xffff = Black, 0x0000 = White, one word(2bytes) = 4 pixels
def epd_fill_device(color, sysInfo):
    # Prepare the image Buffer
    imgBuf = [color] * int((sysInfo['panelW'] * sysInfo['panelH']) / 4)

    # construct the imgInfo
    imgInfo = dict()
    imgInfo['rotate_mode'] = 0
    imgInfo['endian_type'] = 0 # LITTLE
    imgInfo['pixel_format'] = 2 #M_4BPP (16 bit 2^4 Grey scale)
    imgInfo['x'] = 0
    imgInfo['y'] = 0
    imgInfo['width'] = sysInfo['panelW']
    imgInfo['height'] = sysInfo['panelH']
    epd_load_image_buffer(imgBuf, imgInfo)
    return imgInfo

def epd_refresh_whole_screen(sysInfo):
    epd_refresh_region(0, 0, sysInfo['panelW'], sysInfo['panelH'], 2)

def epd_clear_whole_screen(sysInfo):
    epd_refresh_region(0, 0, sysInfo['panelW'], sysInfo['panelH'], 0)


def display(filename):
    ##########
    # init SPI and GPIO
    init_spi_and_gpio()

    # reset EPD
    epd_reset()

    # system run
    epd_start()

    # GetSystemInfo
    sysInfo = epd_get_system_info()

    # enable i80 packed mode
    epd_enable_i80_format()

    # VCOM
    epd_update_vcom(-1.6)

    # set the img buffer address
    epd_set_buffer_memory_address(sysInfo)

    # clear everything first
    epd_clear_whole_screen(sysInfo)


    # Update frame
    x = 1072
    y = 804

    #imgInfo = epd_load_image_file_to_device('./pic/1872x1404.bmp', 0, 0)
    #imgInfo = epd_load_image_file_to_device('./pic/800x600.bmp', x, y)
    #epd_fill_device(0x0000, sysInfo)
    epd_load_and_center_image_file_to_device(filename, sysInfo)

    # Refresh Display
    #epd_refresh_region(x, y, imgInfo['width'], imgInfo['height'], 2)
    epd_refresh_whole_screen(sysInfo)

    # Put EPD to Sleep
    epd_sleep()

    # Module Exit
    deinit_api_and_gpio()


if __name__ == "__main__":
   display('./pic/800x600.bmp')

