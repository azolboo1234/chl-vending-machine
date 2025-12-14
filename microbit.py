from microbit import *
import utime

# Minimal Micro:bit Web Serial demo for the candy slot machine.
# Load this .py file directly in the Micro:bit Python Editor (no GitHub link needed).
# Copy it from the Raw view so the editor does not wrap or alter characters.

SERVO_PIN_1 = pin1  # Hummingbird rotation servo on slot 1
SERVO_PIN_2 = pin2  # Hummingbird rotation servo on slot 2
SENSOR_PIN_1 = pin0  # Ultrasonic sensor on sensor slot 1
SENSOR_PIN_2 = pin8  # Ultrasonic sensor on sensor slot 2
SERVO_PERIOD_US = 20000  # 50 Hz pulses

# Hummingbird Bit servo slots expect pulses roughly in the 0.7–2.3 ms range.
SERVO_PULSE_CCW = 700
SERVO_PULSE_CW = 2300
SERVO_PULSE_STOP = 1500
SENSOR_THRESHOLD = 200  # Analog value above this counts as a detection

# Number of 20 ms pulses to send for a single spin and to stop afterward.
SERVO_SPIN_CYCLES = 250  # ~5 seconds of motion (250 * 20 ms)
SERVO_STOP_CYCLES = 8

vending_verify = 0
last_sensor_1 = False
last_sensor_2 = False


def _pulse_servo(pin, pulse_us, cycles):
    # Manually bit-bang servo pulses to keep timing precise on the Hummingbird
    # board. This avoids PWM drift that can happen with analog writes.
    gap = SERVO_PERIOD_US - pulse_us
    for _ in range(cycles):
        pin.write_digital(1)
        utime.sleep_us(pulse_us)
        pin.write_digital(0)
        utime.sleep_us(gap)


def sensor_triggered(pin):
    try:
        return pin.read_analog() > SENSOR_THRESHOLD
    except Exception:
        return pin.read_digital() == 1


def _stop_servo(pin):
    _pulse_servo(pin, SERVO_PULSE_STOP, SERVO_STOP_CYCLES)


def spin_servo(pin, clockwise):
    # Continuous rotation: ~0.7 ms drives CCW, ~2.3 ms drives CW. The stop
    # pulse is ~1.5 ms. Holding the pulse for ~5 s yields a long spin.
    pulse = SERVO_PULSE_CW if clockwise else SERVO_PULSE_CCW
    _pulse_servo(pin, pulse, SERVO_SPIN_CYCLES)
    _stop_servo(pin)  # precise stop


def handle_payout(kind):
    if kind == "KITKAT":
        display.show("K")
        spin_servo(SERVO_PIN_1, True)
        uart.write("PAYOUT:KITKAT\n")
    elif kind == "JOLLY":
        display.show("J")
        spin_servo(SERVO_PIN_2, False)
        uart.write("PAYOUT:JOLLY\n")
    else:
        display.show(Image.NO)
        _stop_servo(SERVO_PIN_1)
        _stop_servo(SERVO_PIN_2)
        uart.write("PAYOUT:NONE\n")


def set_verify(value):
    global vending_verify
    vending_verify = value
    uart.write("VERIFY:" + str(value) + "\n")


# Ensure the servos are stopped at boot so they don't drift.
_stop_servo(SERVO_PIN_1)
_stop_servo(SERVO_PIN_2)


uart.init(baudrate=115200)
set_verify(0)
uart.write("READY\n")

while True:
    detected_1 = sensor_triggered(SENSOR_PIN_1)
    detected_2 = sensor_triggered(SENSOR_PIN_2)

    if detected_1 and not last_sensor_1:
        set_verify(1)
        display.show("1")
    if detected_2 and not last_sensor_2:
        if vending_verify:
            set_verify(0)
            display.show("2")
            uart.write("CRANK\n")
        else:
            uart.write("CRANK-IGNORED\n")

    last_sensor_1 = detected_1
    last_sensor_2 = detected_2

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
        elif cmd == "VERIFY RESET":
            set_verify(0)
            display.clear()
        elif cmd.startswith("SERVO 1 "):
            value = cmd.split(" ")[-1]
            uart.write("SERVO1:" + value + "\n")
        elif cmd == "SENSOR?":
            uart.write("LIGHT:" + str(display.read_light_level()) + "\n")
        elif cmd:
            uart.write("ERR:UNKNOWN:" + cmd + "\n")

    sleep(10)
