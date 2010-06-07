#ifndef ROOMBA_H_
#define ROOMBA_H_

#include <stdio.h>
#include "roomba_sci.h"
#include "sensor_struct.h"

typedef enum _rsg
{
        EXTERNAL_SENSORS=1,             // group 1 (bumper/wheeldrops, cliff sensors, virtual wall, motor overcurrents, dirt sensors)
        CHASSIS_SENSORS=2,              // group 2 (remote, buttons, distance, angle)
        INTERNAL_SENSORS=3,             // group 3 (charging state; battery voltage, current, charge and capacity; internal temperature)
} ROOMBA_SENSOR_GROUP;

typedef enum _rstate
{
	PASSIVE_MODE,
	SAFE_MODE,
	FULL_MODE,
} ROOMBA_STATE;

/**
 * Turn on the Roomba with the serial port DD pin, configure the SCI to operate at 38400 baud, put the Roomba into safe mode,
 * and configure the LEDs to their default values.
 */
void Roomba_Init(uint8_t);

/**
 * Retrieve a section of the Roomba's sensor data and copy it into a sensor packet structure.
 *
 * There are three sensor packet groups:
 * 		Group 1: Environment sensors (bumper, wheeldrops, wall sensor, cliff detect, virtual wall, motor overcurrents, dirt detect)
 * 		Group 2: Chassis sensors (remote control, chassis button states, distance sensor, angle sensor)
 * 		Group 3: Internal sensors (charging state, battery voltage, current draw, temperature, battery charge, battery capacity)
 *
 * If the distance and/or angle sensors are being used, then the sensor packet's distance/angle values must be processed every time
 * group 2 is updated.  This is because the Roomba sets the sensor values back to 0 every time group 2 is read, so that the next time
 * group 2 is read the value copied into the packet structure will not include the data from the last update.  Updating groups 1
 * and 3 do not affect the distance and angle sensor values stored in the Roomba, nor do they change the values in the sensor packet
 * structure.  The following code sample will cause the Roomba to travel around 1 m forward then 1 m backward:
 *
 * 		roomba_sensor_packet_t sensors;
 * 		int16_t total_distance = 0;
 * 		Roomba_Drive(200, 0x8000);
 * 		while (total_distance < 1000)
 * 		{
 * 			Roomba_UpdateSensorPacket(CHASSIS, &sensors);
 * 			total_distance += sensors.distance.value;
 * 			_delay_ms(100);	// polling too often results in significant error accumulation, but we don't want to overshoot too much
 * 		}
 * 		Roomba_Drive(-200, 0x8000);		// reverse direction
 * 		total_distance = 0;				// reset the total distance; going backwards ==> negative distance
 * 		while (total_distance > -1000)
 * 		{
 * 			Roomba_UpdateSensorPacket(CHASSIS, &sensors);
 * 			total_distance += sensors.distance.value;
 * 			_delay_ms(100);
 * 		}
 * 		Roomba_Drive(0, 0);
 *
 * The distance and angle sensors are not very accurate.
 *
 * The three sensor packet groups are respectively 10 bytes, 6 bytes, and 10 bytes in length.  At 38400 baud, it takes 0.5 ms to transfer
 * the two bytes to request a sensor group update.  It takes an additional 2.6 ms to download a 10 byte group, and 1.6 ms to download the
 * 6-byte group.  If you're using the RTOS, I recommend that you not overrun the 5 ms tick length in this function because a sensor byte
 * might be skipped by the UART driver while the kernel is executing (in which case this function will enter an infinite loop).  It's safe
 * to update one group per tick.  Updating more than one group takes at least 5.2 ms, so it's impossible to update two or three groups
 * in the same tick without modifying the definition of this function.
 */
void Roomba_UpdateSensorPacket(ROOMBA_SENSOR_GROUP group, roomba_sensor_data_t* sensor_packet);

/**
 * Command the Roomba to move.
 * \param velocity The velocity is measured in mm/s, and can range from -500 to 500.  A negative velocity means that the Roomba moves
 * 		backward.
 * \param radius The radius of the circle that the Roomba drives, measured in mm.  This can range from -2000 to 2000.  When the Roomba
 * 		is moving forward, a positive radius causes it to turn left and a negative radius causes it to turn right.  There are three
 * 		special cases for the radius value:
 *
 * 			0x8000		Move straight
 * 			-1			Turn in place clockwise
 * 			1			Turn in place counter-clockwise
 *
 * 		The Roomba isn't actually able to move perfectly straight, even with an angle value of 0x8000.  It generally drifts to the left
 * 		at a rate of several inches of error per metre travelled.  There is no way to drive the Roomba perfectly straight without using
 * 		a control loop on the controller and an external angle sensor (such as a compass or accelerometer) to provide feedback.
 */
