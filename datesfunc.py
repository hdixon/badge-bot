def daysSince(date):
	assert isValidDate(date)
	startDateObject = parse(date)
	todayObject = datetime.today()
	assert(todayObject >= startDateObject)
	daysSince = abs(todayObject - startDateObject)
	return str(daysSince.days)

def isValidDate(date):
	if date:
		try:
			date = parse(date)
			if date <= datetime.today():
				return True
			elif parse(date == datetime.today()):
				return True
			else:
				return False
		except Exception as e:
			print(e)
			return False
	return False
