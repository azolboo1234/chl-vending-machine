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
4. Press button **A** on the micro:bit to trigger a random pick: the page receives `BTN:A`, chooses 0 or 1 with equal
   chance, sends back `CHOICE 0` or `CHOICE 1`, and the micro:bit displays that number on its LEDs (and echoes `SHOW:0`
   or `SHOW:1`). With a Hummingbird rotation servo on slot 1, `CHOICE 1` spins it clockwise once; `CHOICE 0`
   spins it counterclockwise once.
5. Responses and button events appear in the log. Click **Disconnect** when finished.

### Flashing the micro:bit
1. Open the `microbit/serial_demo.py` file in the Micro:bit Python Editor or Mu. If you are using the web editor, click **Load/Upload** and choose the file directly (no GitHub connection is required).
2. Flash it to the board. The script starts a UART at 115200 baud, responds to the commands above, emits `BTN:A` / `BTN:B` events on button presses, and renders `CHOICE 0` / `CHOICE 1` responses on the LED grid while spinning the rotation servo once.
3. A Hummingbird rotation servo on slot 1 will rotate clockwise for `CHOICE 1` and counterclockwise for `CHOICE 0`; the stub `SERVO 1 <angle>` handler still just echoes the value.
4. If the Micro:bit Python Editor reports syntax errors, it is usually because the file was copied from a rendered GitHub Page rather than downloaded directly. Use **Raw** → **Save As** (or upload the `.py` file) so the editor receives the exact text.
