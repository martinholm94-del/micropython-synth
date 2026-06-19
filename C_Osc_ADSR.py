from array import array
import math
from machine import I2S, Pin

#############################################################
# External modules
#############################################################
from D_Keyboard import D_Keyboard_GetPots, D_Keyboard_GetKey
from C_GUI import C_GUI_GetMenuIndex

#############################################################
# Hardware config
#############################################################
SAMPLE_RATE  = 22050
WT_SIZE      = 512
BUF_SAMPLES  = 64
VOLUME       = 0.1

sck_pin = Pin(7)    # Serial clock output (= BCLK på DAC)
ws_pin = Pin(8)     # Word clock output (= LRCLK på DAC)
sd_pin = Pin(9)     # Serial data output (= DIN på DAC)

audio_out = I2S(
    0,
    sck=sck_pin,
    ws=ws_pin,
    sd=sd_pin,
    mode=I2S.TX,
    bits=16,
    format=I2S.MONO,
    rate=SAMPLE_RATE,
    ibuf=800,
)

#############################################################
# Local variables
#############################################################
phase     = 0
phase_inc = 0

wavetables  = {}
active_wave = 0
_waveforms = ['sine', 'saw', 'square', 'triangle']

out_buf = bytearray(BUF_SAMPLES * 2)

tones = {"cLow" : 523,
         "c#"   : 554,
         "d"    : 587,
         "d#"   : 622,
         "e"    : 659,
         "f"    : 698,
         "f#"   : 740,
         "g"    : 784,
         "g#"   : 831,
         "a"    : 880,
         "a#"   : 932,
         "b"    : 988,
         "cHigh": 1047}

# ── ADSR state constants ──────────────────────────────────────
ADSR_IDLE    = 0
ADSR_ATTACK  = 1
ADSR_DECAY   = 2
ADSR_SUSTAIN = 3
ADSR_RELEASE = 4

# ── ADSR tidsparametre ────────────────────────────────────────
ATTACK_MS   = 10
DECAY_MS    = 10
SUSTAIN_LVL = 0.5    # 0.0 – 1.0
RELEASE_MS  = 10

# ── Forudberegnede integer-trin pr. buffer-kald ───────────────
# Envelope opdateres én gang pr. fill_buffer()-kald, ikke pr. sample.
# Amplitude repræsenteres som heltal 0–256 for at undgå float i loopen.

_LEVEL_MAX  = 65536
_BUFS_SEC   = SAMPLE_RATE // BUF_SAMPLES  # 22050 // 64 = 344 buffer-kald pr. sekund

# ADSR
_attack_inc  = 0
_sustain_int = 0
_decay_inc   = 0
_release_inc = 0

adsr_state = ADSR_IDLE
adsr_level = 0        # 0 – 255 (heltal)

_prev_tone = ""
_prev_menu_index = 0

