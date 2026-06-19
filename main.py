from machine import Timer
import machine

machine.freq(250000000)

#############################################################
# Import external modules
#############################################################
from C_TaskManager import *
from C_Osc_ADSR import *
from D_Keyboard import *
from D_QuadEncoder import *
from C_GUI import C_GUI_Init, C_GUI_Task

#############################################################
# Module setup
#############################################################

#############################################################
# Hardware config
#############################################################
# 1 ms timer interrupt:
# Define the IRQ callback ISR:
def tick(timer):
    C_TM_Update_ISR()

# Setup timer interrupt:
# It is necessary to ignore a warning, because the interpreter 
# expects an argument for the Timer() function.
tim = Timer() # type: ignore
tim.init(freq=1000, mode=Timer.PERIODIC, callback=tick)

#############################################################
# Local variables
#############################################################

#############################################################
# Init external modules
#############################################################
C_Osc_ADSR_Init()
D_Keyboard_Init()
D_QuadEncoder_Init()
C_GUI_Init()

#############################################################
# Private functions
#############################################################
def mainDebugPrint_Task():
    # print( f"Encoder state: {D_QuadEncoder_GetValue( False )}" )
    # print( f"Button state:  {D_QuadEncoder_GetButtonPressed()}" )
    atk, dec, sus, rel = D_Keyboard_GetPots()
    print(f"Attack: {atk}")
    print(f"Decay: {dec}")
    print(f"Sustain: {sus}")
    print(f"Release: {rel}")
    print(f"Active key: {D_Keyboard_GetKey()}")
    print(f"Menu index: {C_GUI_GetMenuIndex()}")

#############################################################
# Start tasks
#############################################################
C_TM_CreateTask( "SET TONE AND WAVE", 1, C_Osc_ADSR_Task )
C_TM_CreateTask( "GUI", 100, C_GUI_Task )
C_TM_CreateTask( "KEYBOARD", 100, D_Keyboard_Task )
C_TM_CreateTask( "OSC_POTS", 100, C_Osc_ADSR_UpdatePots )
#C_TM_CreateTask( "DEBUG", 1000, mainDebugPrint_Task )

###################################################################################################
# Application is now ready to fly...
###################################################################################################
print("Application running...")

# Main loop: Simply calls the TM as fast as possible
# TM is now in control of the system.
try:
    while True:
        C_TM_Execute()
        C_Osc_ADSR_Audio()

except KeyboardInterrupt:
    tim.deinit()
    print( "Application exit")
finally:
    # Clean up before exit
    pass

