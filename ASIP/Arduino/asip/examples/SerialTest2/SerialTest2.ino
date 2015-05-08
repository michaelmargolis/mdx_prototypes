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
  // wait for any three characters and a terminating newline
  if (Serial.available() >= 2) {
    Serial.read(); // ignore the first character
    char c = Serial.read();
    Serial.print(c);
    if ( c == 'p')
      Serial.peek();
    else
      Serial.println(" This only prints after the first message");
  }
  delay(10);
}
