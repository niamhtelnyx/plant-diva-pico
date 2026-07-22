from machine import Pin
red = Pin(13, Pin.OUT)

while True:
    red.value(1)
