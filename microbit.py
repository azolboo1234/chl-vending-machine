from microbit import *
import utime

# Minimal Micro:bit Web Serial demo for the candy vending machine.
# Load this .py file directly in the Micro:bit Python Editor (no GitHub link needed).
# Copy it from the Raw view so the editor does not wrap or alter characters.

SERVO_PIN_1 = pin1  # Hummingbird positional servo on servo slot 1
SERVO_PIN_2 = pin2  # Hummingbird positional servo on servo slot 2
SENSOR_PIN_1 = pin0  # Distance sensor on sensor slot 1 (3-wire analog)
SENSOR_PIN_2 = pin8  # Distance sensor on sensor slot 2 (3-wire analog)
SENSOR_PIN_3 = pin3  # Rotary dial on sensor slot 3 (potentiometer)
SERVO_PERIOD_US = 20000  # 50 Hz pulses

# Hummingbird Bit servos expect roughly 0.6–2.4 ms pulses for 0–180 degrees.
SERVO_PULSE_MIN = 600
SERVO_PULSE_MAX = 2400
DIAL_LOW = 320
DIAL_HIGH = 700

CALIBRATION_SAMPLES = 24
CALIBRATION_DELAY_MS = 10

# Adaptive distance-sensor detection tuned for the analog distance sensors that ship
# with the Hummingbird premium kit. These values fire on hand waves at ~8–12 cm while
# rejecting slow drift.
SENSOR_TRIGGER_DELTA = 30  # Change needed from baseline to count as a hit
SENSOR_RESET_DELTA = 18  # Change needed to fall back to idle
BASELINE_BLEND = 0.9  # Exponential moving average for smoothing
TARGET_MAX_CM = 10
RESET_CM = 14

ANGLE_SETTLE_MS = 700

last_dial = None
baseline_1 = None
baseline_2 = None
armed_1 = False
armed_2 = False
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


def calibrate_distance_baseline():
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

    uart.write("BASELINE:DIST1=" + str(baseline_1) + " DIST2=" + str(baseline_2) + "\n")


def update_baseline(current, baseline):
    if baseline is None:
        return current
    return int((baseline * BASELINE_BLEND) + (current * (1 - BASELINE_BLEND)))


def sensor_triggered(value, baseline, distance_cm, armed):
    if baseline is None:
        baseline = value
    delta = value - baseline
    magnitude = delta if delta >= 0 else -delta
    direct_hit = distance_cm <= TARGET_MAX_CM
    delta_hit = magnitude >= SENSOR_TRIGGER_DELTA
    release = distance_cm >= RESET_CM and magnitude <= SENSOR_RESET_DELTA

    if not armed and (direct_hit or delta_hit):
        return True, True
    if armed and release:
        return False, False
    return False, armed


def estimate_distance_cm(value):
    if value <= 0:
        return 999
    # Lightweight reciprocal approximation for the Hummingbird analog distance
    # sensor. Higher readings mean closer objects. The constant is tuned so that
    # values around 600–1200 (typical within 5–10 cm) land in the desired range.
    est = 6000 // value
    if est < 1:
        est = 1
    if est > 200:
        est = 200
    return est



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
        calibrate_distance_baseline()
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
    elif upper == "ACK DIST1":
        display.show("1")
        uart.write("ACK:DIST1\n")
    elif upper == "ACK DIST2":
        display.show("2")
        uart.write("ACK:DIST2\n")
    elif upper:
        uart.write("ERR:UNKNOWN:" + upper + "\n")


# Ensure the servos start at 0 degrees so positional pulls are consistent and the
# distance sensor baselines are measured before we start listening for triggers.
uart.init(baudrate=115200)
home_servos()
calibrate_distance_baseline()
uart.write("READY\n")

while True:
    # Capture distance sensor readings first so we can compare against the
    # previous baseline before smoothing updates.
    val_1 = read_sensor_value(SENSOR_PIN_1)
    val_2 = read_sensor_value(SENSOR_PIN_2)

    if baseline_1 is None:
        baseline_1 = val_1
    if baseline_2 is None:
        baseline_2 = val_2

    distance_cm_1 = estimate_distance_cm(val_1)
    distance_cm_2 = estimate_distance_cm(val_2)

    trig_1, armed_1 = sensor_triggered(val_1, baseline_1, distance_cm_1, armed_1)
    trig_2, armed_2 = sensor_triggered(val_2, baseline_2, distance_cm_2, armed_2)
    triggered_1 = trig_1
    triggered_2 = trig_2

    # After calculating triggers, slowly move baselines toward the latest
    # readings so drift is handled without swallowing quick changes.
    baseline_1 = update_baseline(val_1, baseline_1)
    baseline_2 = update_baseline(val_2, baseline_2)

    dial_value = 0
    try:
        dial_value = SENSOR_PIN_3.read_analog()
    except Exception:
        dial_value = 0

    if triggered_1:
        display.show("1")
        uart.write("DIST1\n")
        uart.write("DIST1:VAL=" + str(val_1) + "\n")
        uart.write("DIST1:CM=" + str(distance_cm_1) + "\n")
    if triggered_2:
        display.show("2")
        uart.write("DIST2\n")
        uart.write("DIST2:VAL=" + str(val_2) + "\n")
        uart.write("DIST2:CM=" + str(distance_cm_2) + "\n")

    if dial_value < DIAL_LOW:
        if last_dial != "KITKAT":
            uart.write("DIAL:KITKAT\n")
        last_dial = "KITKAT"
    elif dial_value > DIAL_HIGH:
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
