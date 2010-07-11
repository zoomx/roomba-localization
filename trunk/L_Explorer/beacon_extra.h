/*
 * beacon_extra.h
 *
 *  Created on: 11-Jul-2010
 *      Author: nrqm
 */

#include <avr/io.h>

#ifndef BEACON_EXTRA_H_
#define BEACON_EXTRA_H_

/**
 * Ping a beacon to see if it's online and within range.
 * This function uses and overwrites several values in explorer.cpp (see externs in beacon_extra.cpp).  A
 * 		50 ms delay should be executed between calls to ping_beacon, to give the sonar pulse time to
 * 		dissipate.
 * @return
 * 0 if the beacon didn't respond on the radio
 * 1 if the beacon responded on the radio but the sonar pulse was not received
 * Otherwise the distance to the beacon is returned.
 */
uint16_t ping_beacon(uint8_t id);

void poll_beacons(int16_t* beacon_distances, uint8_t num_beacons);

/**
 * Infinitely ping a beacon every 1 second.  Turn the LED on if the beacon was online and in range,
 * and turn the LED off if the beacon was offline or out of range.  If the beacon is within radio
 * range but not within sonar range, then for some reason the Explorer's LED will sort of flash briefly.
 */
void beacon_test_routine(uint8_t beacon_id);

#endif /* BEACON_EXTRA_H_ */
