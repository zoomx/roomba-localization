/*
 * sensor_struct.h
 *
 *  Created on: 20-May-2009
 *      Author: nrqm
 */

#ifndef SENSOR_STRUCT_H_
#define SENSOR_STRUCT_H_

// a 16-bit integer split into its high and low bytes (AVR RAM is little-endian!)
typedef struct _i16s
{
        uint8_t low_byte;
        uint8_t high_byte;
} int16_split;

// a signed integer that can be manipulated as a single 16-bit value or as two concatenated bytes.
typedef union _i16u
{
        int16_t value;
        int16_split bytes;
} int16_u;

// an unsigned integer that can be manipulated as a single 16-bit value or as two concatenated bytes.
typedef union _u16u
{
        uint16_t value;
        int16_split bytes;
} uint16_u;

typedef struct
{
    // packet 1 (external sensors)
    uint8_t  bumps_wheeldrops;
    uint8_t  wall;
    uint8_t  cliff_left;
    uint8_t  cliff_front_left;
    uint8_t  cliff_front_right;
    uint8_t  cliff_right;
    uint8_t  virtual_wall;
    uint8_t  motor_overcurrents;
    uint8_t  dirt_left;
    uint8_t  dirt_right;

    // packet 2 (chassis sensors)
    uint8_t  remote_opcode;
    uint8_t  buttons;
	int16_u  distance;
	int16_u  angle;

	// packet 3 (internal sensors)
    uint8_t  charging_state;
    uint16_u voltage;
    int16_u  current;
    int8_t   temperature;
    uint16_u charge;
    uint16_u capacity;
} roomba_sensor_data_t;

#endif /* SENSOR_STRUCT_H_ */
