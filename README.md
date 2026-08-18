<h1 align="center">ESP32 DS4 Bridge</h1>

<p align="center">
  <img alt="ESP32" src="https://img.shields.io/badge/ESP32-Bluetooth%20Bridge-E7352C">
  <img alt="Arduino" src="https://img.shields.io/badge/Arduino-Compatible-00979D">
  <img alt="Bluepad32" src="https://img.shields.io/badge/Bluepad32-Controller%20Input-2563EB">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.x-3776AB">
  <img alt="Linux" src="https://img.shields.io/badge/Linux-evdev%20%2F%20uinput-FCC624">
</p>

<p align="center">
  A lightweight ESP32-to-Linux bridge for using a DualShock 4 as a virtual
  DS4-style controller.
</p>

---

This project turns an ESP32 into a small Bluetooth bridge for a DualShock 4.
The ESP32 talks to the controller with Bluepad32, sends clean serial packets
over USB, and the PC-side Python script turns those packets into Linux virtual
input devices.

The goal is simple: make a DS4-style controller that Steam and Linux games can
understand, while keeping the ESP32 firmware small and easy to debug.

## How It Works

```text
DualShock 4 -> ESP32 over Bluetooth -> USB serial -> pc-side.py -> Linux evdev/uinput
```

The ESP32 sketch reads the controller state and prints compact serial packets.
On Linux, `pc-side.py` reads those packets and creates virtual input devices.

| Packet | Purpose |
| --- | --- |
| `G` | Gamepad buttons, sticks, triggers, d-pad, and misc buttons |
| `M` | DS4 touchpad input as a relative mouse |

| Virtual device | Name |
| --- | --- |
| Gamepad | `Sony Interactive Entertainment Wireless Controller` |
| Touchpad mouse | `ESP32 DS4 Touchpad` |

## Project Files

| Path | Description |
| --- | --- |
| `esp32-side/esp32-side.ino` | Main ESP32 firmware |
| `pc-side.py` | Linux serial-to-evdev bridge |
| `identify-btns/identify-btns.ino` | Helper sketch for checking raw button values |
| `btns-map.md` | Captured button mapping notes |

## Requirements

| Side | Requirements |
| --- | --- |
| ESP32 | ESP32 board, Arduino-compatible build setup, Bluepad32, DualShock 4 |
| PC | Linux, Python 3, `/dev/uinput` access, serial access |

```bash
python3 -m pip install pyserial evdev
```

Depending on your system permissions, you may need to run the bridge with
`sudo`, or configure udev/user permissions for serial and uinput access.

## Setup

1. Open `esp32-side/esp32-side.ino` in your ESP32 build environment.
2. Make sure Bluepad32 is installed and available.
3. Flash the sketch to the ESP32.
4. Connect the ESP32 to the PC over USB.
5. Pair or connect the DualShock 4 to the ESP32.
6. Find the ESP32 serial port, usually `/dev/ttyUSB0` or `/dev/ttyACM0`.
7. Start the PC bridge.

```bash
python3 pc-side.py /dev/ttyUSB0
```

Use your actual serial port if it is different.

When it starts correctly, the script prints the virtual device paths and then
keeps running while it forwards controller input.

## Mapping Notes

The mappings in `pc-side.py` are intentional. Some of the Linux button codes may
look unusual at first glance because Steam applies its own DS4 mapping based on
raw button indexes and axis order.

The script arranges axes so Steam sees them roughly like this.

```text
a0 = Left X
a1 = Left Y
a2 = Right X
a3 = L2
a4 = R2
a5 = Right Y
```

| Input | Handling |
| --- | --- |
| L2/R2 | Analog axes plus digital button presses using a threshold |
| D-pad | Converted to `ABS_HAT0X` and `ABS_HAT0Y` |
| Touchpad | Separate relative mouse with click, X/Y motion, and scroll |

## Identifying Buttons

If a button does not map the way you expect, flash
`identify-btns/identify-btns.ino` instead of the main sketch. Open the serial
monitor, press buttons on the controller, and compare the raw values with
`btns-map.md`.

After updating the map in `pc-side.py`, flash `esp32-side/esp32-side.ino` again
and restart the Python bridge.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Serial port will not open | Confirm the path and user permissions |
| Virtual device creation fails | Check `/dev/uinput` permissions |
| Steam sees wrong buttons or axes | Keep the intentional DS4/Steam mapping comments in `pc-side.py` in mind |
| Input feels noisy | Adjust `applyDeadzone()` in `esp32-side/esp32-side.ino` |

Running with `sudo` is the quickest way to test whether the issue is a
permissions problem.

```bash
sudo python3 pc-side.py /dev/ttyUSB0
```

## Notes

This project is currently Linux-focused because it depends on `evdev` and
`uinput` on the PC side.

Note: this project was vibecoded.
