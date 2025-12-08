from microbit import *
import utime

# Minimal Micro:bit Web Serial demo.
# Load this .py file directly in the Micro:bit Python Editor (no GitHub link needed).
# Copy it from the Raw view so the editor does not wrap or alter characters.

SERVO_PIN = pin1  # Hummingbird rotation servo on slot 1
SERVO_PERIOD_US = 20000  # 50 Hz pulses

# Hummingbird Bit servo slots expect pulses roughly in the 0.7–2.3 ms range.
SERVO_PULSE_CCW = 700
SERVO_PULSE_CW = 2300
SERVO_PULSE_STOP = 1500

# Number of 20 ms pulses to send for a single spin and to stop afterward.
SERVO_SPIN_CYCLES = 60  # ~1.2 s of motion
SERVO_STOP_CYCLES = 6


def _pulse_servo(pulse_us, cycles):
    # Manually bit-bang servo pulses to keep timing precise on the Hummingbird
    # board. This avoids PWM drift that can happen with analog writes.
    gap = SERVO_PERIOD_US - pulse_us
    for _ in range(cycles):
        SERVO_PIN.write_digital(1)
        utime.sleep_us(pulse_us)
        SERVO_PIN.write_digital(0)
        utime.sleep_us(gap)


# Ensure the servo is stopped at boot so it doesn't drift.
_pulse_servo(SERVO_PULSE_STOP, SERVO_STOP_CYCLES)


def spin_servo(clockwise):
    # Continuous rotation: ~0.7 ms drives CCW, ~2.3 ms drives CW. The stop
    # pulse is ~1.5 ms. Holding the pulse for ~1.2 s yields about one spin.
    pulse = SERVO_PULSE_CW if clockwise else SERVO_PULSE_CCW
    _pulse_servo(pulse, SERVO_SPIN_CYCLES)
    _pulse_servo(SERVO_PULSE_STOP, SERVO_STOP_CYCLES)  # precise stop


uart.init(baudrate=115200)
uart.write("READY\n")

while True:
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
        elif cmd == "CHOICE 0":
            display.show("0")
            spin_servo(False)  # counterclockwise
            uart.write("SHOW:0\n")
        elif cmd == "CHOICE 1":
            display.show("1")
            spin_servo(True)  # clockwise
            uart.write("SHOW:1\n")
        elif cmd.startswith("SERVO 1 "):
            # Replace this stub with your Hummingbird servo driver if available.
            value = cmd.split(" ")[-1]
            uart.write("SERVO1:" + value + "\n")
        elif cmd == "SENSOR?":
            uart.write("LIGHT:" + str(display.read_light_level()) + "\n")
        elif cmd:
            uart.write("ERR:UNKNOWN:" + cmd + "\n")

    sleep(10)
