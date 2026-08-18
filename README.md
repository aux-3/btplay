# ESP32 DS4 Bridge

This project turns an ESP32 into a small Bluetooth bridge for a DualShock 4
controller. The ESP32 talks to the controller with Bluepad32, sends clean serial
packets over USB, and the PC-side Python script turns those packets into Linux
virtual input devices.

The goal is simple: make a DS4-style controller device that Steam and Linux
games can understand, while keeping the ESP32 firmware small and easy to debug.

## How It Works

The input path is:

```text
DualShock 4 -> ESP32 over Bluetooth -> USB serial -> pc-side.py -> Linux evdev/uinput
```

The ESP32 sketch reads the controller state and prints two packet types:

- `G` packets for gamepad buttons, sticks, triggers, d-pad, and misc buttons.
- `M` packets for the DS4 touchpad, exposed as a small relative mouse device.

On the PC, `pc-side.py` reads those serial packets and creates:

- A virtual DS4-like gamepad named `Sony Interactive Entertainment Wireless Controller`.
- A virtual touchpad mouse named `ESP32 DS4 Touchpad`.

## Project Files

- `esp32-side/esp32-side.ino` is the main ESP32 firmware.
- `pc-side.py` is the Linux bridge that reads serial data and creates virtual input devices.
- `identify-btns/identify-btns.ino` is a helper sketch for checking raw button values.
- `btns-map.md` contains the captured button mapping notes.

## Requirements

### ESP32 Side

- An ESP32 board.
- Arduino IDE, Arduino CLI, or another ESP32-compatible build setup.
- Bluepad32 installed for the ESP32 environment.
- A DualShock 4 controller.

### PC Side

- Linux.
- Python 3.
- Access to `/dev/uinput`.
- Python packages:

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
6. Find the ESP32 serial port, usually something like `/dev/ttyUSB0` or `/dev/ttyACM0`.
7. Start the PC bridge:

```bash
python3 pc-side.py /dev/ttyUSB0
```

Use your actual serial port if it is different.

When it starts correctly, the script prints the virtual device paths and then
keeps running while it forwards controller input.

## Button And Axis Notes

The mappings in `pc-side.py` are intentional. Some of the Linux button codes may
look unusual at first glance because Steam applies its own DS4 mapping based on
raw button indexes and axis order.

The script arranges axes so Steam sees them roughly like this:

```text
a0 = Left X
a1 = Left Y
a2 = Right X
a3 = L2
a4 = R2
a5 = Right Y
```

Triggers are handled as both analog axes and digital button presses. The digital
press is generated when the analog trigger value crosses the configured
threshold in `pc-side.py`.

The touchpad is handled separately from the main gamepad. It becomes a relative
mouse device with left click, X/Y motion, and scroll wheel support.

## Identifying Buttons

If a button does not map the way you expect, flash
`identify-btns/identify-btns.ino` instead of the main sketch. Open the serial
monitor, press buttons on the controller, and compare the raw values with
`btns-map.md`.

After updating the map in `pc-side.py`, flash `esp32-side/esp32-side.ino` again
and restart the Python bridge.

## Troubleshooting

If the Python script cannot open the serial port, check that the port path is
correct and that your user has permission to access it.

If the script fails while creating virtual input devices, check `/dev/uinput`
permissions. Running with `sudo` is the quickest test:

```bash
sudo python3 pc-side.py /dev/ttyUSB0
```

If Steam sees the wrong buttons or axes, keep the existing comments in
`pc-side.py` in mind. Some mappings are deliberately shifted to match what Steam
expects from a DS4-like Linux input device.

If the controller connects but input feels noisy, the ESP32 sketch already
applies a small analog stick deadzone. You can adjust `applyDeadzone()` in
`esp32-side/esp32-side.ino` if your controller needs more or less filtering.

## Notes

This project is currently Linux-focused because it depends on `evdev` and
`uinput` on the PC side.

Note: this project was vibecoded.
