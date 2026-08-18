#!/usr/bin/env python3

import sys

import serial
from serial import SerialException

from evdev import (
    UInput,
    AbsInfo,
    ecodes as e,
)


# ==================================================
# General configuration
# ==================================================

BAUD_RATE = 115200

DS4_NAME = "Sony Interactive Entertainment Wireless Controller"

DS4_VENDOR_ID = 0x054C
DS4_PRODUCT_ID = 0x09CC
DS4_VERSION = 0x0100

TOUCHPAD_NAME = "ESP32 DS4 Touchpad"

TRIGGER_BUTTON_THRESHOLD = 30


if len(sys.argv) != 2:
    print(
        f"Usage: {sys.argv[0]} /dev/ttyUSB0"
    )
    sys.exit(1)


SERIAL_PORT = sys.argv[1]


# ==================================================
# BUTTON MAPPING
# ==================================================
#
# هذا أهم Dict إذا تريد تغير ترتيب الأزرار.
#
# source:
#   buttons = buttons field القادم من ESP32
#   misc    = miscButtons
#   trigger = analog trigger + digital mask
#
# code:
#   الزر الذي نرسله إلى Linux.
#
# ملاحظة:
# الأكواد هنا تبدو غريبة لأن Steam يطبق DS4 mapping
# على ترتيب button indexes.
#
# Steam DS4 mapping المتوقع تقريباً:
#
# b0  = Square
# b1  = Cross
# b2  = Circle
# b3  = Triangle
#
# b4  = L1
# b5  = R1
#
# b8  = Share
# b9  = Options
#
# b10 = L3
# b11 = R3
# b12 = PS
#
# ==================================================

BUTTON_MAP = {

    # ------------------------------------------------
    # Face buttons
    # ------------------------------------------------

    "CROSS": {
        "source": "buttons",
        "mask": 0x0001,
        "code": e.BTN_EAST,
    },

    "CIRCLE": {
        "source": "buttons",
        "mask": 0x0002,
        "code": e.BTN_NORTH,
    },

    "SQUARE": {
        "source": "buttons",
        "mask": 0x0004,
        "code": e.BTN_SOUTH,
    },

    "TRIANGLE": {
        "source": "buttons",
        "mask": 0x0008,
        "code": e.BTN_WEST,
    },


    # ------------------------------------------------
    # Shoulder buttons
    # ------------------------------------------------

    "L1": {
        "source": "buttons",
        "mask": 0x0010,
        "code": e.BTN_TL,
    },

    "R1": {
        "source": "buttons",
        "mask": 0x0020,
        "code": e.BTN_TR,
    },


    # ------------------------------------------------
    # Triggers
    # ------------------------------------------------

    "L2": {
        "source": "trigger",
        "trigger": "L2",
        "mask": 0x0040,
        "code": e.BTN_TL2,
    },

    "R2": {
        "source": "trigger",
        "trigger": "R2",
        "mask": 0x0080,
        "code": e.BTN_TR2,
    },


    # ------------------------------------------------
    # Stick buttons
    # ------------------------------------------------

    # Steam expects L3 at raw button index b10.
    "L3": {
        "source": "buttons",
        "mask": 0x0100,

        # Intentionally BTN_MODE.
        "code": e.BTN_MODE,
    },

    # Steam expects R3 at b11.
    "R3": {
        "source": "buttons",
        "mask": 0x0200,

        # Intentionally BTN_THUMBL.
        "code": e.BTN_THUMBL,
    },


    # ------------------------------------------------
    # Misc buttons
    # ------------------------------------------------

    # PS needs raw b12.
    "PS": {
        "source": "misc",
        "mask": 0x01,

        # Intentionally BTN_THUMBR.
        "code": e.BTN_THUMBR,
    },

    "SHARE": {
        "source": "misc",
        "mask": 0x02,
        "code": e.BTN_SELECT,
    },

    "OPTIONS": {
        "source": "misc",
        "mask": 0x04,
        "code": e.BTN_START,
    },
}


# ==================================================
# AXIS MAPPING
# ==================================================
#
# هذا الـ Dict الثاني المهم.
#
# المشكلة القديمة كانت:
#
# RX -> ABS_RX -> Steam اعتبره Left Trigger
# RY -> ABS_RY -> Steam اعتبره Right Trigger
# R2 -> ABS_RZ -> Steam اعتبره Right Stick
#
# DS4 mapping الذي يستخدمه Steam يتوقع:
#
# a0 = Left X
# a1 = Left Y
# a2 = Right X
# a3 = L2
# a4 = R2
# a5 = Right Y
#
# Linux joydev يرتب ABS axes حسب رقم ABS code.
# لذلك نرتبها هكذا عمداً.
#
# ==================================================

