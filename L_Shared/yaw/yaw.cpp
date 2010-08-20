/*
 * yaw.cpp
 *
 *  Created on: 17-Aug-2010
 *      Author: nrqm
 *
 *  Interface code for using the IDG-300Q dual-axis gyro sensor.
 *
 *  We use the following circuit for the device:
 *
 *                                     |----------- GND
 *                              10 uF ===
 * ------------                        |        1 kOhm
 * |      ADC0|----------------------------------vvvv-----
 * |      Aref|------------------------------            |
 * |          |                             |            |    ------------------
 * |          |             --------------  | +3.3 V     -----|X-rate out      |
 * |      +5 V|-------------| LM1086-3.3 |--------------------|Vcc             |
 * |          |          |  --------------             |   ---|GND             |
 * |          |   10 uF ===       |             10 uF ===  |  |    IDG-300Q    |
 * |          |          |        |                    |   |  ------------------
 * |       GND|---------------------------------------------
 * ------------
 *
 * The X-rot output is put through a passive low-pass filter with a corner around 16 Hz.  The sensor supports an
 * output frequency around 140 Hz, but 16 Hz is sufficient for our purposes.  The circuit could be improved by
 * using a regulator with better noise rejection and an instrumentation amplifier for the filter, but this works
 * okay (the sensor's output impedance is 100 ohms, so the circuit's output impedance is 1.1 kOhms, which is fine).
 */

#include "yaw.h"
#include <avr/io.h>
#include <avr/interrupt.h>

// TIMER_PERIOD is the number of timer cycles between timer ticks.  The timer runs at 250 kHz (fck/64),
// so 250 ticks will take 1 ms.  This means that the yaw sensor output is sampled at a frequency of 1 kHz,
// which is excessive considering that its filter has a corner frequency of 16 Hz.  However, because the
// sensor output is unamplified, it needs to be sampled often in order to increase the software sensitivity
// of the accumulator.   For example, if it samples at 1000 Hz then a 90 degree turn may produce an accumulator
// value around 13000 (this value depends on several factors and might not be correct); thus to obtain a
// reading in degrees you divide the accumulator by 145.  If it samples at 100 Hz then a 90 degree turn would
// correspond to an accumulator value around 1300.  You can't divide the accumulator by 14.5, you'd have to
// divide by 14 or 15 and lose the extra .5 of precision.
//
// So anyway, we could make the system more sensitive to small yaw rates by sampling at 100 Hz and applying a
// gain to the ADC input.  That is, if we wanted to mess around with op-amps or differential inputs and DC
// blocking, which I don't.
#define TIMER_PERIOD 250

// The accumulator is divided by this value to produce a value in degrees.
#define DEGREE_CONVERSION_FACTOR 145

// the minimum number of matching readings for calibration
#define MIN_SUCCESSFUL_CALIBRATIONS 5

volatile YAW_SYSTEM_STATE state = YAW_IDLE;
volatile uint8_t successful_calibrations = 0;
volatile uint8_t adj = 0;
volatile int16_t accumulator = 0;

void Yaw_Init()
{
	// select Aref as reference, enable left-adjust, and set MUX to channel 0.
	ADMUX = _BV(ADLAR);
	// enable ADC; enable auto-trigger, enable interrupt, set prescaler to fck/128 (125 kHz at 16 MHz clock)
	ADCSRA = _BV(ADEN) | _BV(ADATE) | _BV(ADIE) | _BV(ADPS2) | _BV(ADPS1) | _BV(ADPS0);
	// auto-trigger on timer 1B compare match
	ADCSRB = _BV(ADTS2) | _BV(ADTS0);
	// disable digital input pin corresponding to ADC0.
	DIDR0 = _BV(ADC0D);

	// This enables timer 1B running at fck/64 with the compare match interrupt triggering every 1 ms.
	// The compare match triggers the ADC, so the interrupt is not enabled (it is handled in ADC_vect).
	// The sonar module also uses timer 1, so if you change this configuration make sure that the
	// change won't affect the sonar.
	TCCR1A = 0;
	OCR1B = TIMER_PERIOD;
	TCNT1 = 0;
	TCCR1B = _BV(CS11) | _BV(CS10);		// start running timer at 250 kHz (16 MHz base).
}

void Yaw_StartAccumulating()
{
	if (state == YAW_IDLE)
	{
		state = YAW_CALIBRATING;
	}
	else
	{
		// error?  Or maybe just always move the state to CALIBRATING?  Whatever.
	}
}

void Yaw_WaitForCalibration()
{
	while (state == YAW_CALIBRATING);
}

YAW_SYSTEM_STATE Yaw_GetState()
{
	return state;
}

int16_t Yaw_GetDegrees()
{
	// TODO: This algorithm could use some tuning, especially for small angles.
	return accumulator / DEGREE_CONVERSION_FACTOR;
}

int16_t Yaw_StopAccumulating()
{
	state = YAW_IDLE;
	return Yaw_GetDegrees();
}

void Yaw_ResetAccumulator()
{
	accumulator = 0;
}

// This interrupt is triggered when an ADC conversion completes.  The conversion is started by the
// timer 1B interrupt (which does not have a handler, so it is maintained in this handler).  If the
// system is in the CALIBRATING or ACCUMULATING states then the conversion result is applied respectively
// to the adjust variable or the accumulator, otherwise it is ignored.
ISR(ADC_vect)
{
	uint8_t adj_temp;
	// timer maintenance: clear timer interrupt flag and set next interrupt time for 1 ms hence
	TIFR1 = _BV(OCF1B);
	OCR1B += TIMER_PERIOD;

	// the calibration routine takes samples until 5 in a row are equal
	if (state == YAW_CALIBRATING)
	{
		adj_temp = ADCH;
		if (adj_temp == adj)
		{
			successful_calibrations++;
		}
		else
		{
			successful_calibrations = 0;
		}
		adj = adj_temp;
		if (successful_calibrations == MIN_SUCCESSFUL_CALIBRATIONS)
		{
			// adj will now hold the value representing 0 deg/s
			state = YAW_ACCUMULATING;
			successful_calibrations = 0;
		}
	}
	else if (state == YAW_ACCUMULATING)
	{
		accumulator += ADCH;
		accumulator -= adj;
	}
	else
	{
		// ignore conversion in other states
	}
}
