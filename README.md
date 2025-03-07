# GEARS Squid Software

This software is intended for use on the ESP32-WROOM-32 board in the GEARS, Inc. Squid float. Currently, **all rights are reserved** by Jacob Shaffer (jacobot1), except rights to `ads1x15.py`, which is MIT-licensed by Radomir Dopieralski.

## Setup

First, ensure you have the correct serial drivers for connecting to the ESP32. If you have never connected your computer to the ESP32 over serial, install [this driver](https://www.silabs.com/developer-tools/usb-to-uart-bridge-vcp-drivers?tab=downloads) from Silicon Labs. Download the one labled "CP210x VCP Windows"

Once you have the driver, ensure you have Python installed. You can get the latest version [here](https://www.python.org/downloads/). Make sure to check `Add Python to PATH` during installation.

Next, flash MicroPython firmware to the ESP32 if it is not already installed.  You can do this with `esptool.py`.
If you don't have it:

```
py -m pip install esptool
```

You can get the latest version of MicroPython for ESP32 [here](https://micropython.org/download/ESP32_GENERIC/).
Before installing MicroPython, you'll need to connect to the ESP32 and erase its flash:

```
esptool --chip esp32 --port YOUR_COMPORT erase_flash
```

If you don't know what COM port the ESP32 is connected to and you're on a Windows machine, you can find it in Device Manager under `Ports (COM & LPT)`.

Finally, install the firmware:

```powershell
esptool --chip esp32 --port YOUR_COMPORT --baud 460800 write_flash -z 0x1000 YOUR_FIRMWARE.bin
```

Once you've got the firmware installed, you'll need to upload this software to the ESP32. Go ahead and clone this repository if you haven't already:

```powershell
git clone https://github.com/jacobot1/GEARS-Squid.git
```

I prefer to upload the files with Thonny Python IDE. If you don't have it, you can install it with:

```powershell
py -m pip install thonny
```

Once you've got Thonny installed, open it up. You can actually open it by just sending `thonny` to a terminal prompt. Under the `Run` tab, click `Configure Interpreter...`. Under `What type of interpreter should Thonny use for running your code?`, select `MicroPython (ESP32)` and click `OK`. If the ESP32 is connected, Thonny should detect it and connect automatically. A section should open in the sidebar showing the ESP32's internal filesystem. In the file browser above it, navigate to the folder in which you cloned this repository. Then, for each file in the folder (besides `README.md` and `.git` of course), right-click on it and click `Upload to /`.

## Usage

Once you have everything set up, reboot MicroPython by either powercycling the ESP32 or by sending a Ctrl-D to the MicroPython REPL (which is available underneath the editor in Thonny). The Squid float should immediately perform a motor test and generate an HTML webpage with an initial transmission. You can view this page by connecting to the ESP32's access point, `ESP32_FLOAT`, and opening `http://192.168.4.1` in a web browser (I prefer Firefox as it seems to load the fastest, but any browser should theoretically work). Squid will descend after approximately 45 seconds. Squid should be done recording after 80 seconds have passed and should begin returning after only 46 seconds. If Squid does not return in that time frame, Squid has most likely experienced a water ingress that changed its bouyancy and will need manual recovery. Once Squid has finished recording, it should post its findings on the same webpage it generated earlier. You will need to reconnect to `ESP32_FLOAT` and refresh the webpage in your browser as 2.4GHz Wi-Fi radio waves don't travel through water and the connection will have been lost. You may need to refresh the webpage multiple times to receive the new data. Squid will complete 2 more profiles and should keep its webpage available indefinitely as long as power is connected.

## Extras

The script `boot.py` includes optional functionality for running the MicroPython WebREPL for debugging or adjusting the software wirelessly. Uncomment `webrepl_setup()` at the end of the file to enable it. It will be available after reboot. To connect to the WebREPL, you will need to download the client software from the [MicroPython repository](https://github.com/micropython/webrepl). Connection instrcutions are available there.

To edit files directly on the ESP32, you can use a text editor such as `pye` by robert-hh, available [here](https://github.com/robert-hh/Micropython-Editor).

## Troubleshooting

If you are having trouble connecting to your computer to the ESP32, make sure the Silicon Labs driver mentioned earlier is installed.

If you are having trouble viewing the webpage, make sure you are still connected to `ESP32-FLOAT` and try opening the page in Firefox.

If Squid has not begun returning from the bottom after about 46 seconds, it probably experienced water ingress and needs to be manually recovered. However, it is also possible that the syringe mechanism that changes Squid's buoyancy has broken, in which case it would also need to be manually recovered.

If you have any software OR hardware-related issues, contact me and I will be glad to help.
