
#include <asip.h>       // the base class definitions
#include <asipIO.h>     // the core I/O class definition
#include "utility\robot.h"       // definitions for mirtle services(motor, ir, encoder etc) 
#include "utility\HUBeeWheel.h"
#include <utility\asipDistance.h> // ultrasonics distance sensor
#include <utility\asipServos.h> // derived definitions for servo
#include <Servo.h> // needed for the servo service 

char * sketchName = "Mirtle";
// the order of the following pins is service specific, see the service definition for details

#define MIRTO_V2_BOARD // board designed for New Raspberry Pi
#if defined(__AVR_ATmega644P__) || defined(__AVR_ATmega1284P__)
#if defined MIRTO_V2_BOARD
const pinArray_t motorPins[] = {18,19,3,22,23,4};
const pinArray_t bumpPins[] = {A7,A6};
// note that analog pins are referred to by their digital number (on uno, 15 = analog 1, 16 =analog 2...)
const pinArray_t irReflectancePins[] = {A1,A3,A0,A2}; // first is control, the remainder are used as analog inputs
const pinArray_t servoPins[] = {18};     // analog pin 4
#else
const pinArray_t motorPins[] = {18,19,3,22,23,4};
const pinArray_t bumpPins[] = {12,15};
// note that analog pins are referred to by their digital number (on uno, 15 = analog 1, 16 =analog 2...)
//const pinArray_t irReflectancePins[] = {30,29,31,28}; // first is control, the remainder are used as analog inputs
// TODO - use same references as V2 board for analog pin references 
const pinArray_t irReflectancePins[] = {A1,A3,A0,A2}; // first is control, the remainder are used as analog inputs
const pinArray_t servoPins[] = {18};     // analog pin 4
#endif

#elif defined(__MK20DX256__) // Teensy 3.1
const pinArray_t motorPins[] = {8,11,9,5,6,10}; 
const pinArray_t bumpPins[] = {2,1};
// note that analog pins are referred to by their digital number (on uno, 15 = analog 1, 16 =analog 2...)
const pinArray_t irReflectancePins[] = {14,15,16,17}; // first is control, the remainder are used as analog inputs
const pinArray_t servoPins[] = {0};     // digital pin 0

#elif defined(__MK20DX128__) // Teensy 3.0 
#error "Teensy 3.0 not supported, use Teensy 3.1"

#else
const pinArray_t motorPins[] = {8,11,5,12,13,6};
const pinArray_t bumpPins[] = {9,10};
// note that analog pins are referred to by their digital number (on uno, 15 = analog 1, 16 =analog 2...)
const pinArray_t irReflectancePins[] = {14,15,16,17}; // first is control, the remainder are used as analog inputs
const pinArray_t servoPins[] = {18};     // analog pin 4
#endif

// encoder pin constants for supported boards are defined in HUBeeWheel.h
const pinArray_t encoderPins[] = {wheel_1QeiAPin,wheel_1QeiBPin, // defined in HUBeeWheel.h
                                  wheel_2QeiAPin,wheel_2QeiBPin};
//declare servo object(s) 
const byte NBR_SERVOS =1;
Servo myServos[NBR_SERVOS];  // create servo objects

asipCHECK_PINS(servoPins[NBR_SERVOS]);  // compiler will check if the number of pins is same as number of servos

const byte NBR_DISTANCE_SENSORS = 1;
const pinArray_t distancePins[] = {19};  // analog pin 5 
asipCHECK_PINS(distancePins[NBR_DISTANCE_SENSORS]); //this declaration tests for correct nbr of pin initializers

// create the services
robotMotorClass motors(id_MOTOR_SERVICE, NO_EVENT);
encoderClass encoders(id_ENCODER_SERVICE);
bumpSensorClass bumpSensors(id_BUMP_SERVICE);
irLineSensorClass irLineSensors(id_IR_REFLECTANCE_SERVICE);
asipServoClass asipServos(id_SERVO_SERVICE, NO_EVENT);
asipDistanceClass asipDistance(id_DISTANCE_SERVICE);

// make a list of the created services
asipServiceClass *services[] = { 
                                 &asipIO, // the core class for pin level I/O
                                 &motors,
                                 &encoders,
                                 &bumpSensors,
                                 &irLineSensors, 
                                 &asipServos,                                 
                                 &asipDistance };

int nbrServices = sizeof(services) / sizeof(asipServiceClass*);

void setup() {
  Serial.begin(57600);
  while (!Serial);
 // Serial.begin(250000);
  
  asip.begin(&Serial, nbrServices, (asipServiceClass **)&services, sketchName); 
  asipIO.begin(); 
  asip.reserve(SERIAL_RX_PIN);  // reserve pins used by the serial port 
  asip.reserve(SERIAL_TX_PIN);  // these defines are in asip/boards.h
  // start the services
  motors.begin(2,6,motorPins); // two motors that use a total of 6 pins  
  encoders.begin(2,4,encoderPins); // two encoders that use a total of 4 pins 
  bumpSensors.begin(2,2,bumpPins);
  irLineSensors.begin(3,4,irReflectancePins); // 3 sensors plus control pin
  asipDistance.begin(NBR_DISTANCE_SENSORS,distancePins); 
  asipServos.begin(NBR_SERVOS,servoPins,myServos);
  asip.sendPinModes(); // for debug
  asip.sendPortMap(); 
  
  for(int i=0; i< nbrServices; i++)
  {
    services[i]->reportName(&Serial); 
    Serial.print(" is service ");
    Serial.write(services[i]->getServiceId());
    Serial.println();  
  }
}

void loop() 
{
  asip.service();
}

  
