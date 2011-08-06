/*
 * sonar.h
 *
 *  Created on: 1-Jun-2010
 *      Author: nrqm
 */
#include "../arduino/WProgram.h"

#ifndef SONAR_H_
#define SONAR_H_

/**
 * This module provides programmatic access to the Seeed Studio ultrasonic ranger.
 * It assumes the following wiring on the Arduion Pro Mini:
 *
 *     Sonar                Arduino        Arduino Mega
 *
 * 		Vcc ----------------- +5V             +5V
 *   Signal ----------------- Pin 8          Pin 48
 *      GND ----------------- GND             GND
 *
 */

/**
 * Initialise the trigger pin and the input capture timer.
 *
 * This must be called after the Arduino init() function or else init() will clobber our timer settings.
 */
void Sonar_Init();

/**
 * Set the sonar trigger pin high, and initialise the driver's state.  The sonar will not be triggered
 * until Sonar_Trigger() is called.
 */
void Sonar_PreTrigger();

/**
 * Pull the sonar trigger pin low, which triggers an echo pulse on the sonar.  Sonar_PreTrigger() must be
 * called at least 10 microseconds before Sonar_Trigger().
 */
void Sonar_Trigger();

/**
 * Get the last distance measured by the sonar.
 * This should be called after the pulse-end callback sonar_pulseend_cb has been asserted by the sonar module.
 * The distance calculation takes a long time, so this should not be called within the callback.
 */
uint16_t Sonar_GetDistance(int8_t error_in_cm);


#endif /* SONAR_H_ */
