# This file is executed on every boot.

# Import necessary modules
import network, webrepl

# Setup AP
def ap_setup():
    ap=network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid="ESP32_FLOAT")

# Setup Network Connection
def net_setup():
    net=network.WLAN(network.STA_IF)
    net.active(True)
    net.connect("SSID", "PASSWORD")

# WebREPL
def webrepl_setup():
    webrepl.start()

# Select Modes
ap_setup()
# net_setup()
# webrepl_setup()