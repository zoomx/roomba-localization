/*
 * roomba.cpp
 *
 *  Created on: 4-Feb-2009
 *      Author: nrqm
 */

#include <util/delay.h>
#include "../arduino/HardwareSerial.h" // Needed for Serial1|2|3
#include "roomba.h"
#include "roomba_sci.h"
#include "sensor_struct.h"

#define LOW_BYTE(v)   ((unsigned char) (v))
#define HIGH_BYTE(v)  ((unsigned char) (((unsigned int) (v)) >> 8))

#define DD_DDR DDRC
#define DD_PORT PORTC
#define DD_PIN PC5

VACUUM_STATE vacuum = VACUUM_OFF;

STATUS_LED_STATE status = STATUS_LED_OFF;
LED_STATE spot = LED_OFF;
LED_STATE clean = LED_OFF;
LED_STATE max = LED_OFF;
LED_STATE dd = LED_OFF;
uint8_t power_colour = 0;		// green
uint8_t power_intensity = 255;	// full intensity

ROOMBA_STATE state = SAFE_MODE;

static int16_t _roomba_distance = 0;
static int16_t _roomba_angle = 0;

static void update_leds();

void Roomba_Init(uint8_t use_DD)
{
	if (use_DD)
	{
		// TODO: Needs to be re-written for Arduino (digital pins)
		/*
		uint8_t i;
		DD_DDR |= _BV(DD_PIN);
		// Wake up the Roomba by driving the DD pin low for 500 ms.
		DD_PORT &= ~_BV(DD_PIN);
		_delay_ms(500);
		DD_PORT |= _BV(DD_PIN);

		// Wait for 2 seconds, Then pulse the DD pin 3 times to set the Roomba to operate at 19200 baud.
		// This ensures that we know what baud rate to talk at.
		_delay_ms(2000);
		for (i = 0; i < 3; i++)
		{
			DD_PORT &= ~_BV(DD_PIN);
			_delay_ms(50);
			DD_PORT |= _BV(DD_PIN);
			_delay_ms(50);
		}
		*/
		Serial1.begin(19200);
	}
	else
	{
		Serial1.begin(57600);
	}
	// start the Roomba's SCI
	Serial1.write(START);
	_delay_ms(20);

	// See the appropriate AVR hardware specification, at the end of the USART section, for a table of baud rate
	// framing error probabilities.  The best we can do with a 16 or 8 MHz crystal is 38400 bps, which has a framing
	// error rate of 0.2% (1 bit out of every 500).  Well, the best is 76800 bps, but the Roomba doesn't support
	// that.  38400 at 0.2% is sufficient for our purposes.  An 18.432 MHz crystal will generate all the Roomba's
	// baud rates with 0.0% error!.  Anyway, the point is we want to use a 38400 bps baud rate to avoid framing
	// errors.  Also, we have to wait for 100 ms after changing the baud rate.
	Serial1.write(BAUD);
	Serial1.write(ROOMBA_38400BPS);
	_delay_ms(100);

	// change the AVR's UART clock to the new baud rate.
	Serial1.begin(38400);

	// start the SCI again in case the first start didn't go through.
	Serial1.write(START);
	_delay_ms(20);

	// put the Roomba into safe mode.
	Serial1.write(CONTROL);
	_delay_ms(20);

	// Set the Roomba's LEDs to the defaults defined above (to verify defaults).
	update_leds();
}

/**
 * Use this function instead of the while loops in Roomba_UpdateSensorPacket if you have a system
 * clock.  This will add a timeout when it's waiting for the bytes to come in, so that the
 * function doesn't enter an infinite loop if a byte is missed.  You'll have to modify this function
 * and insert it into Roomba_UpdateSensorPacket to suit your application.
 */
/*
uint8_t wait_for_bytes(uint8_t num_bytes, uint8_t timeout)
{
	uint16_t start;
	start = Now();	// current system time
	while (Now() - start < timeout && uart_bytes_received() != num_bytes);
	if (uart_bytes_received() >= num_bytes)
		return 1;
	else
		return 0;
}*/

