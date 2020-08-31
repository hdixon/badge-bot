import praw
import sqlite3
from datetime import datetime
from praw.models import Message
from dateutil.parser import parse
import time
from datesfunc import *

bot = praw.Reddit("badge-bot", user_agent="badge-bot by u/huckingfoes")
db = "badges.db"



def tableExists(tableName):
	# untested
	query = "SELECT name FROM ? WHERE type='table' AND name='?';"
	try:
		conn = sqlite3.connect(db)
		cur = conn.cursor()
		sql_tuple = (db, tableName)
		cur.execute = (query, sql_tuple)
		if len(cur) == 1:
			conn.close()
			return True
		elif len(cur) > 1:
			# there's an issue, there's more than 1 table with that name
			print("Issue: more than one table with the same name wtf")
			conn.close()
			return -1
		else:
			# table doesn't exist
			conn.close()
			return 0
	except Exception as e:
		print(e)


def addSubreddit(subName):
	# unfinished
	assert(isinstance(subName, String))

	if(tableExists):
		# don't do anything and return false
		return 0

	else:
		query = ''' CREATE TABLE IF NOT EXISTS ? (
					username text NOT NULL,
					badgedate text NOT NULL,
					);
				'''
		sql_tuple = (subName,)

		# create table and return true
		return 1

	return -1

def isInDatabase(username):
	# check if redditor is in database
	assert(isinstance(username, String))

	try:
		conn = sqlite3.connect(db)
		cur = conn.cursor()
		cur.execute("SELECT username FROM users WHERE username =" + " '" + username + "'")
		rows = cur.fetchall()
		print(rows)

		if len(rows) == 1:
			# user exists, we can update the date in the db and update flairText
			return True

		elif len(rows) == 0:
			# user does not exist, we can insert a new row in the db and update flair
			return False
		else:
			print("Unexpected error:", sys.exc_info()[0])
			raise

		conn.commit()
		conn.close()

	except Exception as e:
		print(e)

	return -1

def updateAllBadges():
	try:
		conn = sqlite3.connect(db)
		c = conn.cursor()
		sqlite_param = 'SELECT * from users'
		c.execute(sqlite_param)

		for row in c:
			username = row[0]
			badgedate = row[1]
			dateDiff = daysSince(badgedate)
			newBadge = str(dateDiff + " days")
			updateFlair(username, newBadge)
			print("updateAllBadges: updated " + username + " with " + newBadge)

	except Exception as e:
		print(e)

	return 1

def removeFromDatabase(username):
	username = str(username)
	if not isInDatabase(username):
		print("Tried to remove user not in database.")
		return 0

	try:
		username = str(username)
		print("Trying to remove, user is in db: " + str(username))
		conn = sqlite3.connect(db)
		c = conn.cursor()
		sqlite_param = """DELETE FROM users
						WHERE username = ?
						"""

		c.execute(sqlite_param, (username,))
		conn.commit()
		conn.close()
		print("Removed " + username + " from database.")

	except Exception as e:
		print(e)
		return -1

	return 1

def updateDate(username, startDate):
	dateDiff = daysSince(startDate)
	username = str(username)

	if isInDatabase(username):
		updateDatabase(username, startDate)
		updateFlair(username, str(dateDiff + " days"))
	else:
		insertInDatabase(username, startDate)
		updateFlair(username, str(dateDiff + " days"))

def updateDatabase(username, startDate):
	try:
		conn = sqlite3.connect(db)
		c = conn.cursor()
		sqlite_insert_with_param = """UPDATE users
								SET badgedate = ?
								WHERE username = ?
								"""
		data_tuple = (startDate, username)
		c.execute(sqlite_insert_with_param, data_tuple)
		conn.commit()
		conn.close()
	except Exception as e:
		print(e)
		raise

def insertInDatabase(username, startDate):
	if isinstance(startDate, datetime):
		startDate = datetime.strptime(startDate, "%Y-%m-%d")
	try:
		conn = sqlite3.connect(db)
		c = conn.cursor()
		sqlite_insert_with_param = """INSERT INTO users
                          (username, badgedate)
                          VALUES (?, ?);"""
		data_tuple = (username, startDate)
		c.execute(sqlite_insert_with_param, data_tuple)
		conn.commit()
		conn.close()

	except Exception as e:
		print(e)
		raise

	return 0

def checkValidMessage(item):
	# ensure type of item is Message
	assert(isinstance(item, Message))
	redditor = item.author
	subject = item.subject.strip().lower()
	body = item.body.strip().lower()

	acceptableSubjects = ["update", "request", "remove", "reset"]
	print("Checking valid message")

	if subject in acceptableSubjects:
	# okay, subject is within set of acceptable subjects

		if subject == "update" and isValidDate(body):
			print("Update message recieved with valid body: " + body)
			return True
		elif subject == 'request' or subject == 'reset':
			return True
		elif subject == 'remove':
			return True
		else:
			print("checkValidMessage failed (other)")
			return False
		return True

	return False

def updateFlair(redditor, flairText):
	sub = bot.subreddit('StopSpeeding')
	username = str(redditor)
	return sub.flair.set(username, flairText, css_class='badge')

def removeFlair(redditor):
	sub = bot.subreddit('StopSpeeding')
	return sub.flair.delete(redditor)

def iterateMessageRequests():
	unreadMessages = bot.inbox.unread(limit=None)
	unread_messages = []
	today = datetime.today().strftime("%Y-%m-%d")
	for item in unreadMessages:
		if isinstance(item, Message):
			if(checkValidMessage(item)):
				print("New message is valid, from " + str(item.author))
				subj = str(item.subject.lower())
				if subj == 'request' or subj == "reset":
					print("New badge request... giving badge")
					updateDate(item.author, today)
					item.mark_read()
					item.reply("Request honored. Your badge has been updated.")
				elif subj == 'update':
					if isValidDate(item.body):
						if int(daysSince(item.body)) > 1440:
							# dont allow for manually updating flairs more than 4 years
							item.reply("You may only update a flair with up to 4 years in the past. Try again with a more recent date or contact moderators manually to update your flair accordingly.")
						else:
							updateDate(item.author, item.body)
							item.reply("Update honored. Your badge has been updated.")
						item.mark_read()
					else:
						item.mark_read()
						item.reply("I could not parse the date you provided.")
				elif subj == 'remove':
					print("Message is remove request.")
					removeFromDatabase(item.author)
					print("Removed from database")
					removeFlair(item.author)
					item.mark_read()
					item.reply("You've been removed from the badge database.")
			else:
				s = "Hello %s, your message is invalid: \n %s \n %s" % (item.author, item.subject, item.body)
				print(s)
				item.reply("Your message is invalid.")
				item.mark_read()

count = 0
while True:
	count += 1
	t = datetime.today().strftime('%H:%M:%S')
	print(t + " Main loop, checking messages.")
	iterateMessageRequests()

	if count % 120 == 0:
		print("Count is " + str(count))
		print("Updating all badges.")
		updateAllBadges()

	time.sleep(180)
