/*
 * packet.h
 *
 *  Created on: 26-Apr-2009
 *      Author: Neil MacMillan
 */

#ifndef PACKET_H_
#define PACKET_H_


#include <avr/io.h>

/*****					Add labels for the packet types to the enumeration					*****/

typedef enum _pt
{
	EMPTY,			// not a realized packet type; empty means that the packet structure contains invalid data
	REQUEST_ECHO,	// explorer sends sonar station an echo request
	CONFIRM_ECHO,	// sonar station replies with confirmation as soon as sonar pulse is transmitted
	MOVE_ROOMBA,	// base sends a movement command to the explorer
	LOG_DATA,		// explorer sends distance/angle/beacon readings to the base
} PACKET_TYPE;

/*****							Construct payload format structures							*****/

// structures must be 29 bytes long or less.

typedef struct _re
{
	uint8_t return_address[5];	/// The explorer's address.
} pf_request_echo_t;

typedef struct _ce
{
	uint8_t station_id;			/// The ID of the station sending the echo
} pf_confirm_echo_t;

typedef struct _mr
{
	int16_t angle; 				/// Angle for the Roomba to move (in Roomba format)
	int16_t distance;			/// Distance for the Roomba to move straight (in mm)
} pf_move_roomba_t;

typedef struct _ld
{
	int16_t angle;				 /// Angle Roomba moved (in Roomba format)
	int16_t distance;			 /// Distance Roomba moved (in mm)
	int16_t beacon_distance[12];/// Distance from Roomba to each beacon
} pf_log_data_t;

/*****							Add format structures to the union							*****/

/// The application-dependent packet format.  Add structures to the union that correspond to the packet types defined
/// in the PACKET_TYPE enumeration.  The format structures may not be more than 29 bytes long.  The _filler array must
/// be included to ensure that the union is exactly 29 bytes long.
typedef union _pf
{
	uint8_t _filler[29];	// make sure the packet is exactly 32 bytes long - this array should not be accessed directly.
	pf_request_echo_t request;
	pf_confirm_echo_t confirm;
	pf_move_roomba_t move;
	pf_log_data_t log;
} payloadformat_t;

/*****						Leave the radiopacket_t structure alone.						*****/

typedef struct _rp
{
	PACKET_TYPE type;
	uint16_t timestamp;
	payloadformat_t payload;
} radiopacket_t;

#endif /* PACKET_H_ */
