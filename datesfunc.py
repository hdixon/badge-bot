import datetime as dt
from dateutil.parser import parse
import time
import logging

def time_between(begin_time, end_time, check_time=None):
	# If check time is not given, default to current UTC time
	print(check_time)
	check_time = check_time or dt.datetime.utcnow().time()
	if begin_time < end_time:
		return check_time >= begin_time and check_time <= end_time
	else: # crosses midnight
		return check_time >= begin_time or check_time <= end_time

def getBadgeText(daysDiff):
	daysDiff = int(daysDiff)
	if daysDiff < 365:
		return str(daysDiff) + " days"
	elif daysDiff >= 365:
		numYears = int(daysDiff / 365)
		if numYears == 1:
			return str(numYears) + " year"
		else:
			return str(numYears) + " years"
	return str(daysDiff) + " days"

def daysSince(date):
	todayObject = dt.datetime.today()
	if isinstance(date, dt.datetime):
		return str((todayObject - date).days)
	if isValidDateStr(date):
		startDateObject = parse(date)
		if (todayObject >= startDateObject):
			daysSince = abs(todayObject - startDateObject)
			return str(daysSince.days)
	else:
		try:
			return todayObject - startDateObject
		except:
			return 0
	return -1

def isValidDateStr(date):
	if date:
		try:
			date = parse(date)
			if date <= dt.datetimetoday():
				return True
				logging.debug("Date  is before or equal today")
			elif date == dt.datetimetoday():
				return True
				logging.debug("Date is today")
			else:
				logging.error("Invalid date: " + str(date))
				return False
		except Exception as e:
			logging.critical(e)
			return False
	return False
