from machine import Pin, SPI, PWM
from time import sleep

# MCP3008 SPI setup
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

# RGB LED pins
red = PWM(Pin(13))
green = PWM(Pin(14))
blue = PWM(Pin(15))

for led in [red, green, blue]:
    led.freq(1000)

def set_color(r, g, b):
    red.duty_u16(int(r * 65535))
    green.duty_u16(int(g * 65535))
    blue.duty_u16(int(b * 65535))

while True:
    moisture = read_mcp3008(0)

    if moisture >= 650:
        set_color(1, 0, 0)      # Red
        print("Moisture:", moisture, "— WATER ME 😭")

    elif moisture > 615:
        set_color(0, 0, 1)    # Yellow/Orange
        print("Moisture:", moisture, "— Getting thirsty 👀")

    else:
        set_color(0, 1, 0)      # Green
        print("Moisture:", moisture, "— I'm good 🌿")

    sleep(1)

