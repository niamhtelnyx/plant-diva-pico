from machine import Pin, SPI
from time import sleep

spi = SPI(0, baudrate=1000000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(19), miso=Pin(16))

cs = Pin(17, Pin.OUT)
cs.value(1)

def read_mcp3008(channel):
    cs.value(0)
    command = bytearray([1, (8 + channel) << 4, 0])
    response = bytearray(3)
    spi.write_readinto(command, response)
    cs.value(1)

    return ((response[1] & 3) << 8) | response[2]

while True:
    moisture = read_mcp3008(0)

    if moisture > 630:
        print("Moisture:", moisture, "— WATER ME 😭")
    elif moisture > 560:
        print("Moisture:", moisture, "— Getting thirsty 👀")
    else:
        print("Moisture:", moisture, "— Thriving 🌿")

    sleep(1)

