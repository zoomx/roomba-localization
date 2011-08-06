/*
 * sonar.cpp
 *
 *  Created on: 1-Jun-2010
 *      Author: nrqm
 */

#include "sonar.h"

#define SONAR_PIN 6


void Sonar_Init()
{
	pinMode(SONAR_PIN, OUTPUT);
	digitalWrite(SONAR_PIN, LOW);
}
void Sonar_PreTrigger()
{
	// This starts the trigger pulse, which must last at least 10 us.
	pinMode(SONAR_PIN, OUTPUT);
	digitalWrite(SONAR_PIN, HIGH);
}

void Sonar_Trigger()
{
	// This ends the trigger pulse started in Sonar_PreTrigger().
	digitalWrite(SONAR_PIN, LOW);

	pinMode(SONAR_PIN, INPUT);
}
