/*
 * roomba_extra.cpp
 *
 *  Created on: 9-Jun-2010
 *      Author: nrqm
 */

#include <avr/io.h>
#include <stdlib.h>
#include "arduino/WProgram.h"
#include "roomba/roomba.h"

// Roomba Defs -- Probably want to move these...
#define DRIVE_SPEED		250 // How fast the Roomba moves mm/sec
#define TURN_SPEED		100
#define MOVE_STRAIGHT	32768 // The straight angle in the Roomba Spec
#define MOVE_LEFT		1 // The left angle in Roomba Spec
#define MOVE_RIGHT		-1 // The right angle in Roomba Spec

roomba_sensor_data_t roomba_sensors;

void rotate_roomba(int16_t angle)
{
	// Get Angle Sensor / Reset Angle Sensor
	Roomba_UpdateSensorPacket(CHASSIS_SENSORS, &roomba_sensors);
	Roomba_ResetTotalAngle();

	if (angle < 0){ Roomba_Drive(TURN_SPEED, MOVE_RIGHT); }
	else if (angle > 0){ Roomba_Drive(TURN_SPEED, MOVE_LEFT); }
	else return;

	// TODO: May need to change this so it stops within a certain error.
	// Example: Desired Angle 33 -- it reads 32. Currently, it will not stop.
	while (abs(Roomba_GetTotalAngle()) < abs(angle) && abs(angle - Roomba_GetTotalAngle()) > 2)
	{
		if((abs(angle) - abs(Roomba_GetTotalAngle())) < 7)
		{
			delay(25);
		}
		else
		{
			delay(100);
		}

		Roomba_UpdateSensorPacket(CHASSIS_SENSORS, &roomba_sensors);
	}
}

// Drive Straight
void translate_roomba(int16_t distance)
{
	// Get Angle Sensor / Reset Angle Sensor
	Roomba_UpdateSensorPacket(CHASSIS_SENSORS, &roomba_sensors);
	Roomba_ResetTotalDistance();

	if (distance < 0){ Roomba_Drive(DRIVE_SPEED * -1, MOVE_STRAIGHT); }
	else if (distance > 0){ Roomba_Drive(DRIVE_SPEED, MOVE_STRAIGHT); }
	else return;

	// TODO: May need to change this so it stops within a certain error.
	// Example: Desired Distance 432 -- it reads 431. Currently, it will not stop.
	while (abs(Roomba_GetTotalDistance()) < abs(distance))
	{
		delay(25);
		Roomba_UpdateSensorPacket(CHASSIS_SENSORS, &roomba_sensors);
	}
	Roomba_Drive(0, 0); // Stop
}
