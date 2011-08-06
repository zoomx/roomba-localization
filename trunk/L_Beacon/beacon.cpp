/*
 * sonar.c
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

#define STATION_ID 4		// station identifier can be 0 to 254 inclusive

char output[64];

volatile uint8_t radio_flag = 0;
radiopacket_t packet;
uint8_t sensor_address[RADIO_ADDRESS_LENGTH] = {0xB7, 0xB7, 0xB7, 0xB7, STATION_ID};
uint8_t radioPowerPin = 7;

uint8_t sonarPowerPin = 5;
uint8_t sonarGroundPin = 4;

int main()
{
	init();
	pinMode(14, OUTPUT);
	pinMode(15, OUTPUT);
	digitalWrite(15, LOW);

	pinMode(radioPowerPin, OUTPUT);		// power cycle radio
	digitalWrite(radioPowerPin, LOW);
	delay(100);
	digitalWrite(radioPowerPin, HIGH);
	delay(100);

	pinMode(sonarPowerPin, OUTPUT);
	pinMode(sonarGroundPin, OUTPUT);
	digitalWrite(sonarGroundPin, LOW);
	digitalWrite(sonarPowerPin, HIGH);
	Sonar_Init();

	Radio_Init();
	Radio_Configure(RADIO_2MBPS, RADIO_HIGHEST_POWER);
	Radio_Configure_Rx(RADIO_PIPE_0, sensor_address, ENABLE);



	for (;;)
	{
		if (radio_flag)
		{
			radio_flag = 0;
			Radio_Receive(&packet);				// assumption: radio FIFO contains just one packet
			if (packet.type == REQUEST_ECHO)
			{
				Sonar_PreTrigger();
				Radio_Set_Tx_Addr(packet.payload.request.return_address);
				packet.type = CONFIRM_ECHO;
				packet.payload.confirm.station_id = STATION_ID;
				Radio_Transmit(&packet, RADIO_WAIT_FOR_TX);
				// sonar is triggered as soon as the explorer acknowledges it received the confirmation
				Sonar_Trigger();
				delay(50);
				digitalWrite(14, LOW);
			}
			packet.type = EMPTY;
		}
	}

	for (;;);
	return 0;
}

// This function is called by the radio interrupt, so it must return quickly.
void radio_rxhandler(uint8_t pipe_numer)
{
	digitalWrite(14, HIGH);
	radio_flag = 1;
}
