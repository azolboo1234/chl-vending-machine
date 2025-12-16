// Candy Vending Machine firmware for micro:bit v2 + Hummingbird Bit
// FIXED: Motion sensor 2 now triggers correctly (uses absolute delta + sane thresholds).
// Protocol matches your HTML:
//   micro:bit -> browser: READY, BTN:A/BTN:B, MOTION1/2 (+ MOTIONx:VAL=...), DIAL:KITKAT/JOLLY
//   browser -> micro:bit: PAYOUT KITKAT/JOLLY/NONE, SERVO ZERO, CALIBRATE, ACK MOTION1/2

hummingbird.startHummingbird()
serial.setBaudRate(BaudRate.BaudRate115200)

// --- Tuning ---
const DIAL_LEFT = 35
const DIAL_RIGHT = 65

const CAL_SAMPLES = 24
const CAL_DELAY_MS = 10

// Distance values are typically "cm-like". 30 was way too big.
// Use ABS change so it triggers whether the value rises OR falls.
const TRIGGER_DELTA = 8
const RESET_DELTA = 3
const BASELINE_BLEND = 0.9

// Servo "payout" motion
const SERVO_PAYOUT_ANGLE = 90
const SERVO_PAYOUT_HOLD_MS = 350

let baseline1 = 0
let baseline2 = 0
let armed1 = false
let armed2 = false
let armedSince1 = -1
let armedSince2 = -1

let lastDial = "" // "KITKAT" | "JOLLY" | ""

function clamp(v: number, lo: number, hi: number) {
    return Math.max(lo, Math.min(hi, v))
}

function updateBaseline(current: number, baseline: number) {
    return Math.round(baseline * BASELINE_BLEND + current * (1 - BASELINE_BLEND))
}

function readDistance1(): number {
    return hummingbird.getSensor(SensorType.Distance, ThreePort.One)
}

function readDistance2(): number {
    return hummingbird.getSensor(SensorType.Distance, ThreePort.Two)
}

function readDial0to100(): number {
    const v = hummingbird.getSensor(SensorType.Dial, ThreePort.Three)
    return clamp(v, 0, 100)
}

function calibrate() {
    let t1 = 0
    let t2 = 0
    for (let i = 0; i < CAL_SAMPLES; i++) {
        t1 += readDistance1()
        t2 += readDistance2()
        basic.pause(CAL_DELAY_MS)
    }
    baseline1 = Math.round(t1 / CAL_SAMPLES)
    baseline2 = Math.round(t2 / CAL_SAMPLES)
    armed1 = false
    armed2 = false
    armedSince1 = -1
    armedSince2 = -1
    serial.writeLine(`BASELINE:MOTION1=${baseline1} MOTION2=${baseline2}`)
}

function homeServos() {
    hummingbird.setPositionServo(FourPort.One, 0)
    hummingbird.setPositionServo(FourPort.Two, 0)
    serial.writeLine("SERVO:ZERO")
}

function payoutServo(port: FourPort) {
    hummingbird.setPositionServo(port, SERVO_PAYOUT_ANGLE)
    basic.pause(SERVO_PAYOUT_HOLD_MS)
    hummingbird.setPositionServo(port, 0)
    basic.pause(200)
}

function handlePayout(kind: string) {
    if (kind === "KITKAT") {
        payoutServo(FourPort.One)
        serial.writeLine("PAYOUT:KITKAT")
    } else if (kind === "JOLLY") {
        payoutServo(FourPort.One)   // ← PATCH: Two → One (ONLY CHANGE)
        serial.writeLine("PAYOUT:JOLLY")
    } else {
        homeServos()
        serial.writeLine("PAYOUT:NONE")
    }
}

// --- Incoming commands from your HTML ---
serial.onDataReceived(serial.delimiters(Delimiters.NewLine), function () {
    const raw = serial.readLine()
    if (!raw) return
    const cmd = raw.trim()
    if (!cmd) return

    const upper = cmd.toUpperCase()

    if (upper.indexOf("PAYOUT") === 0) {
        const parts = upper.split(" ")
        if (parts.length >= 2) handlePayout(parts[1])
        return
    }

    if (upper === "SERVO ZERO") {
        homeServos()
        return
    }

    if (upper === "CALIBRATE") {
        calibrate()
        return
    }

    if (upper === "ACK MOTION1") {
        serial.writeLine("ACK:MOTION1")
        return
    }

    if (upper === "ACK MOTION2") {
        serial.writeLine("ACK:MOTION2")
        return
    }

    if (upper.indexOf("SERVO 1 ") === 0) {
        const parts = upper.split(" ")
        const a = clamp(parseInt(parts[2]), 0, 180)
        hummingbird.setPositionServo(FourPort.One, a)
        serial.writeLine("SERVO1:" + a)
        return
    }
    if (upper.indexOf("SERVO 2 ") === 0) {
        const parts = upper.split(" ")
        const a = clamp(parseInt(parts[2]), 0, 180)
        hummingbird.setPositionServo(FourPort.Two, a)
        serial.writeLine("SERVO2:" + a)
        return
    }

    serial.writeLine("ERR:UNKNOWN:" + upper)
})

// --- Startup ---
homeServos()
calibrate()
serial.writeLine("READY")

// --- Main loop ---
basic.forever(function () {
    const now = input.runningTime()

    const v1 = readDistance1()
    const v2 = readDistance2()

    const d1 = Math.abs(v1 - baseline1)
    const d2 = Math.abs(v2 - baseline2)

    let trig1 = false
    let trig2 = false

    if (!armed1 && d1 >= TRIGGER_DELTA) { trig1 = true; armed1 = true; armedSince1 = now }
    if (!armed2 && d2 >= TRIGGER_DELTA) { trig2 = true; armed2 = true; armedSince2 = now }

    if (armed1 && d1 <= RESET_DELTA) { armed1 = false; armedSince1 = -1 }
    if (armed2 && d2 <= RESET_DELTA) { armed2 = false; armedSince2 = -1 }

    if (armed1 && armedSince1 >= 0 && now - armedSince1 > 2500) { armed1 = false; armedSince1 = -1 }
    if (armed2 && armedSince2 >= 0 && now - armedSince2 > 2500) { armed2 = false; armedSince2 = -1 }

    baseline1 = updateBaseline(v1, baseline1)
    baseline2 = updateBaseline(v2, baseline2)

    if (trig1) {
        serial.writeLine("MOTION1")
        serial.writeLine("MOTION1:VAL=" + v1)
    }
    if (trig2) {
        serial.writeLine("MOTION2")
        serial.writeLine("MOTION2:VAL=" + v2)
    }

    const dial = readDial0to100()
    if (dial <= DIAL_LEFT) {
        if (lastDial !== "KITKAT") serial.writeLine("DIAL:KITKAT")
        lastDial = "KITKAT"
    } else if (dial >= DIAL_RIGHT) {
        if (lastDial !== "JOLLY") serial.writeLine("DIAL:JOLLY")
        lastDial = "JOLLY"
    }

    if (input.buttonIsPressed(Button.A)) {
        serial.writeLine("BTN:A")
        basic.pause(180)
    }
    if (input.buttonIsPressed(Button.B)) {
        serial.writeLine("BTN:B")
        basic.pause(180)
    }

    basic.pause(10)
})
