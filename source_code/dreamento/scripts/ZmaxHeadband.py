import numpy as np
import time
import enum

from scripts.ZmaxSocket import ZmaxSocket
from scripts.CustomSocket import CustomSocket


class ZmaxDataID(enum.Enum):
    eegr = 0
    eegl = 1
    dx = 2
    dy = 3
    dz = 4
    bodytemp = 5
    bat = 6
    noise = 7
    light = 8
    nasal_l = 9
    nasal_r = 10
    oxy_ir_ac = 11
    oxy_r_ac = 12
    oxy_dark_ac = 13
    oxy_ir_dc = 14
    oxy_r_dc = 15
    oxy_dark_dc = 16


def connect():
    # sendSocket: the standard TCP socket used to send data to the headband. (Normally we would read from that socket aswell, but reading seems not to work.
    # readSocket: a RAW socket, which reads everything but discards everything but the designated port and message structure.

    sendSocket = ZmaxSocket()
    readSocket = CustomSocket()

    sendSocket.connect()
    readSocket.connect()
    if readSocket.serverConnected and sendSocket.serverConnected:
        sendSocket.sendString('HELLO\n')
        time.sleep(0.3)  # sec
        return readSocket, sendSocket
    else:
        return None, None


class ZmaxHeadband():
    def __init__(self):
        self.buf_size = 3 * 256  # 3 seconds at 256 frames per second (plotting can be SLOW)
        self.buf_eeg1 = np.zeros((self.buf_size, 1))
        self.buf_eeg2 = np.zeros((self.buf_size, 1))
        self.buf_dx = np.zeros((self.buf_size, 1))
        self.buf_dy = np.zeros((self.buf_size, 1))
        self.buf_dz = np.zeros((self.buf_size, 1))
        self.readSocket, self.writeSocket = connect()
        self.msgn = 1  # message number for sending stimulation

    #@profile
    def read(self, reqIDs=[0, 1]):
        """
        output refers to a list of lists of the desired outputs of the function for example [0,1,3] returns [[eegl, eegr, dy], [eegl, eegr, dy]]
        [0=eegr, 1=eegl, 2=dx, 3=dy, 4=dz, 5=bodytemp, 6=bat, 7=noise, 8=light, 9=nasal_l, 10=nasal_r, 11=oxy_ir_ac,
            12=oxy_r_ac, 13=oxy_dark_ac, 14=oxy_ir_dc, 15=oxy_r_dc, 16=oxy_dark_dc]
        """
        reqVals = []
        buf = self.readSocket.read_socket_buffer_for_port()

        for line in buf.split('\n'):
            if str.startswith(line, 'DEBUG'):  # ignore debugging messages from server
                pass

            else:
                if str.startswith(line, 'D'):  # only process data packets
                    p = line.split('.')

                    if len(p) == 2:
                        line = p[1]
                        packet_type = self.getbyteat(line, 0)
                        if (packet_type >= 1) and (packet_type <= 11):  # packet type within correct range
                            if len(line) == 120: #119
                                # EEG channels
                                eegr = self.getwordat(line, 1)
                                eegl = self.getwordat(line, 3)
                                # Accelerometer channels
                                dx = self.getwordat(line, 5)
                                dy = self.getwordat(line, 7)
                                dz = self.getwordat(line, 9)
                                # PPG channels (not plotted)
                                oxy_ir_ac = self.getwordat(line, 27)  # requires external nasal sensor
                                oxy_r_ac = self.getwordat(line, 25)  # requires external nasal sensor
                                oxy_dark_ac = self.getwordat(line, 34)  # requires external nasal sensor
                                oxy_ir_dc = self.getwordat(line, 17)  # requires external nasal sensor
                                oxy_r_dc = self.getwordat(line, 15)  # requires external nasal sensor
                                oxy_dark_dc = self.getwordat(line, 32)  # requires external nasal sensor
                                # other channels (not plotted)
                                bodytemp = self.getwordat(line, 36)
                                nasal_l = self.getwordat(line, 11)  # requires external nasal sensor
                                nasal_r = self.getwordat(line, 13)  # requires external nasal sensor
                                light = self.getwordat(line, 21)
                                bat = self.getwordat(line, 23)
                                noise = self.getwordat(line, 19)
                                # convert
                                eegr, eegl = self.ScaleEEG(eegr), self.ScaleEEG(eegl)
                                dx, dy, dz = self.ScaleAccel(dx), self.ScaleAccel(dy), self.ScaleAccel(dz)
                                bodytemp = self.BodyTemp(bodytemp)
                                bat = self.BatteryVoltage(bat)
                                # for function return
                                result = [eegr, eegl, dx, dy, dz, bodytemp, bat, noise, light, nasal_l, nasal_r, \
                                          oxy_ir_ac, oxy_r_ac, oxy_dark_ac, oxy_ir_dc, oxy_r_dc, oxy_dark_dc]
                                vals = []
                                for i in reqIDs:
                                    vals.append(result[i])
                                reqVals.append(vals)

        return reqVals

    def getbyteat(self, buf, idx=0):
        """
        for example getbyteat("08-80-56-7F-EA",0) -> hex2dec(08)
                    getbyteat("08-80-56-7F-EA",2) -> hex2dec(56)
        """
        s = buf[idx * 3:idx * 3 + 2]
        return self.hex2dec(s)

    def getwordat(self, buf, idx=0):
        w = self.getbyteat(buf, idx) * 256 + self.getbyteat(buf, idx + 1)
        return w

    def ScaleEEG(self, e):  # word value to uV
        uvRange = 3952
        d = e - 32768
        d = d * uvRange
        d = d / 65536
        return d

    def ScaleAccel(self, dx):  # word value to 'g'
        d = dx * 4 / 4096 - 2
        return d

    def BatteryVoltage(self, vbat):  # word value to Volts
        v = vbat / 1024 * 6.60
        return v

    def BodyTemp(self, bodytemp):  # word value to degrees C
        v = bodytemp / 1024 * 3.3
        t = 15 + ((v - 1.0446) / 0.0565537333333333)
        return t

    def hex2dec(self, s):
        """return the integer value of a hexadecimal string s"""
        return int(s, 16)

    def dec2hex(self, n, pad=0):
        """return the hexadecimal string representation of integer n"""
        s = "%X" % n
        if pad == 0:
            return s
        else:
            # for example if pad = 3, the dec2hex(5,2) = '005'
            return s.rjust(pad, '0')

    def stimulate(self, rgb1=(0, 0, 2), rgb2=(0, 0, 2), pwm1=254, pwm2=0, t1=1, t2=3, reps=5, vib=1, alt=0):
        """
        example:
        LIVEMODE_SENDBYTES 15 6 111 04-00-00-02-00-00-02-FE-00-01-03-05-01-00\r\n
        command = "LIVEMODE_SENDBYTES"
        retries = 15
        msgn = 6
        retry_ms = 111
        LIVECMD_FLASHLEDS = 04
        r = 00
        g = 00
        b = 02
        r2 = 00
        g2 = 00
        b2 = 02
        pwm1 = FE (254); intensity from 2(1%) to 254(100%)
        pwm2 = 00
        t1 = 01
        t2 = 03
        reps = 05
        vib = 01
        alt = 00 # althernate eyes
        """
        command = "LIVEMODE_SENDBYTES"
        retries = 15
        retry_ms = 111
        LIVECMD_FLASHLEDS = 4

        i1 = self.dec2hex(LIVECMD_FLASHLEDS, pad=2)
        i2 = self.dec2hex(rgb1[0], pad=2)
        i3 = self.dec2hex(rgb1[1], pad=2)
        i4 = self.dec2hex(rgb1[2], pad=2)
        i5 = self.dec2hex(rgb2[0], pad=2)
        i6 = self.dec2hex(rgb2[1], pad=2)
        i7 = self.dec2hex(rgb2[2], pad=2)
        i8 = self.dec2hex(pwm1, pad=2)
        i9 = self.dec2hex(pwm2, pad=2)
        i10 = self.dec2hex(t1, pad=2)
        i11 = self.dec2hex(t2, pad=2)
        i12 = self.dec2hex(reps, pad=2)
        i13 = self.dec2hex(vib, pad=2)
        i14 = self.dec2hex(alt, pad=2)

        s = f"""{command} {retries} {self.msgn} {retry_ms} {i1}-{i2}-{i3}-{i4}\
-{i5}-{i6}-{i7}-{i8}-{i9}-{i10}-{i11}-{i12}-{i13}-{i14}\r\n"""
        # print(s)
        self.writeSocket.sendString(s)
        self.msgn += 1


if __name__ == '__main__':
    hb = ZmaxHeadband()
    print(hb.readSocket)
    print(hb.writeSocket)

