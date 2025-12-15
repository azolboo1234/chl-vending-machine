from microbit import *
import utime

# Minimal Micro:bit Web Serial demo for the candy vending machine.
# Load this .py file directly in the Micro:bit Python Editor (no GitHub link needed).
# Copy it from the Raw view so the editor does not wrap or alter characters.

SERVO_PIN_1 = pin1  # Hummingbird positional servo on servo slot 1
SERVO_PIN_2 = pin2  # Hummingbird positional servo on servo slot 2
SENSOR_PIN_1 = pin0  # Motion sensor on sensor slot 1 (3-wire analog/digital)
SENSOR_PIN_2 = pin8  # Motion sensor on sensor slot 2 (3-wire analog/digital)
SENSOR_PIN_3 = pin3  # Rotary dial on sensor slot 3 (potentiometer)
SERVO_PERIOD_US = 20000  # 50 Hz pulses

# Hummingbird Bit servos expect roughly 0.6–2.4 ms pulses for 0–180 degrees.
SERVO_PULSE_MIN = 600
SERVO_PULSE_MAX = 2400

# Rotary dial outputs a 0–100 range (0 = far counterclockwise, 100 = far
# clockwise). Treat below 35 as KitKat and above 65 as Jolly Rancher.
DIAL_LEFT = 35
DIAL_RIGHT = 65

CALIBRATION_SAMPLES = 24
CALIBRATION_DELAY_MS = 10

# Adaptive motion detection tuned for the Hummingbird distance sensors. These
# modules spike high on movement and slowly settle. We watch for a fast rise
# above baseline, then re-arm once the reading drops back toward baseline.
SENSOR_TRIGGER_DELTA = 30  # Change needed from baseline to count as motion
SENSOR_RESET_DELTA = 10  # Change needed to consider the motion cleared
BASELINE_BLEND = 0.9  # Exponential moving average for smoothing

ANGLE_SETTLE_MS = 700

last_dial = None
baseline_1 = None
baseline_2 = None
armed_1 = False
armed_2 = False
armed_since_1 = None
armed_since_2 = None
incoming_buffer = ""


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


def calibrate_motion_baseline():
    global baseline_1, baseline_2, armed_1, armed_2
    total_1 = 0
    total_2 = 0
    count = 0
    for _ in range(CALIBRATION_SAMPLES):
        total_1 += read_sensor_value(SENSOR_PIN_1)
        total_2 += read_sensor_value(SENSOR_PIN_2)
        count += 1
        utime.sleep_ms(CALIBRATION_DELAY_MS)

    if count == 0:
        baseline_1 = 0
        baseline_2 = 0
    else:
        baseline_1 = total_1 // count
        baseline_2 = total_2 // count

    armed_1 = False
    armed_2 = False

    uart.write("BASELINE:MOTION1=" + str(baseline_1) + " MOTION2=" + str(baseline_2) + "\n")


def update_baseline(current, baseline):
    if baseline is None:
        return current
    return int((baseline * BASELINE_BLEND) + (current * (1 - BASELINE_BLEND)))


def sensor_triggered(value, baseline, armed):
    if baseline is None:
        baseline = value
    delta = value - baseline
    if not armed and delta >= SENSOR_TRIGGER_DELTA:
        return True, True
    if armed and delta <= SENSOR_RESET_DELTA:
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


