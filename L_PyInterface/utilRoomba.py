import math

def RoombaAngleToDegrees(ang):
    # Angle in degrees from Roomba Spec
    # (int)(360 * a) / (258 * PI)
    return (360 * ang) / (258 * math.pi)

def DegreesToRoombaAngle(deg):
    # Angle in degrees from Roomba Spec
    # (int)(360 * a) / (258 * PI)
    return (deg * 258 * math.pi) / 360

def RoombaDistanceToCm(dist):
    # Distance in cm
    # Roomba: d * 10
    return dist / 10

def CmToRoombaDistance(cm):
    return cm * 10
