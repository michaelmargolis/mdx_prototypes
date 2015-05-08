#include <asip.h>       // the base class definitions
#include <asipIO.h>     // the core I/O class definition
#include <Servo.h>      // if you have the servo service in utilities folder then you need this even if you don't use servos

char * sketchName = "Simple"; // this name can be queried by clients to see what is running on Arduino

// the list of services, here there is only the core service to read and write pins
asipService services[] = { 
                             &asipIO, // the core class for pin level I/O
                          };


void setup() {
  Serial.begin(57600);
 // Serial.begin(250000);
  
  asip.begin(&Serial, asipServiceCount(services), services, sketchName); 
  asipIO.begin(); // start the IO service
  asip.reserve(SERIAL_RX_PIN);  // reserve pins used by the serial port 
  asip.reserve(SERIAL_TX_PIN);  // these defines are in asip/boards.h  
}

void loop() 
{
  asip.service();
}


