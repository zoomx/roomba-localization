/*
 * compass.h
 *
 *  Created on: 6-Jul-2010
 *      Author: nrqm
 */

#ifndef COMPASS_H_
#define COMPASS_H_

#include <avr/io.h>

/**
 * Initialize the compass unit and start the TWI module
 */
void Compass_Init();

/**
 * Calibrate the compass.  This function puts the compass into calibration mode, waits for 20 seconds,
 * exits calibration mode, and waits for another 15 ms.  The calibration routine requires that the
 * compass be held flat while rotating (the datasheet suggests 2 full rotations in 20 seconds).  As such,
 * the compass must start rotating in place before this function is called.
 *
 * The calibration routine corrects for hard iron distortions in the magnetic field.  The calibration
 * results are stored in EEPROM.  Therefore this routine only needs to be run when the hard iron distortion
 * (e.g. from pieces of ferromagnetic or magnetic material) placed at a constant position relative to the
 * compass changes.
 */
void Compass_Calibrate();

/**
 * Query the compass for a reading.  This function includes a 10 ms delay.  It returns a number from 0 to
 * 3599, representing the compass's orientation clockwise from magnetic north, in increments of 0.1 degree.
 * In other words, the range is 0 to 359.9 degrees.
 */
uint16_t Compass_GetReading();

#endif /* COMPASS_H_ */
