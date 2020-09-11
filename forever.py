#!/usr/bin/python3
import time
from subprocess import Popen
import sys

count = 3

filename = sys.argv[1]
while True:
    print("\nStarting " + filename)
    p = Popen("python3 " + filename, shell=True)
    p.wait()
    print("Waiting to restart...")
    time.sleep(count ** count)
