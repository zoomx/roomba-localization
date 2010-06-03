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

typedef enum _rs
{
	NO_PACKET,
	PACKET_READY,
} RADIO_STATE;

char output[64];

RADIO_STATE radio_state = NO_PACKET;
radiopacket_t packet;

uint8_t explorer_address[RADIO_ADDRESS_LENGTH] = {0xB7, 0xB7, 0xB7, 0xB7, 0xFF};
uint8_t sensor_address[RADIO_ADDRESS_LENGTH] = {0xB7, 0xB7, 0xB7, 0xB7, 1};

int main()
{
	uint16_t start;
	init();
	cli();

	Serial.begin(100000);	// why 100000 bps?  No framing errors with a 16 MHz crystal!

	pinMode(13, OUTPUT);	// LED pin

	// cycle radio power
	pinMode(9, OUTPUT);
	digitalWrite(9, LOW);
	_delay_ms(100);
	digitalWrite(9, HIGH);
	_delay_ms(100);

	// enable interrupts
	sei();

	Sonar_Init();

	Radio_Init();
	Radio_Configure(RADIO_2MBPS, RADIO_HIGHEST_POWER);
	Radio_Configure_Rx(RADIO_PIPE_0, explorer_address, ENABLE);

	start = millis16();

	for (;;)
	{
		if (millis16() - start > 1000)
		{
			// start the query protocol every 1000 ms.
			Sonar_PreTrigger();
			// send a request to the sonar station
			packet.type = REQUEST_ECHO;
			memcpy(packet.payload.request.return_address, explorer_address, RADIO_ADDRESS_LENGTH);
			Radio_Set_Tx_Addr(sensor_address);
			Radio_Transmit(&packet, RADIO_WAIT_FOR_TX);
			start = millis16();
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
		if (Sonar_GetState() == OUTPUT_READY)
		{
			// TODO: the error changes if the confirmation packet was retransmitted, might be able to detect.
			snprintf(output, sizeof(output), "Dist: %d\n\r", Sonar_GetDistance(-15));
			Serial.print(output);
		}
	}

	for (;;);
	return 0;
}

// This function is called by the radio interrupt, so it must return quickly.
void radio_rxhandler(uint8_t pipe_number)
{
	radio_state = PACKET_READY;
}
