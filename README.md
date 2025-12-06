# chl-vending-machine

gl on gettin candy

## Micro:bit ↔ GitHub Pages Test Harness

This repo now includes a minimal Web Serial console (`index.html`) and a companion MicroPython firmware (`microbit/serial_demo.py`) so you can test two-way messaging between a GitHub Pages site and a micro:bit with the Hummingbird kit.

### How to use the test page
1. Serve `index.html` (or host it on GitHub Pages) and open it in a recent Chromium-based browser (Chrome, Edge, Opera). The page requires the `navigator.serial` API.
2. Click **Connect micro:bit (Web Serial)** and select your micro:bit (vendor ID `0x0D28`).
3. Use the input to send newline-terminated commands such as:
   - `LED ON` / `LED OFF`
   - `SERVO 1 90`
   - `SENSOR?`
4. Responses and button events appear in the log. Click **Disconnect** when finished.

### Flashing the micro:bit
1. Open the `microbit/serial_demo.py` file in the Micro:bit Python Editor or Mu.
2. Flash it to the board. The script starts a UART at 115200 baud, responds to the commands above, and emits `BTN:A` / `BTN:B` events on button presses.
3. If you have Hummingbird servos connected, replace the placeholder servo section with calls to your driver (the sample just echoes the requested angle).