void Roomba_UpdateSensorPacket(ROOMBA_SENSOR_GROUP group, roomba_sensor_data_t* sensor_packet)
{
	// No, I don't feel bad about manual loop unrolling.
	Serial1.write(SENSORS);
	Serial1.write(group);
	switch(group)
	{
	case EXTERNAL_SENSORS:
		// environment sensors
		while (Serial1.available() != 10);
		sensor_packet->bumps_wheeldrops = Serial1.read();
		sensor_packet->wall = Serial1.read();
		sensor_packet->cliff_left = Serial1.read();
		sensor_packet->cliff_front_left = Serial1.read();
		sensor_packet->cliff_front_right = Serial1.read();
		sensor_packet->cliff_right = Serial1.read();
		sensor_packet->virtual_wall = Serial1.read();
		sensor_packet->motor_overcurrents = Serial1.read();
		sensor_packet->dirt_left = Serial1.read();
		sensor_packet->dirt_right = Serial1.read();
		break;
	case CHASSIS_SENSORS:
		// chassis sensors
		while (Serial1.available() != 6);
		sensor_packet->remote_opcode = Serial1.read();
		sensor_packet->buttons = Serial1.read();
		sensor_packet->distance.bytes.high_byte = Serial1.read();
		sensor_packet->distance.bytes.low_byte = Serial1.read();
		sensor_packet->angle.bytes.high_byte = Serial1.read();
		sensor_packet->angle.bytes.low_byte = Serial1.read();
		_roomba_distance += sensor_packet->distance.value;
		_roomba_angle += sensor_packet->angle.value;
		break;
	case INTERNAL_SENSORS:
		// internal sensors
		while (Serial1.available() != 10);
		sensor_packet->charging_state = Serial1.read();
		sensor_packet->voltage.bytes.high_byte = Serial1.read();
		sensor_packet->voltage.bytes.low_byte = Serial1.read();
		sensor_packet->current.bytes.high_byte = Serial1.read();
		sensor_packet->current.bytes.low_byte = Serial1.read();
		sensor_packet->temperature = Serial1.read();
		sensor_packet->charge.bytes.high_byte = Serial1.read();
		sensor_packet->charge.bytes.low_byte = Serial1.read();
		sensor_packet->capacity.bytes.high_byte = Serial1.read();
		sensor_packet->capacity.bytes.low_byte = Serial1.read();
		break;
	}
	//uart_reset_receive();
}

void Roomba_ChangeState(ROOMBA_STATE newState)
{
	if (newState == SAFE_MODE)
	{
		if (state == PASSIVE_MODE)
			Serial1.write(CONTROL);
		else if (state == FULL_MODE)
			Serial1.write(SAFE);
	}
	else if (newState == FULL_MODE)
	{
		Roomba_ChangeState(SAFE_MODE);
		Serial1.write(FULL);
	}
	else if (newState == PASSIVE_MODE)
	{
		Serial1.write(POWER);
	}
	else
	{
		// already in the requested state
		return;
	}

	state = newState;
	_delay_ms(20);
}

void Roomba_Drive( int16_t velocity, int16_t radius )
{
	Serial1.write(DRIVE);
	Serial1.write(HIGH_BYTE(velocity));
	Serial1.write(LOW_BYTE(velocity));
	Serial1.write(HIGH_BYTE(radius));
	Serial1.write(LOW_BYTE(radius));
}

/**
 * Update the LEDs on the Roomba to match the configured state
 */
void update_leds()
{
	// The status, spot, clean, max, and dirt detect LED states are combined in a single byte.
	uint8_t leds = status << 4 | spot << 3 | clean << 2 | max << 1 | dd;

	Serial1.write(LEDS);
	Serial1.write(leds);
	Serial1.write(power_colour);
	Serial1.write(power_intensity);
}

void Roomba_ConfigPowerLED(uint8_t colour, uint8_t intensity)
{
	power_colour = colour;
	power_intensity = intensity;
	update_leds();
}

void Roomba_ConfigStatusLED(STATUS_LED_STATE state)
{
	status = state;
	update_leds();
}

void Roomba_ConfigSpotLED(LED_STATE state)
{
	spot = state;
	update_leds();
}

void Roomba_ConfigCleanLED(LED_STATE state)
{
	clean = state;
	update_leds();
}

void Roomba_ConfigMaxLED(LED_STATE state)
{
	max = state;
	update_leds();
}

void Roomba_ConfigDirtDetectLED(LED_STATE state)
{
	dd = state;
	update_leds();
}

void Roomba_LoadSong(uint8_t songNum, uint8_t* notes, uint8_t* notelengths, uint8_t numNotes)
{
	uint8_t i = 0;

	Serial1.write(SONG);
	Serial1.write(songNum);
	Serial1.write(numNotes);

	for (i=0; i<numNotes; i++)
	{
		Serial1.write(notes[i]);
		Serial1.write(notelengths[i]);
	}
}

void Roomba_PlaySong(int songNum)
{
	Serial1.write(PLAY);
	Serial1.write(songNum);
}

uint8_t Roomba_BumperActivated(roomba_sensor_data_t* sensor_data)
{
	// if either of the bumper bits is set, then return true.
	return (sensor_data->bumps_wheeldrops & 0x03) != 0;
}

/**
 * Returns the total distance since roomba_ResetTotalDistance was last called.
 */
int16_t Roomba_GetTotalDistance()
{
	return _roomba_distance;
}

/**
 * Resets the total distance traveled by the roomba.
 */
void Roomba_ResetTotalDistance()
{
	_roomba_distance = 0;
}

/**
 * Returns the total angles since roomba_ResetTotalAngle was last called.
 */
int16_t Roomba_GetTotalAngle()
{
	// this formula for radians is defined in the Roomba Serial Command
	// Interface (SCI) Specification, page 8.  Might need to look at
	// the formula to deal with overflow.
	return _roomba_angle;//
}

/**
 * Resets the total angle traveled by the roomba.
 */
void Roomba_ResetTotalAngle()
{
	_roomba_angle = 0;
}

void Roomba_ForceSeekingDock()
{
	Serial1.write(DOCK);
}