AXIS_MAP = {

    "LX": {
        "code": e.ABS_X,
        "type": "stick",
    },

    "LY": {
        "code": e.ABS_Y,
        "type": "stick",
    },

    # a2
    "RX": {
        "code": e.ABS_Z,
        "type": "stick",
    },

    # a5
    "RY": {
        "code": e.ABS_RZ,
        "type": "stick",
    },

    # a3
    "L2": {
        "code": e.ABS_RX,
        "type": "trigger",
    },

    # a4
    "R2": {
        "code": e.ABS_RY,
        "type": "trigger",
    },
}


# ==================================================
# D-pad mapping
# ==================================================

DPAD_MAP = {
    "UP": 0x01,
    "DOWN": 0x02,
    "RIGHT": 0x04,
    "LEFT": 0x08,
}


# ==================================================
# Build UInput capabilities automatically
# ==================================================

button_codes = []

for config in BUTTON_MAP.values():
    code = config["code"]

    if code not in button_codes:
        button_codes.append(code)


axis_capabilities = []

for axis_name, config in AXIS_MAP.items():

    code = config["code"]

    if config["type"] == "stick":

        axis_capabilities.append(
            (
                code,
                AbsInfo(
                    value=128,
                    min=0,
                    max=255,
                    fuzz=0,
                    flat=0,
                    resolution=0,
                ),
            )
        )

    else:

        axis_capabilities.append(
            (
                code,
                AbsInfo(
                    value=0,
                    min=0,
                    max=255,
                    fuzz=0,
                    flat=0,
                    resolution=0,
                ),
            )
        )


# Add D-pad axes
axis_capabilities.extend(
    [
        (
            e.ABS_HAT0X,
            AbsInfo(
                0,
                -1,
                1,
                0,
                0,
                0,
            ),
        ),

        (
            e.ABS_HAT0Y,
            AbsInfo(
                0,
                -1,
                1,
                0,
                0,
                0,
            ),
        ),
    ]
)


gamepad_capabilities = {

    e.EV_KEY: button_codes,

    e.EV_ABS: axis_capabilities,
}


# ==================================================
# Touchpad capabilities
# ==================================================

mouse_capabilities = {

    e.EV_KEY: [
        e.BTN_LEFT,
    ],

    e.EV_REL: [
        e.REL_X,
        e.REL_Y,
        e.REL_WHEEL,
    ],
}


# ==================================================
# Scaling
# ==================================================

def scale_stick(value: int) -> int:

    value = max(
        -511,
        min(512, value),
    )

    if value >= 0:

        return 128 + round(
            value * 127 / 512
        )

    return 128 + round(
        value * 128 / 511
    )


def scale_trigger(value: int) -> int:

    value = max(
        0,
        min(1023, value),
    )

    return round(
        value * 255 / 1023
    )


# ==================================================
# Button state helper
# ==================================================

def get_button_state(
    config,
    buttons,
    misc,
    l2,
    r2,
):

    source = config["source"]


    if source == "buttons":

        return bool(
            buttons & config["mask"]
        )


    if source == "misc":

        return bool(
            misc & config["mask"]
        )


    if source == "trigger":

        trigger_name = config["trigger"]

        if trigger_name == "L2":
            analog_value = l2

        else:
            analog_value = r2


        digital_pressed = bool(
            buttons & config["mask"]
        )

        analog_pressed = (
            analog_value >
            TRIGGER_BUTTON_THRESHOLD
        )

        return (
            digital_pressed
            or analog_pressed
        )


    return False


# ==================================================
# Gamepad handler
# ==================================================

