import network
import time
import urequests

from secrets import SSID, PASSWORD, NTFY_TOPIC


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
                "Tags": "seedling,droplet",
            },
        )

        print("Status code:", response.status_code)
        print("Response:", response.text)

        if 200 <= response.status_code < 300:
            print("Notification sent!")
        else:
            print("Notification was rejected.")

    except Exception as error:
        print("Notification error:", error)

    finally:
        if response is not None:
            response.close()


connect_wifi()

send_notification(
    "Plant Diva Test",
    "The Pico 2 W just sent your first app notification!"
)

