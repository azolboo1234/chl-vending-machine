from microbit import *
import utime

# Minimal Micro:bit Web Serial demo for the candy vending machine.
# Load this .py file directly in the Micro:bit Python Editor (no GitHub link needed).
# Copy it from the Raw view so the editor does not wrap or alter characters.

SERVO_PIN_1 = pin1  # Hummingbird positional servo on slot 1
SERVO_PIN_2 = pin2  # Hummingbird positional servo on slot 2
SENSOR_PIN_1 = pin0  # Ultrasonic sensor on sensor slot 1
SENSOR_PIN_2 = pin8  # Ultrasonic sensor on sensor slot 2
SENSOR_PIN_3 = pin3  # Rotary dial on sensor slot 3
SERVO_PERIOD_US = 20000  # 50 Hz pulses

# Hummingbird Bit servos expect roughly 0.6–2.4 ms pulses for 0–180 degrees.
SERVO_PULSE_MIN = 600
SERVO_PULSE_MAX = 2400
DIAL_LOW = 400
DIAL_HIGH = 600

# Adaptive ultrasonic detection
SENSOR_TRIGGER_DELTA = 120  # Change needed from baseline to count as a hit
SENSOR_RESET_DELTA = 70  # Change needed to fall back to idle
BASELINE_BLEND = 0.9  # Exponential moving average for smoothing

ANGLE_SETTLE_MS = 700

last_dial = None
baseline_1 = None
baseline_2 = None
armed_1 = False
armed_2 = False


def _pulse_servo(pin, pulse_us, cycles):
    # Manually bit-bang servo pulses to keep timing precise on the Hummingbird
    # board. This avoids PWM drift that can happen with analog writes.
    gap = SERVO_PERIOD_US - pulse_us
    for _ in range(cycles):
        pin.write_digital(1)
        utime.sleep_us(pulse_us)
        pin.write_digital(0)
        utime.sleep_us(gap)


def _angle_to_pulse(angle):
    if angle < 0:
        angle = 0
    if angle > 180:
        angle = 180
    span = SERVO_PULSE_MAX - SERVO_PULSE_MIN
    return SERVO_PULSE_MIN + (span * angle) // 180


def read_sensor_value(pin):
    try:
        return pin.read_analog()
    except Exception:
        try:
            return pin.read_digital() * 1023
        except Exception:
            return 0


def update_baseline(current, baseline):
    if baseline is None:
        return current
    return int((baseline * BASELINE_BLEND) + (current * (1 - BASELINE_BLEND)))


def sensor_triggered(value, baseline, armed):
    if baseline is None:
        return False, armed
    delta = value - baseline
    magnitude = delta if delta >= 0 else -delta
    if not armed and magnitude >= SENSOR_TRIGGER_DELTA:
        return True, True
    if armed and magnitude <= SENSOR_RESET_DELTA:
        return False, False
    return False, armed


def move_servo_to(pin, angle, hold_ms=ANGLE_SETTLE_MS):
    pulse = _angle_to_pulse(angle)
    cycles = hold_ms // 20
    if cycles < 1:
        cycles = 1
    _pulse_servo(pin, pulse, cycles)


def home_servos():
    move_servo_to(SERVO_PIN_1, 0)
    move_servo_to(SERVO_PIN_2, 0)
    uart.write("SERVO:ZERO\n")


def handle_payout(kind):
    if kind == "KITKAT":
        display.show("K")
        move_servo_to(SERVO_PIN_1, 90)
        move_servo_to(SERVO_PIN_1, 0)
        uart.write("PAYOUT:KITKAT\n")
    elif kind == "JOLLY":
        display.show("J")
        move_servo_to(SERVO_PIN_2, 90)
        move_servo_to(SERVO_PIN_2, 0)
        uart.write("PAYOUT:JOLLY\n")
    else:
        display.show(Image.NO)
        home_servos()
        uart.write("PAYOUT:NONE\n")


# Ensure the servos start at 0 degrees so positional pulls are consistent.
home_servos()


uart.init(baudrate=115200)
uart.write("READY\n")

while True:
    val_1 = read_sensor_value(SENSOR_PIN_1)
    val_2 = read_sensor_value(SENSOR_PIN_2)

    baseline_1 = update_baseline(val_1, baseline_1)
    baseline_2 = update_baseline(val_2, baseline_2)

    triggered_1, armed_1 = sensor_triggered(val_1, baseline_1, armed_1)
    triggered_2, armed_2 = sensor_triggered(val_2, baseline_2, armed_2)

    dial_value = 0
    try:
        dial_value = SENSOR_PIN_3.read_analog()
    except Exception:
        dial_value = 0

    if triggered_1:
        display.show("1")
        uart.write("ULTRA1\n")
        uart.write("ULTRA1:VAL=" + str(val_1) + "\n")
    if triggered_2:
        display.show("2")
        uart.write("ULTRA2\n")
        uart.write("ULTRA2:VAL=" + str(val_2) + "\n")

    if dial_value < DIAL_LOW:
        if last_dial != "KITKAT":
            uart.write("DIAL:KITKAT\n")
        last_dial = "KITKAT"
    elif dial_value > DIAL_HIGH:
        if last_dial != "JOLLY":
            uart.write("DIAL:JOLLY\n")
        last_dial = "JOLLY"

    if button_a.was_pressed():
        uart.write("BTN:A\n")
    if button_b.was_pressed():
        uart.write("BTN:B\n")

    incoming = uart.readline()
    if incoming:
        try:
            cmd = str(incoming, "utf-8")
        except Exception:
            cmd = ""
        cmd = cmd.strip().upper()

        if cmd == "LED ON":
            display.show(Image.HEART)
            uart.write("LED:ON\n")
        elif cmd == "LED OFF":
            display.clear()
            uart.write("LED:OFF\n")
        elif cmd == "PAYOUT KITKAT":
            handle_payout("KITKAT")
        elif cmd == "PAYOUT JOLLY":
            handle_payout("JOLLY")
        elif cmd == "PAYOUT NONE":
            handle_payout("NONE")
        elif cmd == "SERVO ZERO":
            home_servos()
        elif cmd.startswith("SERVO 1 "):
            try:
                angle = int(cmd.split(" ")[-1])
            except Exception:
                angle = 0
            move_servo_to(SERVO_PIN_1, angle)
            uart.write("SERVO1:" + str(angle) + "\n")
        elif cmd.startswith("SERVO 2 "):
            try:
                angle = int(cmd.split(" ")[-1])
            except Exception:
                angle = 0
            move_servo_to(SERVO_PIN_2, angle)
            uart.write("SERVO2:" + str(angle) + "\n")
        elif cmd == "SENSOR?":
            uart.write("LIGHT:" + str(display.read_light_level()) + "\n")
        elif cmd:
            uart.write("ERR:UNKNOWN:" + cmd + "\n")

    sleep(10)