#############################################################
# Private functions
#############################################################
def _ms_to_inc(ms, span):
    # Heltalstrin pr. buffer-kald for at gennemløbe 'span' på 'ms' millisekunder
    bufs = max(1, ms * _BUFS_SEC // 1000)
    return max(1, span // bufs)

def _build_sine():
    samples = []
    for i in range(WT_SIZE):
        sample = int(32767 * VOLUME * math.sin(2 * math.pi * i / WT_SIZE))
        samples.append(sample)
    return array('h', samples)

def _build_saw():
    samples = []
    for i in range(WT_SIZE):
        sample = int(32767 * VOLUME * (1 - 2 * i / WT_SIZE))
        samples.append(sample)
    return array('h', samples)

def _build_square():
    samples = []
    for i in range(WT_SIZE):
        if i < WT_SIZE // 2:
            sample = int(32767 * VOLUME)
        else:
            sample = int(-32767 * VOLUME)
        samples.append(sample)
    return array('h', samples)

def _build_triangle():
    samples = []
    for i in range(WT_SIZE):
        sample = int(32767 * VOLUME * (2 * abs(2 * i / WT_SIZE - 1) - 1))
        samples.append(sample)
    return array('h', samples)

def _set_frequency(freq_hz):
    global phase_inc
    phase_inc = int(WT_SIZE * freq_hz / SAMPLE_RATE * 65536)

def _set_waveform(name):
    global active_wave, wavetables
    active_wave = wavetables[name]

# ── ADSR triggers ─────────────────────────────────────────────
def _adsr_note_on():
    global adsr_state
    adsr_state = ADSR_ATTACK

def _adsr_note_off():
    global adsr_state
    adsr_state = ADSR_RELEASE

# ── Envelope-opdatering (én gang pr. buffer) ──────────────────
def _update_envelope():
    global adsr_state, adsr_level

    if adsr_state == ADSR_ATTACK:
        adsr_level += _attack_inc
        if adsr_level >= _LEVEL_MAX:
            adsr_level = _LEVEL_MAX
            adsr_state = ADSR_DECAY

    elif adsr_state == ADSR_DECAY:
        adsr_level -= _decay_inc
        if adsr_level <= _sustain_int:
            adsr_level = _sustain_int
            adsr_state = ADSR_SUSTAIN

    elif adsr_state == ADSR_RELEASE:
        adsr_level -= _release_inc
        if adsr_level <= 0:
            adsr_level = 0
            adsr_state = ADSR_IDLE

    # SUSTAIN og IDLE: adsr_level er uændret

# ── Buffer-fill ───────────────────────────────────────────────
def _fill_buffer():
    global phase

    # Opdatér envelope ÉN gang for hele bufferen (out_buf) – ingen float i loopet
    _update_envelope()

    wt   = active_wave
    buf  = out_buf
    inc  = phase_inc
    p    = phase
    mask = WT_SIZE - 1
    lvl  = adsr_level >> 8

    for i in range(BUF_SAMPLES):
        idx = (p >> 16) & mask

        val = (wt[idx] * lvl) >> 8  # type: ignore

        j = i << 1
        buf[j]     =  val & 0xFF
        buf[j + 1] = (val >> 8) & 0xFF

        p = (p + inc) & 0xFFFFFFFF

    phase = p

#############################################################
# Public functions
#############################################################
def C_Osc_ADSR_Init():
    global wavetables

    wavetables = {
        'sine':     _build_sine(),
        'saw':      _build_saw(),
        'square':   _build_square(),
        'triangle': _build_triangle(),
    }
   
    _set_waveform(_waveforms[C_GUI_GetMenuIndex()])

def C_Osc_ADSR_Task():
    global _prev_tone, _prev_menu_index

    tone = D_Keyboard_GetKey()
    if tone != _prev_tone:
        if tone in tones:
            _set_frequency(tones[tone])
            _adsr_note_on()
        else:
            _adsr_note_off()
        _prev_tone = tone

    menu_index = C_GUI_GetMenuIndex()
    if menu_index != _prev_menu_index:
        _set_waveform(_waveforms[menu_index])
        _prev_menu_index = menu_index

def C_Osc_ADSR_UpdatePots():
    global _attack_inc, _decay_inc, _release_inc, _sustain_int
    atk_ms, dec_ms, sus_lvl, rel_ms = D_Keyboard_GetPots()

    _sustain_int = int(sus_lvl * _LEVEL_MAX)
    _attack_inc  = _ms_to_inc(atk_ms,  _LEVEL_MAX)
    _decay_inc   = _ms_to_inc(dec_ms,  _LEVEL_MAX - _sustain_int)
    _release_inc = _ms_to_inc(rel_ms,  max(1, _sustain_int))

def C_Osc_ADSR_Audio():
    _fill_buffer()              # genererer 64 samples i out_buf ud fra LUT (sine, saw, square, triangle)
    audio_out.write(out_buf)    # kopierer samples fra out_buf til ibuf. DAC'en henter samples fra ibuf.
                                #.write(out_buf) blokerer indtil out_buf er tømt - out_buf kan kun tømmes når der er plads i ibuf