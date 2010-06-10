/*
 * explorer.c
 *
 *  Created on: 31-May-2010
 *      Author: nrqm
 */

#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>
#include "arduino/WProgram.h"
#include "radio/radio.h"
#include "radio/packet.h"
#include "roomba/roomba.h"
#include "sonar/sonar.h"

/*
 * In this program the query process is started by the timer, every 1000 ms.  I would propose
 * integrating this with the Roomba something like this:
 *
 * 	infinite loop:
 * 		move_to_a_new_position();
 * 		stop_moving();
 * 		foreach sonar_id:	// iterate through the sonar stations, querying one at a time
 * 			sensor_address[4] = sonar_id;	// sensors share the first four bytes of their addresses
 * 			Sonar_PreTrigger();				//		and the last byte is the sensor's ID
 * 			send_echo_request();
 * 			infinite loop:
 * 				if radio_state == PACKET_READY:
 * 					Sonar_Trigger();
 * 					receive_echo_confirm();		// this is the same as below
 * 				if Sonar_GetState() == OUTPUT_READY:
 * 					record_reading(Sonar_GetDistance());	// store to buffer or log directly
 * 					break;
 *
 */

// millis() returns uint32_t, I prefer working in uint16_t.
#define millis16() ((millis() & 0xFFFF))


// Roomba Defs -- Probably want to move these...
#define DRIVE_SPEED		250 // How fast the Roomba moves mm/sec
#define TURN_SPEED		100
#define MOVE_STRAIGHT	32768 // The straight angle in the Roomba Spec
#define MOVE_LEFT		1 // The left angle in Roomba Spec
#define MOVE_RIGHT		-1 // The right angle in Roomba Spec

void rotate_roomba(int16_t);
void translate_roomba(int16_t);

typedef enum _rs
{
	NO_PACKET,
	PACKET_READY,
	BASE_PACKET_READY,
} RADIO_STATE;

char output[64];

volatile RADIO_STATE radio_state = NO_PACKET;
radiopacket_t packet;

uint8_t explorer_address[RADIO_ADDRESS_LENGTH] = {0xB7, 0xB7, 0xB7, 0xB7, 0xFF};
uint8_t roomba_address[RADIO_ADDRESS_LENGTH] = {0xB4, 0xB4, 0xB4, 0xB4, 0xFF};
uint8_t sensor_address[RADIO_ADDRESS_LENGTH] = {0xB7, 0xB7, 0xB7, 0xB7, 1};
uint8_t base_address[RADIO_ADDRESS_LENGTH] = {0xB4, 0xB4, 0xB4, 0xB4, 1};

roomba_sensor_data_t roomba_sensors;

uint8_t powerPin = 9;
uint8_t ledPin = 13;
#define flipLED() digitalWrite(ledPin, !digitalRead(ledPin));

#define TOTAL_BEACONS	1
int16_t beacon_distances[TOTAL_BEACONS];

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
}

int main()
{
	uint16_t start;
	init();
	cli();

	Serial.begin(100000);	// why 100000 bps?  No framing errors with a 16 MHz crystal!

	pinMode(ledPin, OUTPUT);	// LED pin

	// cycle radio power
	pinMode(powerPin, OUTPUT);
	digitalWrite(powerPin, LOW);
	_delay_ms(100);
	digitalWrite(powerPin, HIGH);
	_delay_ms(100);

	// enable interrupts
	sei();
	Roomba_Init(0);
	Sonar_Init();

	Radio_Init();
	Radio_Configure(RADIO_2MBPS, RADIO_HIGHEST_POWER);
	Radio_Configure_Rx(RADIO_PIPE_0, explorer_address, ENABLE);
	Radio_Configure_Rx(RADIO_PIPE_1, roomba_address, ENABLE);
	Roomba_ConfigDirtDetectLED(LED_ON);

	//Serial.println("Initialized...");
	for (;;)
	{
		// Move packet received
		if (radio_state == BASE_PACKET_READY)
		{
			// Receive and use movement pack
			radio_state = NO_PACKET;
			RADIO_RX_STATUS result = Radio_Receive(&packet);
			//if (result != RADIO_RX_SUCCESS){continue;}
			//snprintf(output, sizeof(output), "RO: %d|%d|%d", result, packet.payload.move.angle, packet.payload.move.distance);
			//Serial.println(output);

			if (packet.type == MOVE_ROOMBA)
			{
				rotate_roomba(packet.payload.move.angle);
				translate_roomba(packet.payload.move.distance);
				Roomba_Drive(0, 0); // Stop

				// For each beacon
				int i = 0;
				while (i < TOTAL_BEACONS)
				{
					start = millis16();
					uint8_t attempts = 0;
					// Need to stop after several attempts
					while (attempts < 3 && Sonar_GetState() != OUTPUT_READY)
					{
						if (millis16() - start > 1000)
						{
							//Serial.println("Trigger.");
							// start the query protocol every 1000 ms.
							Sonar_PreTrigger();
							// send a request to the sonar station
							packet.type = REQUEST_ECHO;
							memcpy(packet.payload.request.return_address, explorer_address, RADIO_ADDRESS_LENGTH);
							// Needs to be fixed to change to last sensor address (i.e. i=3 -- 0x03)
							Radio_Set_Tx_Addr(sensor_address);
							Radio_Transmit(&packet, RADIO_WAIT_FOR_TX);
							start = millis16();
							++attempts;
						}

						if (radio_state == PACKET_READY)
						{
							// Radio_Receive takes a while, so I'm putting it after the trigger.  This means that
							// the explorer assumes any packet it gets is an echo confirmation packet ('cause it
							// can't check what the packet was).  Possible solution: send other packets on a
							// different address.
							Sonar_Trigger();
							radio_state = NO_PACKET;
							Radio_Receive(&packet);
							packet.type = EMPTY;
						}
					}
					if (attempts >= 3){beacon_distances[i] = -1;}
					else{
						// TODO: the error changes if the confirmation packet was retransmitted, might be able to detect.
						beacon_distances[i] = Sonar_GetDistance(-19);
					}
					//snprintf(output, sizeof(output), "Dist: %d\n\r", beacon_distances[i]);
					//Serial.print(output);
					++i;
				} // For each

				// Sending log message to base
				Radio_Set_Tx_Addr(base_address);

				packet.type = LOG_DATA;
				packet.timestamp = millis();
				packet.payload.log.angle = Roomba_GetTotalAngle();
				packet.payload.log.distance = Roomba_GetTotalDistance();
				packet.payload.log.beacon_distance[0] = beacon_distances[0];
				Radio_Transmit(&packet, RADIO_WAIT_FOR_TX);
			}
			else
			{
				// Error or Ignore
			}
		}//if basepacket
	}//for;;

	for (;;);
	return 0;
}

// This function is called by the radio interrupt, so it must return quickly.
void radio_rxhandler(uint8_t pipe_number)
{
	flipLED();
	if (pipe_number == RADIO_PIPE_0)
	{
		radio_state = PACKET_READY;
	}
	else
	{
		radio_state = BASE_PACKET_READY;
		//Serial.println("Test!");
	}
}
