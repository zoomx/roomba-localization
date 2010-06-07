/*
 * roomba_sci.h
 *
 *  Created on: 17-May-2009
 *      Author: nrqm
 */

#ifndef ROOMBA_SCI_H_
#define ROOMBA_SCI_H_

/*****											Commands										*****/

#define START	128		// start the Roomba's serial command interface
#define BAUD	129		// set the SCI's baudrate (default on full power cycle is 57600
#define CONTROL	130		// enable control via SCI
#define SAFE	131		// enter safe mode
#define FULL	132		// enter full mode
#define POWER	133		// put the Roomba to sleep
#define SPOT	134		// start spot cleaning cycle
#define CLEAN	135		// start normal cleaning cycle
#define MAX		136		// start maximum time cleaning cycle
#define DRIVE	137		// control wheels
#define MOTORS	138		// turn cleaning motors on or off
#define LEDS	139		// activate LEDs
#define SONG	140		// load a song into memory
#define PLAY	141		// play a song that was loaded using SONG
#define SENSORS	142		// retrieve one of the sensor packets
#define DOCK	143		// force the Roomba to seek its dock.

/*****											Arguments										*****/

/// Arguments to the BAUD command
typedef enum _br {
	ROOMBA_300BPS = 0,
	ROOMBA_600BPS = 1,
	ROOMBA_1200BPS = 2,
	ROOMBA_2400BPS = 3,
	ROOMBA_4800BPS = 4,
	ROOMBA_9600BPS = 5,
	ROOMBA_14400BPS = 6,
	ROOMBA_19200BPS = 7,
	ROOMBA_28800BPS = 8,
	ROOMBA_38400BPS = 9,
	ROOMBA_57600BPS = 10,
	ROOMBA_115200BPS = 11,
} ROOMBA_BITRATE;

/// Bits in the MOTORS command argument
#define MAIN_BRUSH	2
#define VACUUM		1
#define SIDE_BRUSH	0

typedef enum _vacuum
{
	VACUUM_OFF,
	VACUUM_ON,
} VACUUM_STATE;

/// Bits in the first byte to the LEDS command
#define STATUS_GREEN	5	// The status LED is 2 bits:
#define	STATUS_RED		4	// 00 for off, 01 for red, 10 for green, 11 for amber (red + green)
#define SPOT_LED		3
#define CLEAN_LED		2
#define MAX_LED			1
#define DIRT_DETECT		0

typedef enum _led
{
	LED_OFF,
	LED_ON,
} LED_STATE;

typedef enum _sled
{
	STATUS_LED_OFF,
	RED,
	GREEN,
	AMBER,
} STATUS_LED_STATE;

/*****											Sensor Bits										*****/

/// Bits in the Bumps/Wheeldrops byte
#define WHEELDROP_CASTER	4
#define WHEELDROP_LEFT		3
#define WHEELDROP_RIGHT		2
#define BUMP_LEFT			1
#define BUMP_RIGHT			0

/// Bits in the motor overcurrents byte
#define DRIVE_LEFT		4
#define DRIVE_RIGHT		3
#define MAIN_BRUSH_OC	2
#define VACUUM_OC		1
#define SIDE_BRUSH_OC	0

/// Bits in the buttons byte
#define POWER_BTN 		3
#define SPOT_BTN		2
#define CLEAN_BTN		1
#define MAX_BTN			0

/// Values of the charging state byte
typedef enum _cs
{
	NOT_CHARGING = 0,
	CHARGING_RECOVERY = 1,
	CHARGING = 2,
	TRICKLE_CHARGING = 3,
	WAITING = 4,
	CHARGING_ERROR = 5,
} ROOMBA_CHARGING_STATE;






#endif /* ROOMBA_SCI_H_ */
