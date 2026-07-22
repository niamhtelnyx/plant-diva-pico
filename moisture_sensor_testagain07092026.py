from machine import Pin, SPI
from time import sleep

spi = SPI(
    0,
    baudrate=100000,
    polarity=0,
    phase=0,
    sck=Pin(18),
    mosi=Pin(19),
    miso=Pin(16)
)

cs = Pin(17, Pin.OUT)
cs.value(1)

def read_mcp3008(channel):
    tx = bytearray([1, (8 + channel) << 4, 0])
    rx = bytearray(3)

    cs.value(0)
    spi.write_readinto(tx, rx)
    cs.value(1)

    print("TX:", list(tx), "RX:", list(rx))
    return ((rx[1] & 3) << 8) | rx[2]

while True:
    value = read_mcp3008(0)
    print("Moisture:", value)
    sleep(1)
