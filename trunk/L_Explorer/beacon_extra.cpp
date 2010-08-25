/*
 * beacon_extra.cpp
 *
 *  Created on: 11-Jul-2010
 *      Author: nrqm
 */

#include "beacon_extra.h"
#include "arduino/WProgram.h"
#include "sonar/sonar.h"
#include "radio/radio.h"
#include "radio/packet.h"

#define BEACON_ERROR -19	// Constant error in the beacon reading, in cm

typedef enum _rs
{
	NO_PACKET,
	BEACON_PACKET_READY,
	BASE_PACKET_READY,
} RADIO_STATE;

extern radiopacket_t packet;
extern uint8_t explorer_beaconrx_address[RADIO_ADDRESS_LENGTH];
volatile extern RADIO_STATE radio_state;
extern uint8_t ledPin;

uint8_t beacon_address[RADIO_ADDRESS_LENGTH] = {0xB7, 0xB7, 0xB7, 0xB7, 1};

uint16_t ping_beacon(uint8_t beacon_id)
{
	uint16_t distance;

	Sonar_PreTrigger();

	// send a request to the beacon
	packet.type = REQUEST_ECHO;
	memcpy(packet.payload.request.return_address, explorer_beaconrx_address, RADIO_ADDRESS_LENGTH);
	beacon_address[RADIO_ADDRESS_LENGTH-1] = beacon_id;
	Radio_Set_Tx_Addr(beacon_address);
	if (Radio_Transmit(&packet, RADIO_WAIT_FOR_TX) != RADIO_TX_SUCCESS)
	{
		// report beacon was offline or out of radio range
		return 0;
	}

	// wait for its response
	uint32_t start_time = millis();
	while (radio_state != BEACON_PACKET_READY)
	{
		if (millis() - start_time > 100)
		{
			return 1;
		}
	}


	// start counting the sonar delay
	Sonar_Trigger();
	radio_state = NO_PACKET;
	Radio_Receive(&packet);
	packet.type = EMPTY;

	// wait for the sonar pulse to be received
	while (Sonar_GetState() != OUTPUT_READY);

	distance = Sonar_GetDistance(BEACON_ERROR);

	// cap the maximum distance at 10 m (it's actually a little over 11 m but whatever)
	if (distance <1000)
	{
		// report beacon was in range, and return the distance.
		return distance;
	}
	else
	{
		// report beacon was out of sonar range
		// it's okay to use 1 as an error code because the beacon is undetectable within a range
		// of roughly 4 cm (i.e. the distance will never be reported as 1 cm).
		return 1;
	}
}

void poll_beacons(int16_t* beacon_distances, uint8_t num_beacons)
{
	uint8_t i, j;
	uint16_t ping_result;
	// ping each beacon in turn
	for (i = 0; i < num_beacons; i++)
	{
		for (j = 0; j < 3; j++)
		{
			ping_result = ping_beacon(i + 1);
			// give the sonar pulse some time to settle down
			delay(50);

			if (ping_result == 0 || ping_result == 1)
			{
				// beacon was offline or not in sonar range
				beacon_distances[i] = -1;
			}
			else
			{
				// received sane distance, move on to next beacon
				beacon_distances[i] = ping_result;
				break;
			}
		}
	}
}

void beacon_test_routine(uint8_t beacon_id)
{
	uint16_t ping_result;
	for (;;)
	{
		delay(1000);
		ping_result = ping_beacon(beacon_id);
		if (ping_result > 1)
		{
			// the beacon is online and in range
			digitalWrite(ledPin, HIGH);
		}
		else
		{
			// the beacon is offline or out of range
			digitalWrite(ledPin, LOW);
		}
	}
}
