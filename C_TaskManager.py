#############################################################
# Module setup
#############################################################
MAX_NUM_OF_TASKS = 10
TM_TIMER_INTERVAL = 1 # ms
bPrintDebug = False

#############################################################
# Hardware config
#############################################################
# None

#############################################################
# Local variables
#############################################################
# Create the list of tasks to execute:
listTasks = []

#############################################################
# Name definitions
#############################################################
# Define index for the task structure:
TASK_NAME = 0
TASK_INTERVAL = 1
TASK_TIMER = 2
TASK_CALLBACK = 3

###################################################################################################
# Public functions
###################################################################################################

###################################################################################################
# Brief         Create new task
#
# Param[in]     strTaskName:    A representative name for the task. Only used for debug purpose.
#               iInterval_ms:   Task interval in ms
#               funcCallback:   The function to call as task
# Return        None
#
# Warning       None
###################################################################################################
def C_TM_CreateTask( strTaskName: str, iInterval_ms: int, funcCallback ):

    iNumOfTasks = len(listTasks)
    
    # Check if we have a free slot for this task:
    if iNumOfTasks < MAX_NUM_OF_TASKS:
        listTemp = [strTaskName, iInterval_ms, 0, funcCallback]
        listTasks.append(listTemp)

        if bPrintDebug == True:
            print(f"Task number {iNumOfTasks} added succesfully")
       
    else:
        if bPrintDebug == True:
            print("Task not added due to max number of tasks")

###################################################################################################
# Brief         IRQ callback function
#               Decrement timers for all registered tasks.
# Param[in]     None
# Return        None
#
# Warning       Called by IRQ every 1 ms
###################################################################################################
def C_TM_Update_ISR():
    i = 0
    for thisTask in listTasks:
        if thisTask[TASK_TIMER] > 0:
            thisTask[TASK_TIMER] -= TM_TIMER_INTERVAL
            listTasks[i] = thisTask
        i += 1
    
###################################################################################################
# Brief         Runs through all registered tasks. If timeout, then call the task function
#               
# Param[in]     None
# Return        None
#
# Warning       Must be call as fast as possible in an infinite loop
# ###################################################################################################
def C_TM_Execute():
    i = 0

    for thisTask in listTasks:
        if thisTask[TASK_TIMER] <= 0:
            # Timeout -> Call task function:
            # Update timer and task list:
            thisTask[TASK_TIMER] = thisTask[TASK_INTERVAL]
            listTasks[i] = thisTask

            # Call the task function:
            if( thisTask[TASK_CALLBACK] ):
                thisTask[TASK_CALLBACK]()

            if bPrintDebug == True:
                print( "Task: " + thisTask[TASK_NAME] ) 
        i += 1

