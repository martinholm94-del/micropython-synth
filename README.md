# Synthesizer based on Raspberry Pi Pico 2 W and MicroPython

<img width="986" height="794" alt="image" src="https://github.com/user-attachments/assets/830f084d-a377-45b5-95ee-e509dabd6749" />

This project demonstrates the design, implementation, and testing of a software-based synthesizer built on a **Raspberry Pi Pico 2 W** and programmed in **MicroPython**. The project investigates and proves that real-time audio generation and digital signal processing are possible on a microcontroller using an interpreted language, provided that low-level optimization concepts are applied.

The project was developed within the IT-technology higher education program at **Business Academy Aarhus**.

---

## Features
* **Multi-Waveform Oscillator:** Generates sine, sawtooth, square, and triangle waves without audible audio glitching or dropouts (22050 Hz, 16-bit mono).
* **Physical 13-Key Keyboard:** Controls frequencies corresponding to a full octave (from low C: 523 Hz to high C: 1047 Hz).
* **Adjustable ADSR Envelope:** Real-time sound shaping (Attack, Decay, Sustain, Release) controlled via 4 analog potentiometers.
* **Responsive Menu & Display:** Graphical ILI9225 display visualizing the active waveform and current ADSR parameters.
* **Low Latency:** Optimized to achieve a latency of approx. 20 ms from keypress to audio output.

---

## Hardware Architecture

The system is engineered around the Raspberry Pi Pico 2 W. To overcome the microcontroller's GPIO and ADC pin limitations, I²C expanders are utilized to offload standard I/O:

* **Brain:** Raspberry Pi Pico 2 W
* **I/O Expander (Keyboard):** PCF8575 via I²C (handles the 13 tactical buttons)
* **ADC Amplifier (Potentiometers):** ADS1115 via I²C (normalizes ADSR inputs)
* **DAC & Amplifier:** MAX98357A via I2S (converts and amplifies digital audio to an analog signal)
* **Display:** ILI9225 via SPI
* **Input:** Rotary encoder (waveform selection) and 4x 10kΩ potentiometers

### Block Diagram
<img width="1004" height="258" alt="image" src="https://github.com/user-attachments/assets/1501fe86-755b-4e7c-9020-8c0541988cdc" />

### Electrical Diagram
<img width="1004" height="949" alt="image" src="https://github.com/user-attachments/assets/f96562c0-ab23-48de-8522-a79ff963355d" />

---

## Software Design & Optimization

Because MicroPython runs significantly slower than native C/C++, the codebase employs heavy low-level optimizations to prevent buffer underruns and audio stuttering:

1. **Wavetables (Look-Up Tables):** Computing mathematical functions like `math.sin()` in real time is computationally expensive. At boot, 512 samples are pre-calculated for each waveform into arrays. Audio generation is thus reduced to lightning-fast array indexing.
2. **Fixed-Point Math:** To eliminate heavy floating-point arithmetic in the audio loop, `phase` and `amplitude` (ADSR) calculations are represented as 32-bit and 16-bit integers, managed using fast bit-shifting operations (`>>` and `<<`).
3. **Non-Blocking Task Manager:** To prevent SPI display updates and I²C ADC reads from blocking the critical I2S audio stream, background tasks are handled by a custom scheduler running at deterministic intervals (e.g., 1 ms for keyboard scanning, 100 ms for UI/potentiometer updates).

### Module Structure
* `main.py`: Initializes the hardware peripherals and drives the core execution loop.
* `C_TaskManager.py`: Manages non-blocking timing intervals for peripheral tasks.
* `C_OSC_ADSR.py`: The audio engine core containing wavetables and the ADSR finite state machine.
* `D_Keyboard.py`: Handles PCF8575 interrupts and normalizes analog inputs from the ADS1115.
* `C_GUI.py`: Renders menus, active waves, and ADSR metric bars on the ILI9225 display.
* `D_QuadEncoder.py`: Decodes inputs from the rotary encoder.

---

## Installation and Usage

### Prerequisites
* A Raspberry Pi Pico 2 W development board.
* PCF8575
* ADS1115
* ILI9225
* An IDE supporting MicroPython development (e.g., **Thonny IDE** or VS Code with the MicroPython extension).
* Necessary driver libraries uploaded:
  * `D_PCF8575.py`
  * `D_ADS1115.py`
  * `D_ILI9225.py`

### Pictures of the prototype
<img width="955" height="536" alt="image" src="https://github.com/user-attachments/assets/7cf45410-c631-4a2c-b2e4-1c98406e1621" />
<img width="834" height="523" alt="image" src="https://github.com/user-attachments/assets/b95437aa-ae1b-4d3a-b4db-ce49c77ca00a" />
<img width="831" height="529" alt="image" src="https://github.com/user-attachments/assets/5807940a-766e-44ba-bc19-7ca84ba7ca07" />
<img width="833" height="535" alt="image" src="https://github.com/user-attachments/assets/c581edaa-807a-4099-9ae2-be70f80fbfb7" />
<img width="680" height="414" alt="image" src="https://github.com/user-attachments/assets/7d796e4e-9ca6-4c43-a20b-e732b94c8295" />
<img width="680" height="409" alt="image" src="https://github.com/user-attachments/assets/53faba12-7bfe-4c40-8bf9-46214a8e019e" />
<img width="680" height="390" alt="image" src="https://github.com/user-attachments/assets/9a51ea8c-234b-4811-94ac-55c72be177cb" />


The project is made by Martin Schmidt Holm - IT-Technology Student, Business Academy Aarhus (May 2026).
