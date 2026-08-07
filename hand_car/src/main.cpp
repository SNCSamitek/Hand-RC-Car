#include <Arduino.h>
#include "def.h"

void setup() {
  Serial1.begin(9600);
  for(int i = 0; i < MOTR_PIN_COUNT; i++)
    pinMode(motor_pins[i], OUTPUT);
  digitalWrite(motor_pins[MOTR_SLEEP], HIGH);
}

void loop() {
  if(Serial1.available() > 0){
    String cmd = Serial1.readStringUntil('\n');
    cmd.trim();

  if(cmd == "forward") AvanceFD(90);
  else if(cmd == "right") turnRight(90);
  else if(cmd == "left") turnLeft(90);
  else if (cmd == "back") goBack(90);
  else StopBrake();
  }
}

void AvanceFD(int speed){
  int pin_tracker = 1;
  for(int i = 0; i < num_motors; i++){
    digitalWrite(motor_pins[pin_tracker], LOW);
    analogWrite(motor_pins[pin_tracker+1], speed);
    pin_tracker += 2;
  }
}

void goBack(int speed){
  int pin_tracker = 1;
  for(int i = 0; i < num_motors; i++){
    digitalWrite(motor_pins[pin_tracker], HIGH);
    analogWrite(motor_pins[pin_tracker+1], speed);
    pin_tracker += 2;
  }
}

void turnLeft(int speed){
  analogWrite(motor_pins[MOTR_FL1], speed); 
  digitalWrite(motor_pins[MOTR_FL2], LOW);  // 
  analogWrite(motor_pins[MOTR_BL1], speed);    
  digitalWrite(motor_pins[MOTR_BL2], LOW);  // 
  
  digitalWrite(motor_pins[MOTR_BR1], LOW);  // 
  analogWrite(motor_pins[MOTR_BR2], speed); 
  digitalWrite(motor_pins[MOTR_FR1], LOW);  // 
  analogWrite(motor_pins[MOTR_FR2], speed); 
}


void turnRight(int speed){
  digitalWrite(motor_pins[MOTR_FL1], LOW); 
  analogWrite(motor_pins[MOTR_FL2], speed);  // 
  digitalWrite(motor_pins[MOTR_BL1], LOW);    
  analogWrite(motor_pins[MOTR_BL2], speed);  // 
  
  analogWrite(motor_pins[MOTR_BR1], speed);  // 
  digitalWrite(motor_pins[MOTR_BR2], LOW); 
  analogWrite(motor_pins[MOTR_FR1], speed);  // 
  digitalWrite(motor_pins[MOTR_FR2], LOW); 
}

void StopBrake(){
  for(int i = 1; i < MOTR_PIN_COUNT; i++)
    digitalWrite(motor_pins[i], HIGH); 
}



