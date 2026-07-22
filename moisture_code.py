from machine import Pin, SPI
from time import sleep

# SPI setup
spi = SPI(
    0,
    baudrate=1000000,
    polarity=0,
    phase=0,
    sck=Pin(18),
    mosi=Pin(19),
    miso=Pin(16)
)

# Chip Select pin
cs = Pin(17, Pin.OUT)
cs.value(1)

def read_mcp3008(channel):
    if channel < 0 or channel > 7:
        return -1

    cs.value(0)

    command = bytearray([
        1,
        (8 + channel) << 4,
        0
    ])

    response = bytearray(3)

    spi.write_readinto(command, response)

    cs.value(1)

    value = ((response[1] & 3) << 8) | response[2]

    return value

while True:
    moisture = read_mcp3008(0)  # CH0

    print("Moisture:", moisture)

    sleep(1)
