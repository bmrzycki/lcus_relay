import time
import struct
import serial  # external PySerial 3.0+

__author__     = "Brian Rzycki"
__copyright__  = "Copyright 2020, Brian Rzycki"
__credits__    = [ "Brian Rzycki" ]
__license__    = "Apache-2.0"
__version__    = "1.0.0"
__maintainer__ = "Brian Rzycki"
__email__      = "brzycki@gmail.com"
__status__     = "Production"

class Relay(object):
    """
    Controls the LCUS* series of intelligent control USB
    relay modules. These modules appear as a serial device (tty
    on Linux/Mac, COM on Windows) to the host OS.

    This class was created and tested using the LCUS_X2 2 relay
    module:
      www.chinalctech.com/cpzx/Programmer/Relay_Module/115.html
    purchased from Amazon branded under the name "NOYITO":
      amzn.com/B081RM7PMY

    The LCUS-4 documentation was used due to being more
    comprehensive (and also listed a status command):
      www.chinalctech.com/cpzx/32.html
    The serial port settings are shown in a screenshot as:
      9600 bps, 8 bits, 1 stop bit, no parity, no flow control

    Finally, to avoid confusion, relay numbering starts at 1 to
    match the numbering on the hardware device.  In many methods
    relay == 0 denotes "every relay".
    """
    def __init__(self, port, relays=0, init=True):
        """
        Initalize the Relay class.
          port(str) : The serial port to attach to.
          relays(int) : Number of maximum relays on the device. If
                        0 the number is queried from the device.
          init(bool)  : When True initialize the device by placing
                        all relays in the OFF state.
        """
        # The LCUS_X2 showed this as a stable value.
        self._timeout = 0.05  # 50 ms read timeout
        # Using write_timeout=None makes all writes blocking.
        self._hw = serial.Serial(
            port=port, timeout=self._timeout, write_timeout=None,
            baudrate=9600, bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE,
            xonxoff=False, rtscts=False, dsrdtr=False)
        if relays <= 0:
            self._status_len = 16384     # status read is huge to be safe
            relays = len(self.status())  # get relay count from status
        self.relays = list(range(1, relays + 1))
        # Calculate the length string returned by status. The padding
        # for 'ON ' vs 'OFF' means it's a fixed number of bytes every
        # time. Knowing the exact status length prevents read timeouts
        # making status queries faster.
        self._status_len = 0
        for r in self.relays:
            self._status_len += len('CH%d: OFF\r\n' % r)
        if init:
            self.off()
        return

    def _send(self, relay, cmd):
        # The on/off syntax is a fixed 4 byte command:
        #   START RELAY COMMAND END_CHECK
        #   0xA0  0x01  0x00    0xA1
        #
        # The START byte is always 0xA0 and denotes a relay command. The
        # second RELAY byte is the relay number to alter and starts counting
        # from 1.  The third COMMAND byte is 0x00 for OFF (open) and 0x01 for
        # ON (closed).  The fourth END_CHECK byte is the sum of the previous
        # three bytes as a simple checksum validator.  Here's the complete
        # list of byte commands for a 2 relay device:
        #   A0 01 00 A1  # 1 off
        #   A0 01 01 A2  # 1 on
        #   A0 02 00 A2  # 2 off
        #   A0 02 01 A3  # 2 on
        if cmd not in (0x00, 0x01):
            return False
        if relay == 0:
            relay = self.relays  # Perform on all available relays
        elif relay in self.relays:
            relay = [relay]
        else:
            return False
        for r in relay:
            self._hw.write(struct.pack('4B', 0xA0, r, cmd, 0xA0 + r + cmd))
        return True

    def off(self, relay=0):
        """
        Turn a relay OFF (open). Returns True if the command was sent to
        the device.
          relay(int): The relay to turn off with relay == 0 denoting all
                      relays.
        """
        return self._send(relay, cmd=0x00)

    def on(self, relay=0):
        """
        Turn a relay ON (closed). Returns True if the command was sent to
        the device.
          relay(int): The relay to turn on with relay == 0 denoting all
                      relays.
        """
        return self._send(relay, cmd=0x01)

    def status(self, relay=0):
        """
        Returns a dict with the current status of the relays on device.
        The dict has the format of { relay_num(int) : is_on(bool), ... }.
          relay(int): The relay to query with relay == 0 denoting all
                      relays.
        """
        # Status is returned when a single byte request of 0xFF is sent.
        # The device returns an ASCII string with the current state of the
        # relays. Here's an example response from a 2 relay device:
        #  'CH1: ON \r\nCH2: OFF\r\n'
        #
        # Read status twice in a row. Testing often showed stale status after
        # a single read.
        for i in range(2):
            self._hw.write(struct.pack('B', 0xFF))
            buf = self._hw.read(self._status_len)
        d = {}
        for line in buf.decode().split('\r\n'):
            if line:
                tmp = line.split(': ')
                if len(tmp) == 2:
                    d[int(tmp[0][2:])] = tmp[1] == 'ON '
        return d

    def toggle(self, relay=0, pause=500):
        """
        Toggles a relay on -> pause -> off. Returns True if the on/off
        commands were sent to the device. NOTE: The caller is expected to
        check/set the relay to off (open) before calling. If a relay is
        already on (closed) at the time of this call this method will
        simply act like .close(relay_number).
          relay(int): The relay to toggle with relay == 0 denoting all
                      relays.
          pause(int): Time, in milliseconds, to hold the relay on (closed).
        """
        if self.on(relay):
            time.sleep(pause / 1000.0)
            return self.off(relay)
        return False
