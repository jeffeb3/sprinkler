#!/usr/bin/python

import RPi.GPIO as GPIO

class hwio(object):

    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(3,GPIO.OUT)
        GPIO.setup(5,GPIO.OUT)
        GPIO.setup(7,GPIO.OUT)
        GPIO.setup(12,GPIO.OUT)
        GPIO.output(3,True)
        GPIO.output(5,True)
        GPIO.output(7,True)
        GPIO.output(12,True)
    
    def __del__(self):
        GPIO.cleanup()


if __name__ == '__main__':
    import time
    hw = hwio()
    GPIO.output(3,False)
    time.sleep(3)
    GPIO.output(3,True)
    time.sleep(3)
    GPIO.output(3,False)
    time.sleep(3)
    
