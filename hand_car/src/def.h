#ifndef DEF_H
#define DEF_H

enum MotorPin{
  MOTR_SLEEP, MOTR_FL1, MOTR_FL2, MOTR_BL1, MOTR_BL2, MOTR_BR1, MOTR_BR2,
  MOTR_FR1, MOTR_FR2, MOTR_PIN_COUNT
}; 

const int motor_pins[] = {36, 11, 10, 8, 9, 7, 6, 5, 4};
const int num_motors = 4;

void AvanceFD(int speed);
void StopBrake();
void turnRight(int speed);
void turnLeft(int speed);
void goBack(int speed);

#endif