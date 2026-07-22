from machine import Pin
from time import sleep

RED_PIN = 13

red = Pin(RED_PIN, Pin.OUT)
red.value(1)

print("Red LED on GP13 is ON.")

while True:
    sleep(1)

