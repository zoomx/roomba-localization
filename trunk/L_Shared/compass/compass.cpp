/*
 * compass.cpp
 *
 *  Created on: 6-Jul-2010
 *      Author: nrqm
 *
 * This code owes a lot to http://www.arduino.cc/playground/Learning/Hmc6352 .
 */

#include "compass.h"
#include "../arduino/WProgram.h"
#include "../arduino/Wire.h"
//#include "../roomba/roomba.h"

#define ADDRESS (0x42 >> 1)

void send_command(const char* command)
{
	Wire.beginTransmission(ADDRESS);
	Wire.send((char*)command);
	Wire.endTransmission();
}

void Compass_Init()
{
	Wire.begin();
}

void Compass_Calibrate()
{
	send_command("C");
	delay(20000);
	send_command("E");
	delay(15);
}

uint16_t Compass_GetReading()
{
	uint8_t i;
	uint16_t headingValue;
	uint8_t headingData[2];
	// send "get data" command and wait for at least 6 ms
	send_command("A");
	delay(10);

	i = 0;
	Wire.requestFrom(ADDRESS, 2);        // Request the 2 byte heading (MSB comes first)
	// nrqm - I think this loop is bad, should be replaced
	while(Wire.available() && i < 2)
	{
		headingData[i] = Wire.receive();
		i++;
	}
	headingValue = headingData[0]*256 + headingData[1];
	return headingValue;
}
