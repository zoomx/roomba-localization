/*
 * roomba_extra.h
 *
 *  Created on: 9-Jun-2010
 *      Author: nrqm
 */

#ifndef ROOMBA_EXTRA_H_
#define ROOMBA_EXTRA_H_


// Roomba Defs -- Probably want to move these...
#define DRIVE_SPEED		250 // How fast the Roomba moves mm/sec
#define TURN_SPEED		100
#define MOVE_STRAIGHT	32768 // The straight angle in the Roomba Spec
#define MOVE_LEFT		1 // The left angle in Roomba Spec
#define MOVE_RIGHT		-1 // The right angle in Roomba Spec

void rotate_roomba(int16_t angle);

void translate_roomba(int16_t distance);


#endif /* ROOMBA_EXTRA_H_ */
