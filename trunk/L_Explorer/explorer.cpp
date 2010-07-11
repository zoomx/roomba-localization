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
#include "beacon_extra.h"
#include "roomba_extra.h"

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

typedef enum _rs
{
	NO_PACKET,
	BEACON_PACKET_READY,
	BASE_PACKET_READY,
} RADIO_STATE;

char output[64];

volatile RADIO_STATE radio_state = NO_PACKET;
radiopacket_t packet;

uint8_t explorer_beaconrx_address[RADIO_ADDRESS_LENGTH] = {0xB7, 0xB7, 0xB7, 0xB7, 0xFF};
uint8_t explorer_baserx_address[RADIO_ADDRESS_LENGTH] = {0xB4, 0xB4, 0xB4, 0xB4, 0xFF};
uint8_t base_address[RADIO_ADDRESS_LENGTH] = {0xB4, 0xB4, 0xB4, 0xB4, 1};

uint8_t radioPowerPin = 9;
uint8_t ledPin = 13;
#define flipLED() digitalWrite(ledPin, !digitalRead(ledPin));

#define TOTAL_BEACONS	3	// can't fit more than 12 beacons in log packet
int16_t beacon_distances[TOTAL_BEACONS];

int main()
{
	init();
	cli();

	Serial.begin(100000);	// why 100000 bps?  No framing errors with a 16 MHz crystal!

	pinMode(ledPin, OUTPUT);	// LED pin

	// cycle radio power
	pinMode(radioPowerPin, OUTPUT);
	digitalWrite(radioPowerPin, LOW);
	_delay_ms(100);
	digitalWrite(radioPowerPin, HIGH);
	_delay_ms(100);

	// enable interrupts
	sei();
	Roomba_Init(0);
	Sonar_Init();

	Radio_Init();
	Radio_Configure(RADIO_2MBPS, RADIO_HIGHEST_POWER);
	Radio_Configure_Rx(RADIO_PIPE_0, explorer_beaconrx_address, ENABLE);
	Radio_Configure_Rx(RADIO_PIPE_1, explorer_baserx_address, ENABLE);
	Roomba_ConfigDirtDetectLED(LED_ON);

	// this routine can be enabled to perform an infinite ping test on a given beacon.
	//beacon_test_routine(2);

	for (;;)
	{
		// Move packet received
		if (radio_state == BASE_PACKET_READY)
		{
			// Receive and use movement pack
			radio_state = NO_PACKET;
			Radio_Receive(&packet);

			if (packet.type == MOVE_ROOMBA)
			{
				rotate_roomba(packet.payload.move.angle);
				translate_roomba(packet.payload.move.distance);
				Roomba_Drive(0, 0); // Stop

				poll_beacons(beacon_distances, TOTAL_BEACONS);

				// Send log message to base
				Radio_Set_Tx_Addr(base_address);

				packet.type = LOG_DATA;
				packet.timestamp = millis();
				packet.payload.log.angle = Roomba_GetTotalAngle();
				packet.payload.log.distance = Roomba_GetTotalDistance();
				memcpy(packet.payload.log.beacon_distance, beacon_distances, TOTAL_BEACONS);
				Radio_Transmit(&packet, RADIO_WAIT_FOR_TX);
			}
			else
			{
				// Error or Ignore
			}
		}
	}

	for (;;);
	return 0;
}

// This function is called by the radio interrupt, so it must return quickly.
void radio_rxhandler(uint8_t pipe_number)
{
	if (pipe_number == RADIO_PIPE_0)
	{
		radio_state = BEACON_PACKET_READY;
	}
	else
	{
		radio_state = BASE_PACKET_READY;
	}
}