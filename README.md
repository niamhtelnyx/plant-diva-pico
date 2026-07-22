# Plant Diva Pico

MicroPython code for a Raspberry Pi Pico 2 W plant moisture monitor.

The project reads a moisture sensor through an MCP3008 ADC, shows plant status with an RGB LED, and can send notifications when the plant needs water.

## Hardware

- Raspberry Pi Pico 2 W
- MCP3008 analog-to-digital converter
- Analog moisture sensor connected to MCP3008 channel 0
- RGB LED

## Pin Map

| Function | Pico Pin |
| --- | --- |
| MCP3008 SCK | GP18 |
| MCP3008 MOSI | GP19 |
| MCP3008 MISO | GP16 |
| MCP3008 CS | GP17 |
| RGB red | GP13 |
| RGB green | GP14 |
| RGB blue | GP15 |

## Main Files

- `plant_diva_prod_notification.py` - production-style app with Wi-Fi, moisture readings, RGB LED status, and ntfy alerts.
- `moisture_rgb.py` - local moisture + RGB status loop.
- `moisture_code.py` - basic MCP3008 moisture reader.
- `moisture_warnings.py` - moisture threshold warnings in the serial console.
- `telnyx_sms_test.py` - test script for sending SMS through Telnyx.
- `test_red.py` - simple red LED test.

## Secrets

Do not commit `secrets.py`. Copy the example file and fill it in locally:

```python
SSID = "your-wifi-name"
PASSWORD = "your-wifi-password"

TELNYX_API_KEY = "KEY..."
TELNYX_FROM = "+15551234567"
TELNYX_TO = "+15557654321"
NTFY_TOPIC = "your-ntfy-topic"
```

## Running On The Pico

Copy the files to the Pico with your preferred MicroPython tool. To make the main app run on boot, copy or rename `plant_diva_prod_notification.py` to `main.py` on the Pico.

For one-off testing from a serial REPL:

```python
exec(open("plant_diva_prod_notification.py").read())
```

## Notes

The current moisture thresholds in `plant_diva_prod_notification.py` are:

- Dry: `>= 650`
- Getting thirsty: `> 615`
- Happy: `<= 615`

These may need calibration for the actual sensor, soil, and plant.

