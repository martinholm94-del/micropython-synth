from machine import I2C, Pin

#############################################################
# External modules
#############################################################
from D_PCF8575 import PCF8575
from D_ADS1115 import ADS1115

#############################################################
# Hardware config
#############################################################

# I2C0: PCF8575 (tangenter)
_i2c0 = I2C(id=0, scl=Pin(5), sda=Pin(4), freq=400000)
_pcf  = PCF8575(_i2c0, 0x20)

# INT-pin fra PCF8575 (open drain, derfor pull-up)
_int_pin = Pin(0, Pin.IN, Pin.PULL_UP)

# I2C1: ADS1115 (potmetre) — bruger de frigjorte ADC-pins
# AIN0 = Attack  AIN1 = Decay  AIN2 = Sustain  AIN3 = Release
_i2c1 = I2C(id=1, scl=Pin(3), sda=Pin(2), freq=400000)
_ads  = ADS1115(_i2c1, address=0x48, gain=1)  # gain=1 → ±4.096 V

# ADS1115 med gain=1 har fuldt måleområde på ±4.096 V.
# Pico leverer 3.3 V, så max råværdi bliver 32767 × (3.3/4.096) ≈ 26400.
# Vi normaliserer mod dette tal så potmetrene udnytter hele skalaen.
_ADS_MAX = int(32767 * 3.3 / 4.096)  # ≈ 26400

_MS_MAX = 3000  # Max-værdi i ms for Attack, Decay, Release

#############################################################
# Module setup
#############################################################

#############################################################
# Local variables
#############################################################
active_key = ""
_pot_attack_ms   = 10   # Standard-værdier ved opstart
_pot_decay_ms    = 10
_pot_sustain_lvl = 0.5  # 0.0 – 1.0
_pot_release_ms  = 10

# Mapping: PCF8575 bit-nummer → key-navn
# P00=bit0, P02=bit2, P04=bit4, P05=bit5, P07=bit7
# P11=bit9, P13=bit11, P14=bit12
_key_bits = {
    0:  "cLow",
    1:  "c#",
    2:  "d",
    3:  "d#",
    4:  "e",
    5:  "f",
    6:  "f#",
    7:  "g",
    8:  "g#",
    9:  "a",
    10: "a#",
    11: "b",
    12: "cHigh",
}

_previous_port = 0xFFFF  # Alle pins HIGH ved opstart

#############################################################
# Private functions
#############################################################

def _pcfHandler(p):
    global active_key, _previous_port
 
    current_port = _pcf.port  # Læs port
    changed = _previous_port ^ current_port

    for bit, key_name in _key_bits.items():
        if changed & (1 << bit):
            state = (current_port >> bit) & 1
            if state == 0:          # Pin gik LOW → knap trykket
                active_key = key_name
 
    # Efter alle ændringer: tjek om den aktive tangent stadig holdes nede.
    # Hvis ikke, find en anden der stadig er LOW (holdes nede).
 
    # Find bit-nummeret for den aktive tangent
    active_bit = None
    for bit, key_name in _key_bits.items():
        if key_name == active_key:
            active_bit = bit
            break
 
    # Tjek om den aktive tangent er sluppet (HIGH) eller slet ikke findes
    active_key_was_released = (active_bit is None) or ((current_port >> active_bit) & 1 == 1)
 
    if active_key_was_released:
        # Find en tangent der stadig holdes nede (LOW)
        active_key = ""
        for bit, key_name in _key_bits.items():
            if (current_port >> bit) & 1 == 0:
                active_key = key_name
                break
 
    _previous_port = current_port

#############################################################
# Public functions
#############################################################

def D_Keyboard_Init():
    global _previous_port
    # Sæt alle PCF8575-pins som inputs (HIGH)
    _pcf.port = 0xFFFF
    _previous_port = _pcf.port

    # Aktiver interrupt på INT-pin
    _int_pin.irq( handler=_pcfHandler, trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING )

def D_Keyboard_Task():
    # Kaldes hvert 100 ms fra task manager
    global _pot_attack_ms, _pot_decay_ms, _pot_sustain_lvl, _pot_release_ms
    # Normalisér mod _ADS_MAX så hele potmeter-skalaen udnyttes ved 3.3 V
    _pot_attack_ms   = max(10, _ads.read(rate=4, channel1=0) * _MS_MAX // _ADS_MAX)
    _pot_decay_ms    = max(10, _ads.read(rate=4, channel1=1) * _MS_MAX // _ADS_MAX)
    _pot_sustain_lvl = round(min(1.0, max(0.1, _ads.read(rate=4, channel1=2) / _ADS_MAX)), 1)
    _pot_release_ms  = max(10, _ads.read(rate=4, channel1=3) * _MS_MAX // _ADS_MAX)

def D_Keyboard_GetKey():
    return active_key

def D_Keyboard_GetPots():
    return _pot_attack_ms, _pot_decay_ms, _pot_sustain_lvl, _pot_release_ms