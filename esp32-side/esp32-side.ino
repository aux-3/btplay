#include <Bluepad32.h>

ControllerPtr gamepad = nullptr;
ControllerPtr touchpad = nullptr;

struct GamepadState {
    uint16_t buttons;
    uint8_t dpad;
    uint8_t misc;

    int32_t lx;
    int32_t ly;
    int32_t rx;
    int32_t ry;

    int32_t l2;
    int32_t r2;
};

GamepadState lastGamepad;
bool haveLastGamepad = false;

int32_t applyDeadzone(int32_t value) {
    // تجاهل noise مال الـ analog sticks
    if (abs(value) <= 12) {
        return 0;
    }

    return value;
}

bool sameGamepadState(
    const GamepadState& a,
    const GamepadState& b
) {
    return
        a.buttons == b.buttons &&
        a.dpad == b.dpad &&
        a.misc == b.misc &&

        a.lx == b.lx &&
        a.ly == b.ly &&
        a.rx == b.rx &&
        a.ry == b.ry &&

        a.l2 == b.l2 &&
        a.r2 == b.r2;
}

void sendNeutralGamepad() {
    Serial.println(
        "G,0000,00,0,0,0,0,0,0,00"
    );
}

void sendNeutralTouchpad() {
    Serial.println(
        "M,0000,0,0,0"
    );
}

void onConnectedController(ControllerPtr ctl) {
    Serial.printf(
        "# connected index=%d\n",
        ctl->index()
    );

    // مع DS4 + Virtual Device:
    // index 0 = gamepad
    // index 1 = touchpad virtual mouse

    if (ctl->index() == 0) {
        gamepad = ctl;
        haveLastGamepad = false;

        Serial.println("# assigned GAMEPAD");
    }

    else if (ctl->index() == 1) {
        touchpad = ctl;

        Serial.println("# assigned TOUCHPAD");
    }
}

void onDisconnectedController(ControllerPtr ctl) {
    Serial.printf(
        "# disconnected index=%d\n",
        ctl->index()
    );

    if (gamepad == ctl) {
        sendNeutralGamepad();

        gamepad = nullptr;
        haveLastGamepad = false;
    }

    if (touchpad == ctl) {
        sendNeutralTouchpad();

        touchpad = nullptr;
    }
}

void processGamepad(ControllerPtr ctl) {
    GamepadState current;

    current.buttons = ctl->buttons();
    current.dpad = ctl->dpad();
    current.misc = ctl->miscButtons();

    current.lx = applyDeadzone(ctl->axisX());
    current.ly = applyDeadzone(ctl->axisY());

    current.rx = applyDeadzone(ctl->axisRX());
    current.ry = applyDeadzone(ctl->axisRY());

    current.l2 = ctl->brake();
    current.r2 = ctl->throttle();

    // هنا نتجاهل gyro / accelerometer:
    // إذا فقط gyro تغير، هذه القيم تبقى نفسها
    // وبالتالي ما نرسل packet جديد.

    if (
        haveLastGamepad &&
        sameGamepadState(current, lastGamepad)
    ) {
        return;
    }

    Serial.printf(
        "G,%04X,%02X,%ld,%ld,%ld,%ld,%ld,%ld,%02X\n",

        current.buttons,
        current.dpad,

        current.lx,
        current.ly,

        current.rx,
        current.ry,

        current.l2,
        current.r2,

        current.misc
    );

    lastGamepad = current;
    haveLastGamepad = true;
}

void processTouchpad(ControllerPtr ctl) {
    // الـ touchpad يمثل Mouse نسبي.
    // لازم نرسل كل report جديد، مو فقط لما تختلف القيمة،
    // لأن X/Y هنا حركة relative.

    Serial.printf(
        "M,%04X,%ld,%ld,%ld\n",

        ctl->buttons(),

        ctl->axisX(),
        ctl->axisY(),

        ctl->scrollWheel()
    );
}

void setup() {
    Serial.begin(115200);

    delay(1000);

    Serial.println("# ESP32 DS4 Bridge");
    Serial.println("# waiting for controller");

    BP32.enableVirtualDevice(true);

    BP32.setup(
        &onConnectedController,
        &onDisconnectedController
    );
}

void loop() {
    BP32.update();

    if (
        gamepad &&
        gamepad->isConnected() &&
        gamepad->hasData()
    ) {
        processGamepad(gamepad);
    }

    if (
        touchpad &&
        touchpad->isConnected() &&
        touchpad->hasData()
    ) {
        processTouchpad(touchpad);
    }

    delay(1);
}