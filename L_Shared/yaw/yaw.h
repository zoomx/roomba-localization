/*
 * yaw.h
 *
 *  Created on: 17-Aug-2010
 *      Author: nrqm
 */

#include <avr/io.h>

#ifndef YAW_H_
#define YAW_H_

typedef enum _yss
{
	YAW_IDLE,
	YAW_CALIBRATING,
	YAW_ACCUMULATING,
} YAW_SYSTEM_STATE;

/**
 * Initialize the analog-digital converter and timer 1.
 *
 * This driver assumes that nothing else configures the ADC.  It matches the configuration of timer 1
 * used in sonar.cpp, but if something else uses timer 1 or the ADC then it might interfere with this code.
 */
void Yaw_Init();

/**
 * Re-calibrate the input and start accumulating.  The sensor must not be rotating when this is called, and
 * it should not start rotating until the calibration is complete (use Yaw_GetState or Yaw_WaitForCalibration
 * to wait for the calibration routine to finish).
 */
void Yaw_StartAccumulating();

/**
 * Get the current state of the yaw sensor driver.  The state may be idle, calibrating, or accumulating.
 *   * In idle mode, the driver ignores values read from the yaw sensor.
 *   * In calibration mode, the driver calculates the ADC value corresponding to a rotation of 0 deg/s
 *   * In accumulating mode, the driver accumulates values read from the yaw sensor.
 */
YAW_SYSTEM_STATE Yaw_GetState();

/**
 * Block while the driver is in the YAW_CALIBRATING state.  If the state is YAW_IDLE or YAW_ACCUMULATING
 * then this function returns immediately.  For a non-blocking way of doing this, poll the Yaw_GetState
 * function.
 */
void Yaw_WaitForCalibration();

/**
 * Get the number of degrees that have been accumulated.  The maximum value is +/- 225 degrees (at which
 * points the accumulator will overflow or underflow).
 */
int16_t Yaw_GetDegrees();

/**
 * Change the driver state from YAW_ACCUMULATING to YAW_IDLE.  Returns the same thing as Yaw_GetDegrees.
 * The accumulator will not be zeroed, so calling Yaw_StartAccumulating again after calling
 * Yaw_StopAccumulating will resume from the previous accumulator value.  Use Yaw_ResetAccumulator to
 * zero the accumulator.
 */
int16_t Yaw_StopAccumulating();

/**
 * Set the accumulator to 0 degrees.
 */
void Yaw_ResetAccumulator();


#endif /* YAW_H_ */
