from machine import Pin

#############################################################
# External modules
#############################################################

#############################################################
# Module setup
#############################################################

#############################################################
# Hardware config
#############################################################
# Quadrature encoder = 2 digital input pins:
pinQuadEnc_A = Pin(14, Pin.IN, Pin.PULL_UP)
pinQuadEnc_B = Pin(15, Pin.IN, Pin.PULL_UP)

#############################################################
# Name definitions
#############################################################


#############################################################
# Local variables
#############################################################
# Encoder
iQuadEncValue = 0
_prevState = 0

#############################################################
# Quadrature transition table
#
# Index = (prev_state << 2) | new_state
#
# This lookup table determines direction of rotation based on
# the transition between the previous and current encoder state.
#
# Value meaning:
#  1  = clockwise step
# -1  = counter-clockwise step
#  0  = invalid transition (bounce or no movement)
#############################################################
_transition_table = (
     0, -1,  1,  0,
     1,  0,  0, -1,
    -1,  0,  0,  1,
     0,  1, -1,  0
)

#############################################################
# Private functions
#############################################################

###################################################################################################
# Brief         Updates the quadrature encoder state and calculates direction.
#
#               Reads encoder inputs A and B, generates a new state value and
#               compares it with the previous state. A lookup table is used
#               to determine the direction of rotation.
#
#               The result is added to the raw encoder counter.
#
# Param[in]     None
# Return        None
#
# Warning       Called from Interrupt Service Routine
###################################################################################################
def _updateEncoder():
    global _prevState, iQuadEncValue

    a = pinQuadEnc_A.value()
    b = pinQuadEnc_B.value()

    newState = (a << 1) | b
    index = (_prevState << 2) | newState

    iQuadEncValue += _transition_table[index]

    _prevState = newState

#############################################################
# Interrupts
#############################################################

###################################################################################################
# Brief         Interrupt service routine for encoder pin A.
#
#               Called on rising and falling edges of pin A.
#               The encoder state is updated and direction is calculated.
#
# Param[in]     pin     The pin that triggered the interrupt
# Return        None
#
# Warning       Interrupt Service Routine
#################################################################################################
def _isrQuadEncoder_A(pin):
    _updateEncoder()

###################################################################################################
# Brief         Interrupt service routine for encoder pin B.
#
#               Called on rising and falling edges of pin B.
#               The encoder state is updated and direction is calculated.
#
# Param[in]     pin     The pin that triggered the interrupt
# Return        None
#
# Warning       Interrupt Service Routine
#################################################################################################
def _isrQuadEncoder_B(pin):
    _updateEncoder()


#############################################################
# Public functions
#############################################################

###################################################################################################
# Brief         Initializes the quadrature encoder module.
#
#               Reads the initial encoder state and enables interrupts
#               on both encoder input pins.
#
# Param[in]     None
# Return        None
#
# Warning       Must be called once during system initialization
#################################################################################################
def D_QuadEncoder_Init():
    global _prevState

    # Read initial state
    a = pinQuadEnc_A.value()
    b = pinQuadEnc_B.value()
    _prevState = (a << 1) | b

    # Enable interrupts
    pinQuadEnc_A.irq( handler=_isrQuadEncoder_A, trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING )

    pinQuadEnc_B.irq( handler=_isrQuadEncoder_B, trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING )

#############################################################
# Encoder functions
#############################################################

###################################################################################################
# Brief         Returns the current encoder value.
#
#               The internal counter tracks every quadrature transition.
#               Since a typical encoder produces four transitions per
#               mechanical click (detent), the value is divided by 4
#               using a bit shift.
#
# Param[in]     bReset      True  = reset encoder counter after reading
#                           False = keep encoder counter unchanged
#
# Return        Encoder position in detents (clicks)
#
# Warning       None
###################################################################################################

def D_QuadEncoder_GetValue( bReset ):
    global iQuadEncValue

    val = iQuadEncValue >> 2

    if bReset:
        iQuadEncValue -= val << 2

    return val

###################################################################################################
# Brief         Resets the quad encoder value to 0
#
# Param[in]     None
# Return        None
#
# Warning       None
###################################################################################################
def D_QuadEncoder_ResetValue():
    global iQuadEncValue
    iQuadEncValue = 0


    