void Roomba_Drive( int16_t velocity, int16_t radius );

/**
 * Change the Roomba's state to passive mode, safe mode, or full mode.  The Roomba_Init function puts the Roomba into safe mode.
 * If the Roomba is already in the state requested, then nothing will happen.  Otherwise, the Roomba will be put in the new state and
 * a 20 ms delay will be executed (per the SCI specification).
 *
 * If the Roomba is in safe mode, then it puts itself in passive mode when its cliff sensors or wheeldrop sensors are triggered.
 * There's no way to obtain the Roomba's mode programmatically, but this function should not be affected by unexpected mode changes.
 */
void Roomba_ChangeState(ROOMBA_STATE newState);

/**
 * Configure the power LED to use the given colour and intensity.
 *
 * \param colour Green is 0x00, red is 0xFF, and the values from 0x01 to 0xFE are a corresponding mix of red and green.
 * \param intensity The brightness of the power LED (0 is off, 0xFF is full brightness).
 */
void Roomba_ConfigPowerLED(uint8_t colour, uint8_t intensity);

/**
 * The status LED can be off, red, green, or amber.  The "LED" is actually made up of two LEDs, which produce an amber colour when
 * turned on at the same time.
 */
void Roomba_ConfigStatusLED(STATUS_LED_STATE state);

/**
 * The LED on the Spot cleaning button can be turned on or off.
 */
void Roomba_ConfigSpotLED(LED_STATE state);

/**
 * The LED on the Clean cleaning button can be turned on or off.
 */
void Roomba_ConfigCleanLED(LED_STATE state);

/**
 * The LED on the Max cleaning button can be turned on or off.
 */
void Roomba_ConfigMaxLED(LED_STATE state);

/**
 * The bright blue dirt detect LED can be turned on or off.
 */
void Roomba_ConfigDirtDetectLED(LED_STATE state);

/**
 * Program one of the Roomba's 16 songs.  Songs are a sequence of up to 16 notes mapped to a corresponding number of durations.
 * When a song is loaded into a slot, it remains in that slot until a new song is loaded into the slot or the Roomba's battery
 * is removed.
 *
 * \param songNum The number of the song to program (0 to 15)
 * \param notes An array of numNotes note values.  Valid values for notes are the same as those used in the MIDI protocol
 * 		(e.g. 60 for middle C, 69 for A440, etc.).  Notes can range from 31 (49 Hz G) to 127 (12543.9 Hz G).  Any note value
 * 		not within this range is interpreted as a rest (i.e. no note is played).
 * \param durations An array of durations corresponding to the notes in the "notes" array.  Durations are in 64ths of a second.
 * 		For example, if the first index of the "notes" array is 60 and the first index of the "durations" array is 32, then the
 * 		Roomba will play a middle C for around half a second.
 * \param numNotes The length of the "notes" and "notelengths" arrays.  The arrays must be the same length.
 */
void Roomba_LoadSong(uint8_t songNum, uint8_t* notes, uint8_t* durations, uint8_t numNotes);

/**
 * Play one of the songs that have been loaded onto the Roomba using Roomba_LoadSong.  When a song is played each note in the song
 * is separated by a very short gap.  But the duration of the note is a little shorter than specified, so often a song is shorter
 * than it theoretically should be.  For example, the following "notelengths" array is defined as follows:
 *
 * 		uint8_t durations[16] = {32,  64,  16, 16, 64,  16, 16, 64,  16, 16, 64, 16, 16, 64, 16, 16};
 *
 * then it should last for 8 seconds, but it actually lasts for 7.87 seconds.  If you want to concatenate two songs to make a
 * song that lasts for more than 16 notes, then you will have to manually tune the timing so that the second song starts less than
 * 10 ms after the first song ends.  If the SONG command is sent for the second song before the first song ends, then the second
 * song does not get played.  There is no way to determine if the Roomba is currently playing a song with the SCI.  Another
 * approach would be to use an external sensor to detect the ending of a song.
 */
void Roomba_PlaySong(int songNum);

/**
 * Flash the LEDs and move a bit to verify that the Roomba's working properly.
 */
void Roomba_Workout();

/**
 * Returns the total distance since roomba_ResetTotalDistance was last called.
 */
int16_t Roomba_GetTotalDistance();

/**
 * Resets the total distance traveled by the roomba.
 */
void Roomba_ResetTotalDistance();

/**
 * Returns the total angles since roomba_ResetTotalAngle was last called.
 */
int16_t Roomba_GetTotalAngle();

/**
 * Resets the total angle traveled by the roomba.
 */
void Roomba_ResetTotalAngle();

void Roomba_ForceSeekingDock();

#endif /* ROOMBA_H_ */
