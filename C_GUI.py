from machine import SPI, Pin

#############################################################
# External modules
#############################################################
import Fonts.Font_CodeSansRegular_15 as Font15
import Fonts.Font_CodeSansRegular_30 as Font30
import D_ILI9225
from D_QuadEncoder import D_QuadEncoder_GetValue
from D_Keyboard import D_Keyboard_GetPots

#############################################################
# Module setup
#############################################################
GUI_TASK_INTERVAL = 100

SCREEN_SIZE_W = 220
SCREEN_SIZE_H = 176

#############################################################
# Hardware config
#############################################################
spiDisplay = SPI(0, baudrate=40000000, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
display = D_ILI9225.ILI9225(spiDisplay, ss_pin=17, rs_pin=13, rst_pin=12, rotation=3)
pinLED_backlight = Pin(11, Pin.OUT)

#############################################################
# Local variables
#############################################################
iMenu = 0
_prev_adsr = (None, None, None, None)

#############################################################
# Name definitions
#############################################################
ALIGN_LEFT   = const(0)
ALIGN_CENTER = const(1)
ALIGN_RIGHT  = const(2)

# Menu items og Y-positioner (Font30)
_MENU_NAMES = ["Sine Wave", "Saw Wave", "Square Wave", "Triangle Wave"]
_MENU_Y     = [5, 38, 71, 104]

# ADSR layout:
# To linjer i bunden, Font15 (15px høj).
# Y2 = 176 - 15 = 161 (værdier), Y1 = 161 - 15 - 1 = 145 (labels)
_ADSR_Y1  = 145        # Labels:  ATK  DEC  SUS  REL
_ADSR_Y2  = 161        # Værdier: 10ms 200ms 0.40 2000ms

# Fire lige brede kolonner à 55px (4 × 55 = 220)
_COL_W    = 55
_COLS     = [0, 55, 110, 165]
_ADSR_LABELS = ["ATK", "DEC", "SUS", "REL"]

# 3% af det fulde måleområde
_MS_THRESHOLD  = 3000 * 0.03    # = 90 ms
_SUS_THRESHOLD = 1.0  * 0.03    # = 0.03

###################################################################################################
# Private functions
###################################################################################################
def _draw_menu(highlight):
    for i, name in enumerate(_MENU_NAMES):
        color = 0xFF0000 if i == highlight else 0xFFFFFF
        display.print(name, 0, _MENU_Y[i], Font30, fg_color=color, align=ALIGN_CENTER, iTxtBoxWidth=SCREEN_SIZE_W)

def _draw_adsr(atk, dec, sus, rel):
    values = [f"{atk}ms", f"{dec}ms", f"{sus:.2f}", f"{rel}ms"]
    for i, (lbl, val) in enumerate(zip(_ADSR_LABELS, values)):
        x = _COLS[i]
        display.print(lbl, x, _ADSR_Y1, Font15, fg_color=0xAAAAAA, align=ALIGN_CENTER, iTxtBoxWidth=_COL_W)
        display.print(val, x, _ADSR_Y2, Font15, fg_color=0xFFFFFF, align=ALIGN_CENTER, iTxtBoxWidth=_COL_W)

def _adsr_changed(new, old):
    if old[0] is None:
        return True
    atk_n, dec_n, sus_n, rel_n = new
    atk_o, dec_o, sus_o, rel_o = old
    return (abs(atk_n - atk_o) > _MS_THRESHOLD  or
            abs(dec_n - dec_o) > _MS_THRESHOLD  or
            abs(sus_n - sus_o) > _SUS_THRESHOLD or
            abs(rel_n - rel_o) > _MS_THRESHOLD)

###################################################################################################
# Public functions
###################################################################################################
def C_GUI_Init():
    pinLED_backlight.value(1)
    display.clear()
    _draw_menu(0)
    atk, dec, sus, rel = D_Keyboard_GetPots()
    _draw_adsr(atk, dec, sus, rel)

def C_GUI_Task():
    global iMenu, _prev_adsr

    # Opdatér menu hvis encoder er drejet
    deltaEnc = D_QuadEncoder_GetValue(True)
    if deltaEnc != 0:
        iMenu = max(0, min(3, iMenu + deltaEnc))
        _draw_menu(iMenu)

    # Opdatér ADSR kun hvis en værdi har ændret sig med mere end 3%
    atk, dec, sus, rel = D_Keyboard_GetPots()
    current_adsr = (atk, dec, sus, rel)
    if _adsr_changed(current_adsr, _prev_adsr):
        _draw_adsr(atk, dec, sus, rel)
        _prev_adsr = current_adsr

def C_GUI_GetMenuIndex():
    return iMenu