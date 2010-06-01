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

#define SONAR_PIN 10
#define SONAR_TRIGGER_HIGH() (digitalWrite(SONAR_PIN, HIGH))
#define SONAR_TRIGGER_LOW()  (digitalWrite(SONAR_PIN, LOW))

#define STATION_ID 0x01		// station identifier can be 0 to 254 inclusive

typedef enum _rs
{
	NO_PACKET,
	PACKET_READY,
} RADIO_STATE;

char output[64];

RADIO_STATE radio_state = NO_PACKET;
radiopacket_t packet;
uint8_t sensor_address[RADIO_ADDRESS_LENGTH] = {0xB7, 0xB7, 0xB7, 0xB7, STATION_ID};

extern "C" void __cxa_pure_virtual()
{

}

int main()
{
	cli();
	init();
	Serial.begin(100000);

	pinMode(13, OUTPUT);	// led
	digitalWrite(13, LOW);

	pinMode(SONAR_PIN, OUTPUT);
	digitalWrite(SONAR_PIN, LOW);

	pinMode(9, OUTPUT);		// power cycle radio
	digitalWrite(9, LOW);
	_delay_ms(100);
	digitalWrite(9, HIGH);
	_delay_ms(100);

	sei();

	Radio_Init();
	Radio_Configure(RADIO_2MBPS, RADIO_HIGHEST_POWER);
	Radio_Configure_Rx(RADIO_PIPE_0, sensor_address, ENABLE);

	for (;;)
	{
		if (radio_state == PACKET_READY)
		{
			radio_state = NO_PACKET;
			Radio_Receive(&packet);				// assumption: radio FIFO contains just one packet
			if (packet.type == REQUEST_ECHO)
			{
				SONAR_TRIGGER_HIGH();	// trigger must be high for more than 10 us, and certainly is here.
				Radio_Set_Tx_Addr(packet.payload.request.return_address);
				packet.type = CONFIRM_ECHO;
				packet.payload.confirm.station_id = STATION_ID;
				Radio_Transmit(&packet, RADIO_WAIT_FOR_TX);
				// sonar is triggered as soon as the explorer acknowledges it received the confirmation
				SONAR_TRIGGER_LOW();
			}
			packet.type = EMPTY;
			digitalWrite(13, !digitalRead(13));
		}
	}


	for (;;);
	return 0;
}

void radio_rxhandler(uint8_t pipe_numer)
{
	//digitalWrite(13, HIGH);
	radio_state = PACKET_READY;
}

#if 0

int main()
{

	pinMode(13, OUTPUT);
	pinMode(SONAR_PIN, OUTPUT);

	digitalWrite(SONAR_PIN, LOW);
	//digitalWrite(13, LOW);

	for (;;)
	{
		if (radio_state == PACKET_READY)
		{
			radio_state = NO_PACKET;
			Radio_Receive(&packet);				// assumption: radio FIFO contains just one packet
			if (packet.type == REQUEST_ECHO)
			{
				SONAR_TRIGGER_HIGH();	// trigger must be high for more than 10 us, and certainly is here.
				Radio_Set_Tx_Addr(packet.payload.request.return_address);
				packet.type = CONFIRM_ECHO;
				packet.payload.confirm.station_id = station_id;
				Radio_Transmit(&packet, RADIO_WAIT_FOR_TX);
				// sonar is triggered as soon as the explorer acknowledges it received the confirmation
				SONAR_TRIGGER_LOW();
			}
			packet.type = EMPTY;
			digitalWrite(13, LOW);
		}
	}

	return 0;
}
#endif
