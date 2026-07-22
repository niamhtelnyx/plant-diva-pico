import network
import time
import urequests

from secrets import (
    SSID,
    PASSWORD,
    TELNYX_API_KEY,
    TELNYX_FROM,
    TELNYX_TO,
)


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


def send_sms(message):
    url = "https://api.telnyx.com/v2/messages"

    headers = {
        "Authorization": "Bearer " + TELNYX_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "from": TELNYX_FROM,
        "to": TELNYX_TO,
        "text": message,
    }

    response = None

    try:
        print("Sending SMS...")

        response = urequests.post(
            url,
            headers=headers,
            json=payload,
        )

        print("Status code:", response.status_code)
        print("Response:", response.text)

        if 200 <= response.status_code < 300:
            print("SMS request accepted!")
        else:
            print("Telnyx rejected the request.")

    except Exception as error:
        print("SMS error:", error)

    finally:
        if response is not None:
            response.close()


connect_wifi()

send_sms(
    "Circuit Queens test! The Pico 2 W just sent this text through Telnyx."
)
