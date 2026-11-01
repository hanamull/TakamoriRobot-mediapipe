#include <HIRO.h>
#include <HIRO_Motion.h>
#include <HIRO.h>



HIRO hiro; // Declare an intance of HIRO.
int status = 0;
int priorStatus = 0;
void setup() {
  hiro.begin();
  //hiro.genZeroBegin(); Uncomment this line and comment the line above if you are using H.I.R.O. Gen Zero Edition.
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
  neutralStance(hiro);
  rgbRandom();
  delay(50);
  while (!Serial) {
    ;  // wait for serial port to connect. Needed for native USB port only
  }
    Serial.println("Hello! My name is H.I.R.O!");
  }
 

void loop() {
  if(Serial.available()){
    priorStatus = status;
    status = int(Serial.parseInt());
    //Serial.println(status);
    //Serial.println("Hello! My name is H.I.R.O!");
    // Serial.println("priorStatus: " + String(priorStatus));
    // Serial.println("status: " + String(status));
    if(priorStatus != status){
      Serial.println("Something changed" + String(status));
      switch (status) {
        case 1:
        // rgbRandom();
          wave(hiro);
          Serial.println("case1");
          break;
        case 10:
          rgbRandom();
          swayLeft(hiro, 2);
          Serial.println("case10");          
          break;
        case 00:
          rgbRandom();
          neutralStance(hiro);
          Serial.println("case0");
          break;
        case 11:
          rgbRandom();
          sideToSideWorm(hiro, 2);
          Serial.println("both hands");
          break;
        default:
          neutralStance(hiro);
          Serial.println("default");
          break;
      }
    }
  }else{
    neutralStance(hiro);
  }
}

void rgbRandom(){
  analogWrite(hiro.red, random(0,10));
  analogWrite(hiro.green, random(0,10));
  analogWrite(hiro.blue, random(0,10));
}

