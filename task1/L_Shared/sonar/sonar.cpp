/*
 * sonar.cpp
 *
 *  Created on: 1-Jun-2010
 *      Author: nrqm
 */

#include "sonar.h"

/// Set input capture 1 to trigger when it detects a rising edge on PD4
#define ICP1_DETECT_RISING_EDGE() ((TCCR1B |= _BV(ICES1)))
/// Set input capture 1 to trigger when it detects a falling edge on PD4
#define ICP1_DETECT_FALLING_EDGE() ((TCCR1B &= ~_BV(ICES1)))

#define SONAR_PIN 10	// arbitrary I/O pin

volatile SONAR_STATE sonar_state = WAITING_FOR_PULSE_START;

volatile uint16_t pulse_start = 0;	// ICR1 copied in here on rising edge
volatile uint16_t pulse_end = 0;	// ICR1 copied in here on falling edge

void Sonar_Init()
{
	pinMode(SONAR_PIN, OUTPUT);
	digitalWrite(SONAR_PIN, LOW);

	// configure timer 1 for input capture (overwrites Arduino default setting)
	TCCR1A = 0;
	TIMSK1 = _BV(ICIE1);				// enable ICP1 interrupt (on pin PD4)
	TCNT1 = 0;
	TCCR1B = _BV(CS11) | _BV(CS10);		// start running timer at 250 kHz (16 MHz base).
}
void Sonar_PreTrigger()
{
	// This starts the trigger pulse, which must last at least 10 us.
	digitalWrite(SONAR_PIN, HIGH);
	sonar_state = WAITING_FOR_PULSE_START;
	ICP1_DETECT_RISING_EDGE();
}

void Sonar_Trigger()
{
	// This ends the trigger pulse started in Sonar_PreTrigger().
	digitalWrite(SONAR_PIN, LOW);
}

SONAR_STATE Sonar_GetState()
{
	return sonar_state;
}

uint16_t Sonar_GetDistance(int8_t error_in_cm)
{
	// distance calculation will overflow a 16-bit integer, but the result fits in 16 bits.
	static uint32_t distance = 0;
	if (sonar_state == OUTPUT_READY)
	{
		sonar_state = IDLE;
		distance = 34317;						// speed of sound in cm/s
		distance *= (pulse_end - pulse_start);	// pulse time in ticks
		distance /= 250000;						// ticks per second
		distance += error_in_cm;				// expected error, in cm
		return (uint16_t)distance;
	}
	else
	{
		return 0;
	}
}


ISR(TIMER1_CAPT_vect)
{
	if (sonar_state == WAITING_FOR_PULSE_START)
	{
		// Received a rising edge, the start of the echo pulse
		pulse_start = ICR1;
		// set ICP1 to trigger again on falling edge
		ICP1_DETECT_FALLING_EDGE();
		sonar_state = WAITING_FOR_PULSE_END;
		digitalWrite(13, HIGH);
	}
	else if (sonar_state == WAITING_FOR_PULSE_END)
	{
		// Received a falling edge, the end of the echo pulse
		pulse_end = ICR1;
		// next time ICP1 is needed it will be to detect a rising edge
		ICP1_DETECT_RISING_EDGE();
		sonar_state = OUTPUT_READY;
		digitalWrite(13, LOW);
	}
}
