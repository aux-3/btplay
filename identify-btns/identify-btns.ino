#include <Bluepad32.h>

ControllerPtr gamepad = nullptr;
ControllerPtr touchpad = nullptr;

uint16_t lastButtons = 0;
uint8_t lastDpad = 0;
uint8_t lastMisc = 0;

int32_t lastLX = 0;
int32_t lastLY = 0;
int32_t lastRX = 0;
int32_t lastRY = 0;

int32_t lastL2 = 0;
int32_t lastR2 = 0;

void onConnectedController(ControllerPtr ctl) {
    Serial.println("=================================");
    Serial.println("Device connected");

    Serial.printf("Index: %d\n", ctl->index());

    // DS4 + Virtual Device:
    // index 0 = gamepad
    // index 1 = touchpad virtual mouse

    if (ctl->index() == 0) {
        gamepad = ctl;

        Serial.println("Assigned as GAMEPAD");

        ControllerProperties properties = ctl->getProperties();

        Serial.printf(
            "VID: 0x%04x | PID: 0x%04x\n",
            properties.vendor_id,
            properties.product_id
        );
    }

    else if (ctl->index() == 1) {
        touchpad = ctl;

        Serial.println("Assigned as TOUCHPAD");
    }

    Serial.println("=================================");
}

void onDisconnectedController(ControllerPtr ctl) {

    Serial.printf(
        "Device disconnected: index=%d\n",
        ctl->index()
    );

    if (gamepad == ctl) {
        gamepad = nullptr;
    }

    if (touchpad == ctl) {
        touchpad = nullptr;
    }
}

void printGamepadData(ControllerPtr ctl) {

    uint16_t buttons = ctl->buttons();
    uint8_t dpad = ctl->dpad();
    uint8_t misc = ctl->miscButtons();

    int32_t lx = ctl->axisX();
    int32_t ly = ctl->axisY();

    int32_t rx = ctl->axisRX();
    int32_t ry = ctl->axisRY();

    int32_t l2 = ctl->brake();
    int32_t r2 = ctl->throttle();

    bool changed =
        buttons != lastButtons ||
        dpad != lastDpad ||
        misc != lastMisc ||

        abs(lx - lastLX) > 10 ||
        abs(ly - lastLY) > 10 ||
        abs(rx - lastRX) > 10 ||
        abs(ry - lastRY) > 10 ||

        l2 != lastL2 ||
        r2 != lastR2;

    if (!changed) {
        return;
    }

    Serial.printf(
        "[GAMEPAD] "
        "buttons=0x%04x "
        "dpad=0x%02x "
        "LX=%4d LY=%4d "
        "RX=%4d RY=%4d "
        "L2=%4d R2=%4d "
        "misc=0x%02x\n",

        buttons,
        dpad,
        lx,
        ly,
        rx,
        ry,
        l2,
        r2,
        misc
    );

    lastButtons = buttons;
    lastDpad = dpad;
    lastMisc = misc;

    lastLX = lx;
    lastLY = ly;
    lastRX = rx;
    lastRY = ry;

    lastL2 = l2;
    lastR2 = r2;
}

void printTouchpadData(ControllerPtr ctl) {

    Serial.printf(
        "[TOUCHPAD] "
        "buttons=0x%04x "
        "X=%d "
        "Y=%d "
        "wheel=%d\n",

        ctl->buttons(),
        ctl->axisX(),
        ctl->axisY(),
        ctl->scrollWheel()
    );
}

void setup() {

    Serial.begin(115200);
    delay(1000);

    Serial.println();
    Serial.println("ESP32 Controller Receiver");
    Serial.println("Waiting for Bluetooth controller...");

    BP32.enableVirtualDevice(true);

    BP32.setup(
        &onConnectedController,
        &onDisconnectedController
    );
}

void loop() {

    bool updated = BP32.update();

    if (!updated) {
        delay(5);
        return;
    }

    if (
        gamepad &&
        gamepad->isConnected()
    ) {
        printGamepadData(gamepad);
    }

    if (
        touchpad &&
        touchpad->isConnected()
    ) {
        printTouchpadData(touchpad);
    }

    delay(5);
}