def handle_gamepad(
    parts,
    gamepad,
):

    if len(parts) != 10:
        return


    buttons = int(
        parts[1],
        16,
    )

    dpad = int(
        parts[2],
        16,
    )


    lx = int(parts[3])
    ly = int(parts[4])

    rx = int(parts[5])
    ry = int(parts[6])

    l2 = int(parts[7])
    r2 = int(parts[8])


    misc = int(
        parts[9],
        16,
    )


    # ==================================================
    # Buttons
    # ==================================================

    for name, config in BUTTON_MAP.items():

        pressed = get_button_state(
            config,
            buttons,
            misc,
            l2,
            r2,
        )

        gamepad.write(
            e.EV_KEY,
            config["code"],
            int(pressed),
        )


    # ==================================================
    # Axes
    # ==================================================

    axis_values = {

        "LX": lx,
        "LY": ly,

        "RX": rx,
        "RY": ry,

        "L2": l2,
        "R2": r2,
    }


    for name, config in AXIS_MAP.items():

        value = axis_values[name]


        if config["type"] == "stick":

            output_value = scale_stick(
                value
            )

        else:

            output_value = scale_trigger(
                value
            )


        gamepad.write(
            e.EV_ABS,
            config["code"],
            output_value,
        )


    # ==================================================
    # D-pad
    # ==================================================

    hat_x = 0
    hat_y = 0


    if dpad & DPAD_MAP["RIGHT"]:
        hat_x += 1

    if dpad & DPAD_MAP["LEFT"]:
        hat_x -= 1


    if dpad & DPAD_MAP["DOWN"]:
        hat_y += 1

    if dpad & DPAD_MAP["UP"]:
        hat_y -= 1


    gamepad.write(
        e.EV_ABS,
        e.ABS_HAT0X,
        hat_x,
    )

    gamepad.write(
        e.EV_ABS,
        e.ABS_HAT0Y,
        hat_y,
    )


    gamepad.syn()


# ==================================================
# Touchpad handler
# ==================================================

def handle_mouse(
    parts,
    mouse,
):

    if len(parts) != 5:
        return


    buttons = int(
        parts[1],
        16,
    )


    x = int(parts[2])
    y = int(parts[3])

    wheel = int(parts[4])


    # Touchpad click
    mouse.write(
        e.EV_KEY,
        e.BTN_LEFT,
        1 if buttons & 0x0001 else 0,
    )


    if x:

        mouse.write(
            e.EV_REL,
            e.REL_X,
            x,
        )


    if y:

        mouse.write(
            e.EV_REL,
            e.REL_Y,
            y,
        )


    if wheel:

        mouse.write(
            e.EV_REL,
            e.REL_WHEEL,
            wheel,
        )


    mouse.syn()


# ==================================================
# Main
# ==================================================

def main():

    gamepad = None
    mouse = None


    try:

        # ==================================================
        # Virtual DS4
        # ==================================================

        gamepad = UInput(

            gamepad_capabilities,

            name=DS4_NAME,

            vendor=DS4_VENDOR_ID,
            product=DS4_PRODUCT_ID,
            version=DS4_VERSION,

            bustype=e.BUS_USB,
        )


        # ==================================================
        # Virtual touchpad
        # ==================================================

        mouse = UInput(

            mouse_capabilities,

            name=TOUCHPAD_NAME,

            vendor=0x1209,
            product=0x0002,
            version=0x0001,

            bustype=e.BUS_USB,
        )


        print(
            f"Virtual DS4:      {gamepad.device.path}"
        )

        print(
            f"Virtual touchpad: {mouse.device.path}"
        )

        print(
            f"Serial port:      {SERIAL_PORT}"
        )


        # ==================================================
        # Serial
        # ==================================================

        with serial.Serial(

            SERIAL_PORT,

            BAUD_RATE,

            timeout=1,

        ) as ser:


            ser.reset_input_buffer()


            print(
                "Bridge running"
            )


            while True:

                raw = ser.readline()


                if not raw:
                    continue


                line = raw.decode(
                    "utf-8",
                    errors="ignore",
                ).strip()


                if not line:
                    continue


                # ESP32 debug
                if line.startswith("#"):

                    print(line)

                    continue


                parts = line.split(",")


                try:

                    if parts[0] == "G":

                        handle_gamepad(
                            parts,
                            gamepad,
                        )


                    elif parts[0] == "M":

                        handle_mouse(
                            parts,
                            mouse,
                        )


                    else:

                        print(
                            f"Unknown packet: {line}"
                        )


                except (
                    ValueError,
                    IndexError,
                ):

                    print(
                        f"Bad packet: {line}"
                    )


    except KeyboardInterrupt:

        print()
        print(
            "Bridge stopped."
        )


    except SerialException as exc:

        print(
            f"Serial error: {exc}"
        )

        sys.exit(1)


    finally:

        if mouse is not None:
            mouse.close()

        if gamepad is not None:
            gamepad.close()


if __name__ == "__main__":
    main()