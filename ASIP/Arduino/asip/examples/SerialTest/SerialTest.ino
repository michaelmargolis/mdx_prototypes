/* Leonardo SerialTest.ino */

// send i,p\n to test using peek (this works repeatedly)
// send i,q\n to test without peek (this works once)

void setup() {
  Serial.begin(57600);
  while (!Serial)
    ;
  Serial.println("ready");
}

void loop()
{
  if (Serial.available() >= 4) {
    char tag = Serial.read();
    if ( tag == 'i') { 
      Serial.print(tag);
      if (Serial.read() == ',') {
        char request = Serial.read();
        Serial.print(request);
        if ( request == 'p')
          Serial.peek();
        else
          Serial.print(" This only prints after the first message"); 
      }
    }
  }
  delay(10);
}


