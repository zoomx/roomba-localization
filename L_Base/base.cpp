/*
 * base.cpp
 *
 *  Created on: May 27, 2010
 *      Author: rallen
 */
#include <avr/io.h>
#include "arduino/WProgram.h"
#include "radio/packet.h"
#include "radio/radio.h"

void setup();
void loop();
void setup_radio();
void read_serial(uint8_t);
void echo_serial();
void send_packet();
void read_packet(uint8_t);

#define BAUD_RATE	100000
#define BUF_LEN		64

int ledPin = 13; // LED connected to digital pin 13
int powerPin = 6;

#define flip_LED() digitalWrite(ledPin, !digitalRead(ledPin))
#define millis16() (millis() & 0xFFFF)

#define TOTAL_BEACONS	3	// can't fit more than 12 beacons in log packet

uint8_t roomba_address[RADIO_ADDRESS_LENGTH] = {0xB4, 0xB4, 0xB4, 0xB4, 0xFF};
uint8_t base_address[RADIO_ADDRESS_LENGTH] = {0xB4, 0xB4, 0xB4, 0xB4, 1};
radiopacket_t packet;
volatile uint8_t radio_received_flag = 0;
volatile uint8_t sent_time = 0;
volatile uint8_t sent_packet_flag = 0;
uint8_t current_msg_seq = 0;


// Used by Serial
uint8_t data[BUF_LEN];
char output[BUF_LEN];
pf_move_roomba_t uart_command;


void setup()
{
	pinMode(ledPin, OUTPUT); // initialize the digital pin as an output
	pinMode(powerPin, OUTPUT);

	digitalWrite(powerPin, HIGH); // Provide power to the breadboard / Radio
	delay(11);

	// Radio
	setup_radio();

	// Serial
	Serial.begin(BAUD_RATE);
	memset(data, 0, BUF_LEN);

	Serial.println("INITIALIZED.");
}

void setup_radio()
{
	// Taken from Neil's Radio code.
	Radio_Init();

	Radio_Configure_Rx(RADIO_PIPE_0, base_address, ENABLE);
	Radio_Configure(RADIO_2MBPS, RADIO_HIGHEST_POWER);

	// set the address to send to, dangling prepositions be damned.
	Radio_Set_Tx_Addr(roomba_address);
}

void read_serial(uint8_t len)
{
	int i = 0;
	while(i < len && i < BUF_LEN)
	{
		data[i] = Serial.read();
		++i;
	}
	memcpy(&uart_command, data, sizeof(uart_command));
}

void echo_serial()
{
	Serial.print("RE: ");
	Serial.print(data[0]);
	Serial.print(data[1]);
	Serial.print(data[2]);
	Serial.print(data[3]);
	snprintf(output, sizeof(output), "RE: %d %d", uart_command.angle, uart_command.distance);
	Serial.println(output);
}

void read_packet()
{
	pf_log_data_t inf_packet;
	memcpy(&inf_packet, &packet.payload.log, sizeof(inf_packet));

	if (inf_packet.seq != current_msg_seq)
	{
		snprintf(output, sizeof(output), "Wrong Seq: %d", inf_packet.seq);
		Serial.println(output);
		return;
	}

	Serial.print("IPkt ");
	snprintf(output, sizeof(output), "%d %d |", inf_packet.angle, inf_packet.distance);
	Serial.print(output);
	int i;
	for (i = 0; i < TOTAL_BEACONS; ++i)
	{
		snprintf(output, sizeof(output), "%d ", inf_packet.beacon_distance[i]);
		Serial.print(output);
	}
	// println(output)
	//snprintf(output, sizeof(output), "%d", inf_packet.beacon_distance[0]);
	Serial.println();
	sent_packet_flag = 0;
	++current_msg_seq;
}

void send_packet()
{
	packet.type = MOVE_ROOMBA;
	memcpy(&packet.payload.move, &uart_command, sizeof(uart_command));
	packet.payload.move.seq = current_msg_seq;
	uint8_t result = Radio_Transmit(&packet, RADIO_WAIT_FOR_TX);
	if (result != RADIO_TX_SUCCESS)
	{
		uint8_t retry_counter;
		for (retry_counter = 0; retry_counter < 20; ++retry_counter)
		{
			//Serial.println("Retransmit.");
			delay(500);

			result = Radio_Transmit(&packet, RADIO_WAIT_FOR_TX);
			if (result == RADIO_TX_SUCCESS)
			{
				break;
			}
		}
		Serial.println("Failed to send packet.");
		return;
	}

	flip_LED();
}


void loop()
{

	// Check For new user commands
	if(Serial.available() >= sizeof(pf_move_roomba_t))
	{
		//uint8_t incoming_length = Serial.available();

		// Read the data off the serial into packet
		read_serial(sizeof(pf_move_roomba_t));
		// For debugging purposes. Write back to PC to ensure it is getting it correctly.
		echo_serial();
		// Send the packet off to the Roomba
		send_packet();
		//Serial.println("SENT PACKET");
	}

	if(radio_received_flag)
	{
		radio_received_flag = 0;
		// Copy the received packet from the radio to the local data structure
		flip_LED();
		uint8_t result = Radio_Receive(&packet);
		if (result == RADIO_RX_SUCCESS)
		{
			//pass
		}
		else if (result == RADIO_RX_MORE_PACKETS)
		{
			Radio_Flush();
		}
		else
		{
			snprintf(output, sizeof(output), "Prob w/ pkt %d", result);
			Serial.println(output);
			return;
		}

		if(packet.type == LOG_DATA)
		{

			// Print out the radio packet (log data)
			read_packet();
		}
		else if(packet.type == MOVE_ERROR)
		{
			snprintf(output, sizeof(output), "Error: seq (%d)", packet.type);
			Serial.println(output);
		}
		else
		{
			Serial.println("Rec ? Pkt");
		}
	}
}

int main(void)
{
	init();

	setup();

	for (;;)
		loop();

	return 0;
}

void radio_rxhandler(uint8_t pipenumber)
{
	radio_received_flag = 1;
}
