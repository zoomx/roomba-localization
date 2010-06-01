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

// nrqm - millis() returns uint32_t, I prefer working in uint16_t.
#define millis16() ((millis() & 0xFFFF))

#define SONAR_PIN 10
#define SONAR_TRIGGER_HIGH() (digitalWrite(SONAR_PIN, HIGH))
#define SONAR_TRIGGER_LOW()  (digitalWrite(SONAR_PIN, LOW))

typedef enum _rs
{
	NO_PACKET,
	PACKET_READY,
} RADIO_STATE;

typedef enum _ss
{
	IDLE,						/// waiting for next pulse
	WAITING_FOR_PULSE_START,	/// Trigger has been sent to sonar
	WAITING_FOR_PULSE_END,		/// Sonar echo pulse has started, waiting for falling edge
	OUTPUT_READY,				/// Echo pulse is done, ready to log results.
} SONAR_STATE;

char output[64];

SONAR_STATE sonar_state = IDLE;
volatile uint16_t pulse_start = 0;
volatile uint16_t pulse_end = 0;

RADIO_STATE radio_state = NO_PACKET;
radiopacket_t packet;

uint8_t explorer_address[RADIO_ADDRESS_LENGTH] = {0xB7, 0xB7, 0xB7, 0xB7, 0xFF};
uint8_t sensor_address[RADIO_ADDRESS_LENGTH] = {0xB7, 0xB7, 0xB7, 0xB7, 1};

extern "C" void __cxa_pure_virtual()
{

}

int main()
{
	uint16_t start;
	uint32_t distance;
	init();
	cli();

	// configure timer 1 for input capture
	TCCR1A = 0;
	TIMSK1 = _BV(ICIE1);				// enable ICP1 interrupt (on pin PD4)
	TCNT1 = 0;
	TCCR1B = _BV(CS11) | _BV(CS10);		// start running timer at 250 kHz (16 MHz crystal).

	Serial.begin(100000);	// why 100000 bps?  No framing errors with a 16 MHz crystal!

	pinMode(13, OUTPUT);	// LED pin

	// cycle radio power
	pinMode(9, OUTPUT);
	digitalWrite(9, LOW);
	_delay_ms(100);
	digitalWrite(9, HIGH);
	_delay_ms(100);

	pinMode(SONAR_PIN, OUTPUT);
	digitalWrite(SONAR_PIN, LOW);

	// enable interrupts
	sei();

	Radio_Init();
	Radio_Configure(RADIO_2MBPS, RADIO_HIGHEST_POWER);
	Radio_Configure_Rx(RADIO_PIPE_0, explorer_address, ENABLE);

	start = millis16();

	for (;;)
	{
		if (millis16() - start > 1000)
		{
			// start the query protocol every 1000 ms.
			SONAR_TRIGGER_HIGH();
			// send a request to the sonar station
			packet.type = REQUEST_ECHO;
			memcpy(packet.payload.request.return_address, explorer_address, RADIO_ADDRESS_LENGTH);
			Radio_Set_Tx_Addr(sensor_address);
			Radio_Transmit(&packet, RADIO_WAIT_FOR_TX);
			start = millis16();
		}
		if (radio_state == PACKET_READY)
		{
			radio_state = NO_PACKET;
			SONAR_TRIGGER_LOW();
			sonar_state = WAITING_FOR_PULSE_START;
			Radio_Receive(&packet);
			packet.type = EMPTY;
		}
		if (sonar_state == OUTPUT_READY)
		{
			sonar_state = IDLE;
			distance = 343;
			distance *= (pulse_end - pulse_start);
			distance /= 2500;
			distance -= 15;
			snprintf(output, sizeof(output), "Dist: %d\n\r", (uint16_t)distance);
			Serial.print(output);
		}
	}

	for (;;);
	return 0;
}

void radio_rxhandler(uint8_t pipe_number)
{
	radio_state = PACKET_READY;
}

ISR(TIMER1_CAPT_vect)
{
	if ((TCCR1B & _BV(ICES1)) != 0)
	{
		// Received a rising edge, the start of the echo pulse
		pulse_start = ICR1;
		// set ICP1 to trigger again on falling edge
		TCCR1B &= ~_BV(ICES1);
		digitalWrite(13, HIGH);
	}
	else if ((TCCR1B & _BV(ICES1)) == 0)
	{
		// Received a falling edge, the end of the echo pulse
		pulse_end = ICR1;
		// next time ICP1 is needed it will be to detect a rising edge
		TCCR1B |= _BV(ICES1);
		sonar_state = OUTPUT_READY;
		digitalWrite(13, LOW);
	}
}

#if 0

typedef enum _ys
{
	DOING_OTHER_STUFF,				/// moving, logging, whatever
	WAITING_FOR_ECHO_CONFIRMATION,	/// system is waiting for confirmation packet from sonar station
	GETTING_SONAR_PULSE,			/// this state is just a placeholder for while the SONAR_STATE machine runs
} SYSTEM_STATE;

volatile SYSTEM_STATE system_state = DOING_OTHER_STUFF;
volatile RADIO_STATE radio_state = NO_PACKET;
volatile SONAR_STATE sonar_state = IDLE;

int main()
{


	start = millis16();
	for (;;)
	{
		// currently the echo machine is triggered every second, this condition will need to be
		// changed to trigger when the explorer stops Doing Other Stuff.
		if (millis16() - start >= 1000 && system_state == DOING_OTHER_STUFF)
		{
			// start the query protocol every 1000 ms.
			// send a request to the sonar
			packet.type = REQUEST_ECHO;
			memcpy(packet.payload.request.return_address, explorer_address, RADIO_ADDRESS_LENGTH);
			Radio_Set_Tx_Addr(sensor_address);
			Radio_Transmit(&packet, RADIO_WAIT_FOR_TX);
			// once the request completes, start waiting for the echo confirmation reply
			system_state = WAITING_FOR_ECHO_CONFIRMATION;
			// set the sonar trigger; bringing this low will start the sonar timing pulse.
			SONAR_TRIGGER_HIGH();
			start = millis16();
		}
		if (radio_state == PACKET_READY)
		{
			// Just received echo confirmation, start the sonar detecting.

			// There's an assumption here that the explorer won't receive radio packets while waiting
			// for echo confirmation.  Radio_Receive will take a while to run, so we don't want to
			// have to download the packet before triggering the receiver sonar if we can help it.
			// If this assumption is invalid and we want to check the incoming packet's message type before
			// starting the echo detection pulse, we will have to accept the latency between receiving the
			// echo confirm packet and starting the pulse.
			if (system_state == WAITING_FOR_ECHO_CONFIRMATION)
			{
				// Bringing the trigger line low starts the receiver sonar's echo detect pulse.  The
				// ICP1 ISR handles the pulse measurement automatically and eventually sets the sonar
				// state to OUTPUT_READY.
				SONAR_TRIGGER_LOW();
				sonar_state = WAITING_FOR_PULSE_START;
				system_state = GETTING_SONAR_PULSE;
			}
			// have to copy the packet from the radio, received data are currently ignored.
			Radio_Receive(&packet);
			radio_state = NO_PACKET;
		}
		if (sonar_state == OUTPUT_READY)
		{
			// the explorer has received the signal from the sonar station or timed out.
			// timeout value is around 9000.
			snprintf(output, sizeof(output), "Pulse time: %d\n\r", pulse_end - pulse_start);
			Serial.print(output);
			sonar_state = IDLE;
			system_state = DOING_OTHER_STUFF;
		}
	}

	for (;;);
	return 0;
}

#endif
