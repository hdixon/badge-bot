import pytest
import datetime as dt
from app import *


def test_sub_exists():
	assert(sub_exists('drugsarebeautiful') == True)
	assert(sub_exists('asdfkjsdf9sdi') == False)
	assert(sub_exists("/r/stopspeeding") == True)

def test_SubredditString():
	assert(cleanSubString("r/dadd ") == "dadd")
	assert(cleanSubString("/r/ dadss   ") == 'dadss')
	assert(cleanSubString(" ") == -1)

def test_badgeText():
	assert(getBadgeText("4") == "4 days")
	assert(getBadgeText(4) == "4 days")
	assert(getBadgeText(366) == "1 year")
	assert(getBadgeText((700) == '2 years'))

def test_time_between():
	assert(time_between(dt.time(23,30), dt.time(00,30), dt.time(23,45)))
	assert(time_between(dt.time(00,00), dt.time(5,00), dt.time(3,59)))
	# assert(True)

def test_daysSince():
	print(daysSince(dt.datetime(2020, 9, 8)))
	assert(daysSince(dt.datetime(2020, 9, 8)) == '2')
