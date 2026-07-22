import network
import time
import urequests

from machine import Pin, SPI, PWM
from secrets import SSID, PASSWORD, NTFY_TOPIC


# -----------------------
# WIFI
# -----------------------

def connect_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)

    if not wifi.isconnected():
        print("Connecting to Wi-Fi...")
        wifi.connect(SSID, PASSWORD)

        timeout = 20

        while not wifi.isconnected() and timeout > 0:
            print(".", end="")
            time.sleep(1)
            timeout -= 1

    if not wifi.isconnected():
        raise RuntimeError("Could not connect to Wi-Fi")

    print("\nConnected!")
    print("IP address:", wifi.ifconfig()[0])

    return wifi


# -----------------------
# NTFY NOTIFICATION
# -----------------------

def send_notification(title, message):
    url = "https://ntfy.sh/" + NTFY_TOPIC
    response = None

    try:
        print("Sending notification...")

        response = urequests.post(
            url,
            data=message.encode(),
            headers={
                "Title": title,
                "Priority": "high",
                "Tags": "seedling,droplet"
            }
        )

        print("Notification status:", response.status_code)

        if 200 <= response.status_code < 300:
            print("Notification sent successfully!")
        else:
            print("Notification failed:", response.text)

    except Exception as error:
        print("Notification error:", error)

    finally:
        if response is not None:
            response.close()


# -----------------------
# MCP3008 / SPI
# -----------------------

spi = SPI(
    0,
    baudrate=1_000_000,
    polarity=0,
    phase=0,
    sck=Pin(18),
    mosi=Pin(19),
    miso=Pin(16)
)

cs = Pin(17, Pin.OUT)
cs.value(1)


def read_mcp3008(channel):
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be between 0 and 7")

    command = bytearray([1, (8 + channel) << 4, 0])
    response = bytearray(3)

    cs.value(0)
    spi.write_readinto(command, response)
    cs.value(1)

    return ((response[1] & 3) << 8) | response[2]


# -----------------------
# RGB LED
# -----------------------

red = PWM(Pin(13))
green = PWM(Pin(14))
blue = PWM(Pin(15))

for led in (red, green, blue):
    led.freq(1000)


def set_color(r, g, b):
    red.duty_u16(int(r * 65535))
    green.duty_u16(int(g * 65535))
    blue.duty_u16(int(b * 65535))


# -----------------------
# PLANT DIVA LOGIC
# -----------------------

DRY_THRESHOLD = 650
HAPPY_THRESHOLD = 615

alert_sent = False

connect_wifi()

print("Plant Diva is online!")

while True:
    moisture = read_mcp3008(0)

    print("Moisture:", moisture)

    if moisture >= DRY_THRESHOLD:
        set_color(1, 0, 0)
        print("WATER ME")

        if not alert_sent:
            send_notification(
                "Plant Diva Needs Water",
                "Plant Diva is thirsty! Moisture reading: {}.".format(moisture)
            )

            alert_sent = True

    elif moisture > HAPPY_THRESHOLD:
        set_color(1, 0.5, 0)
        print("Getting thirsty")

    else:
        set_color(0, 1, 0)
        print("I'm good")

        if alert_sent:
            print("Plant has recovered. Alert reset.")

        alert_sent = False

    time.sleep(5)