def process_command(command):
    if not command:
        return
    upper = command.upper()
    if upper.startswith("PAYOUT"):
        parts = upper.split()
        if len(parts) > 1:
            handle_payout(parts[1])
    elif upper.startswith("SERVO ZERO"):
        home_servos()
    elif upper.startswith("CALIBRATE"):
        calibrate_motion_baseline()
    elif upper == "LED ON":
        display.show(Image.HEART)
        uart.write("LED:ON\n")
    elif upper == "LED OFF":
        display.clear()
        uart.write("LED:OFF\n")
    elif upper.startswith("SERVO 1 "):
        try:
            angle = int(upper.split(" ")[-1])
        except Exception:
            angle = 0
        move_servo_to(SERVO_PIN_1, angle)
        uart.write("SERVO1:" + str(angle) + "\n")
    elif upper.startswith("SERVO 2 "):
        try:
            angle = int(upper.split(" ")[-1])
        except Exception:
            angle = 0
        move_servo_to(SERVO_PIN_2, angle)
        uart.write("SERVO2:" + str(angle) + "\n")
    elif upper == "SENSOR?":
        uart.write("LIGHT:" + str(display.read_light_level()) + "\n")
    elif upper == "ACK MOTION1":
        display.show("1")
        uart.write("ACK:MOTION1\n")
    elif upper == "ACK MOTION2":
        display.show("2")
        uart.write("ACK:MOTION2\n")
    elif upper:
        uart.write("ERR:UNKNOWN:" + upper + "\n")


# Ensure the servos start at 0 degrees so positional pulls are consistent and the
# motion sensor baselines are measured before we start listening for triggers.
uart.init(baudrate=115200)
home_servos()
calibrate_motion_baseline()
uart.write("READY\n")

while True:
    now_ms = running_time()
    # Capture motion sensor readings first so we can compare against the
    # previous baseline before smoothing updates.
    val_1 = read_sensor_value(SENSOR_PIN_1)
    val_2 = read_sensor_value(SENSOR_PIN_2)

    if baseline_1 is None:
        baseline_1 = val_1
    if baseline_2 is None:
        baseline_2 = val_2

    trig_1, armed_1 = sensor_triggered(val_1, baseline_1, armed_1)
    trig_2, armed_2 = sensor_triggered(val_2, baseline_2, armed_2)
    triggered_1 = trig_1
    triggered_2 = trig_2

    if triggered_1:
        armed_since_1 = now_ms
    elif armed_1 and armed_since_1 is not None and now_ms - armed_since_1 > 2500:
        armed_1 = False
        armed_since_1 = None

    if triggered_2:
        armed_since_2 = now_ms
    elif armed_2 and armed_since_2 is not None and now_ms - armed_since_2 > 2500:
        armed_2 = False
        armed_since_2 = None

    # After calculating triggers, slowly move baselines toward the latest
    # readings so drift is handled without swallowing quick changes.
    baseline_1 = update_baseline(val_1, baseline_1)
    baseline_2 = update_baseline(val_2, baseline_2)

    dial_raw = 0
    try:
        dial_raw = SENSOR_PIN_3.read_analog()
    except Exception:
        dial_raw = 0
    # Normalize the dial to a 0–100 range so the thresholds match the kit’s
    # labeled extremes.
    dial_value = (dial_raw * 100) // 1023
    if dial_value < 0:
        dial_value = 0
    if dial_value > 100:
        dial_value = 100

    if triggered_1:
        display.show("1")
        uart.write("MOTION1\n")
        uart.write("MOTION1:VAL=" + str(val_1) + "\n")
    if triggered_2:
        display.show("2")
        uart.write("MOTION2\n")
        uart.write("MOTION2:VAL=" + str(val_2) + "\n")

    if dial_value <= DIAL_LEFT:
        if last_dial != "KITKAT":
            uart.write("DIAL:KITKAT\n")
        last_dial = "KITKAT"
    elif dial_value >= DIAL_RIGHT:
        if last_dial != "JOLLY":
            uart.write("DIAL:JOLLY\n")
        last_dial = "JOLLY"

    if uart.any():
        try:
            chunk = uart.readall()
        except Exception:
            chunk = b""
        if chunk:
            try:
                incoming_buffer += chunk.decode()
            except Exception:
                try:
                    incoming_buffer += str(chunk, "utf-8")
                except Exception:
                    incoming_buffer += ""
            parts = incoming_buffer.split("\n")
            incoming_buffer = parts.pop()
            for part in parts:
                process_command(part.strip())

    if button_a.was_pressed():
        uart.write("BTN:A\n")
    if button_b.was_pressed():
        uart.write("BTN:B\n")

    utime.sleep_ms(10)
