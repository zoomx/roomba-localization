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
 * This module provides programmatic access to the SRF04 ultrasonic ranger.  It assumes the following
 * wiring:
 *
 *     Sonar                Seeeduino
 *
 * 		Vcc ----------------- +5V
 *   Output ----------------- PD4
 *  Trigger ----------------- Arduino pin 10 (PB4)
 *     (NC) -----------------
 *      GND ----------------- GND
 *
 * An Arduino pin number is not assigned to PD4, it is labelled "PD4" on the Seeeduino headers.
 */

typedef enum _ss
{
	IDLE,
	WAITING_FOR_PULSE_START,	/// Trigger has been sent to sonar
	WAITING_FOR_PULSE_END,		/// Sonar echo pulse has started, waiting for falling edge
	OUTPUT_READY,				/// Echo pulse is done, ready to log results.
} SONAR_STATE;

/**
 * Initialise the trigger pin and the input capture timer.
 *
 * This must be called after the Arduino init() function or else init() will clobber the timer settings.
 */
void Sonar_Init();

/**
 * Set the sonar trigger pin high, and initialise the driver's state.  The sonar will not be triggered
 * until Sonar_Trigger() is called.  After this is called Sonar_GetState() will return something
 * other than OUTPUT_READY.
 */
void Sonar_PreTrigger();

/**
 * Pull the sonar trigger pin low, which triggers an echo pulse on the sonar.  Sonar_PreTrigger() must be
 * called at least 10 microseconds before Sonar_Trigger().
 */
void Sonar_Trigger();

/**
 * Get the current state of the sonar driver (see SONAR_STATE enumeration).
 */
SONAR_STATE Sonar_GetState();

/**
 * Get the distance measured by the sonar.  If the sonar is currently measuring a signal (i.e. Sonar_GetState()
 * returns something other than OUTPUT_READY) then Sonar_GetDistance() returns 0.
 */
uint16_t Sonar_GetDistance(int8_t error_in_cm);


#endif /* SONAR_H_ */
