# asip.py -   Arduino Services Interface Protocol (ASIP)

#class ASIP(object):

# System messages
# Request messages to Arduino
SYSTEM_MSG_HEADER   = '#' # system requests are preceded with this tag
tag_SYSTEM_GET_INFO = '?' # Get version and hardware info
tag_RESTART_REQUEST = 'R' # disables all autoevents and attempts to restart all services 

# messages from Arduino
EVENT_HEADER= '@'  # event messages are preceded with this tag 
ERROR_MSG_HEADER= '~'  # error messages begin with this tag
DEBUG_MSG_HEADER= '!'  # debug messages begin with this tag

# tags available to all services 
tag_AUTOEVENT_REQUEST = 'A'  # this tag sets autoevent status
tag_REMAP_PIN_REQUEST = 'M'  # for services that can change pin numbers
# Reply tags common to all services
tag_SERVICE_EVENT = 'e' 

MIN_MSG_LEN = 4  # valid request messages must be at least this many characters

NO_EVENT = '\0'  # tag to indicate the a service does not produce an event
MSG_TERMINATOR = '\n'

#class Mirto(object):
# Motor service
id_MOTOR_SERVICE = 'M'
# Motor methods (messages to Arduino)
tag_SET_MOTOR = 'm'  
tag_SET_MOTORS= 'M'
tag_STOP_MOTOR= 's'  
tag_STOP_MOTORS   = 'S'

# Encoder service
id_ENCODER_SERVICE = 'E'
# Encoder methods - use system define, tag_AUTOEVENT_REQUEST ('A') to request autoevents
# Encoder events -  events use system tag: tag_SERVICE_EVENT  ('e')


# Bump detect service
id_BUMP_SERVICE = 'B'
# Bump sensor methods - use system define, tag_AUTOEVENT_REQUEST ('A') to request autoevents
# Bump Sensor events -  events use system tag: tag_SERVICE_EVENT  ('e')


# IR Line detect service
id_IR_REFLECTANCE_SERVICE = 'R'
# IR Line detect methods - use system define, tag_AUTOEVENT_REQUEST ('A') to request autoevents
# IR Line detect events -  events use system tag: tag_SERVICE_EVENT  ('e')

NBR_WHEELS = 2  # defines the number of wheels (and encoders), note not tested with values other than 2

INFO_REQUEST = '#,?\n'
PIN_MODES_REQUEST = 'I,p\n'
CAPABILITY_REQUEST = 'I,c\N'
