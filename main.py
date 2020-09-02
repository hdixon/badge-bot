import praw
import sqlite3
from datetime import datetime
from praw.models import Message
from dateutil.parser import parse
import time
from datesfunc import *

bot = praw.Reddit("badge-bot", user_agent="badge-bot by u/huckingfoes")
db = "badges.db"

# String Helper
def cleanSubredditString(subreddit):
	subreddit = str(subreddit) # just make sure subreddit is a string
	subredditString = subreddit.replace('/r/', '')
	subredditString = subreddit.replace('r/', '')

	# DEBUGGING: lets just check if we had to replace anything
	if(subredditString != subreddit):
		print("Oh we had to remove a r/ from %s to %s" %(subreddit, subredditString))

	return subredditString.lower()

# Database Helpers
def create_table(subreddit):
	# connects to a db and creates new table for subreddit
	subredditString = cleanSubredditString(subreddit)
	conn = sqlite3.connect(db)
	c = conn.cursor()
	c.execute('CREATE TABLE IF NOT EXISTS ' + subredditString + ' (username TEXT NOT NULL, badgedate TEXT NOT NULL, dateadded TEXT NOT NULL);')

	conn.commit()
	conn.close()
	print('Created table: ' + subredditString)

	return True


def table_exists(tableName):
	assert(isinstance(tableName, str)) # ensure input is a string
	# return boolean if table exists or not

	try:
		conn = sqlite3.connect(db)
		c = conn.cursor()
		c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?;", (tableName,))

		if c.fetchone()[0] == 1:
			# table exists
			# print("Table exists: " + tableName)
			return True
		else:
			# table doesn't exist
			# print("Table does not exist: " + tableName)
			return False
		conn.commit()
		conn.close()
	except Exception as e:
		print(e)
		raise


def addSubreddit(subreddit):
	# takes subreddit string
	subredditString = cleanSubredditString(subreddit)
	# assert(isinstance(subredditString, str))
	print("adSubreddit(): Trying to add subreddit:" + subreddit)

	if(table_exists(subredditString)):
		# don't do anything and return false
		# technically we don't need this check because we only create unique
		#     tables due to the SQL IF NOT EXISTS
		print("addSubreddit(): Table already exists.")
		return 0

	else:
		# if table doesn't exist, we make it
		create_table(subredditString)
		print("adSubreddit(): Table doesn't exist... creating: " + subredditString)
		return 1

	return -1

def isInDatabase(username, subreddit):
	# check if redditor is in database
	assert(isinstance(username, str))
	subreddit = cleanSubredditString(subreddit)

	try:
		conn = sqlite3.connect(db)
		cur = conn.cursor()
		cur.execute("SELECT * FROM " + subreddit + " WHERE username =" + " '" + username + "'")
		rows = cur.fetchall()

		if len(rows) == 1:
			# user exists, we can update the date in the db and update flairText
			# print("isInDatabase(): User exists, returning true.")
			conn.commit()
			conn.close()
			return True

		elif len(rows) == 0:
			# user does not exist, we can insert a new row in the db and update flair
			conn.commit()
			conn.close()
			return False
		else:
			print("isInDatabase(): Unexpected error: ", sys.exc_info()[0])
			print("isInDatabase(): Returning -1")
			conn.commit()
			conn.close()
			return -1



	except Exception as e:
		print("isInDatabase() encountered an error.")
		print(e)

	return -1

def loopThroughTables():
	try:
		conn = sqlite3.connect(db)
		db_list = []

		mycursor = conn.cursor()
		for db_name in mycursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'"):
			db_list.append(db_name)
		conn.close()

		# update all badges in teach table
		for x in db_list:
			print("Updating badges for" + str(x[0]))
			updateAllBadges(x[0])


	except sqlite3.Error as e:
		print('Db Not found', str(e))

def updateAllBadges(subreddit):
	subreddit = cleanSubredditString(subreddit)
	try:
		conn = sqlite3.connect(db)
		c = conn.cursor()
		c.execute('SELECT * from ' + subreddit)

		for row in c:
			username = row[0]
			badgedate = row[1]
			dateDiff = daysSince(badgedate)
			newBadge = str(dateDiff + " days")
			updateFlair(username, newBadge, subreddit)
			print("updateAllBadges: updated " + username + " with " + newBadge + " in subreddit " + subreddit)

	except Exception as e:
		print("updateAllBadges() failed. Probably a database error.")
		print(e)

	return 1

def removeFromDatabase(username, subreddit):
	username = str(username)
	subreddit = cleanSubredditString(subreddit)
	if not isInDatabase(username, subreddit):
		print("removefromDatabase(): Tried to remove user not in database.")
		return 0

	try:
		# print("Trying to remove, user is in db: " + str(username))
		conn = sqlite3.connect(db)
		c = conn.cursor()
		sqlite_param = "DELETE FROM " + subreddit + " WHERE username = ?"

		c.execute(sqlite_param, (username,))
		conn.commit()
		conn.close()
		print("removeFromDatabase(): Removed " + username + " from " + subreddit)

		return 1

	except Exception as e:
		print(e)
		return -1

	return 1

def updateDate(username, startDate, subreddit):
	dateDiff = daysSince(startDate)
	username = str(username)
	subreddit = cleanSubredditString(subreddit)

	if isInDatabase(username, subreddit):
		updateDatabase(username, startDate, subreddit)
		updateFlair(username, str(dateDiff + " days"), subreddit)
	else:
		insertInDatabase(username, startDate, subreddit)
		updateFlair(username, str(dateDiff + " days"), subreddit)

def updateDatabase(username, startDate, subreddit):
	try:
		subredditString = cleanSubredditString(subreddit)
		conn = sqlite3.connect(db)
		c = conn.cursor()
		data_tuple = (startDate, username)
		c.execute('UPDATE ' + subreddit + ' SET badgedate = ? WHERE username = ?', (startDate, username))
		conn.commit()
		conn.close()
	except Exception as e:
		print(e)
		print("updateDatabase() failed.")
		raise

def insertInDatabase(username, startDate, subreddit):
	subreddit = cleanSubredditString(subreddit)
	assert(not isInDatabase(username, subreddit))

	if isinstance(startDate, datetime):
		startDate = datetime.strptime(startDate, "%Y-%m-%d")
	try:
		conn = sqlite3.connect(db)
		c = conn.cursor()
		todayString = datetime.today().strftime("%Y-%m-%d")
		query1 = 'INSERT INTO ' + subreddit + ' '
		query2 = '(username, badgedate, dateadded) VALUES (?, ?, ?);'
		sqlite_insert_with_param = query1 + query2
		data_tuple = (username, startDate, todayString)

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
	subject = cleanSubredditString(item.subject)
	body = str(item.body).strip().lower()

	acceptableCommands = ["remove", "reset"]
	print("Checking valid message")

	if body in acceptableCommands or isValidDate(body):
	# okay, seems to be within set of acceptable commands
		if not table_exists(subject):
			print("Message invalid: table does not exist for " + subject)
			return False

		if isValidDate(body):
			return True
		elif body == 'reset':
			return True
		elif body == 'remove':
			return True
		else:
			print("checkValidMessage failed (other)")
			return False
		return True

	return False

def updateFlair(redditor, flairText, subreddit):
	subredditString = cleanSubredditString(subreddit)
	sub = bot.subreddit(subredditString)
	username = str(redditor)
	return sub.flair.set(username, flairText, css_class='badge')

def removeFlair(redditor, subreddit):
	subredditString = cleanSubredditString(subreddit)
	sub = bot.subreddit(subredditString)
	return sub.flair.delete(redditor)

def acceptModInvites():
	for message in bot.inbox.unread(limit=None):
		if message.body.startswith('gadzooks!'):

			subredditInstance = message.subreddit
			subredditString = cleanSubredditString(message.subreddit)
			print("Found invite to: " + subredditString)
			message.mark_read()
			try:
				subredditInstance.mod.accept_invite()
				print("Accepted mod invite!")
				strReply = '''
							Thanks for the invite! I can now provide badges to your subreddit %s
							so long as I have flair permissions at least.
							[Check my userpage for more info on configuring badge bot on your subreddit.]
							'''
				message.reply("Thanks for the invite. I can now provide badges for your subreddit as long as I have flair permissions. Check my userpage for more info.")
				# print("Checking all moderators.")
				# checkModPerms(subredditInstance)
				print("Creating new table for subreddit: " + subredditString)
				addSubreddit(subredditString)
				print("Subreddit added to db.")
			except:
				print("Tried to accept invite, but invalid.")

def checkModPerms(sub):
	# for the next version
	moderators = sub.moderator()
	for mod in moderators:
		print(mod)
		if str(mod) == 'badge-bot':
			# okay i'm a mod now
			print("okay i'm a mod are the permissions okay")
	return 0



def iterateMessageRequests():
	unreadMessages = bot.inbox.unread(limit=None)
	# unread_messages = []

	# get any mod invites out of the way
	acceptModInvites()

	today = datetime.today().strftime("%Y-%m-%d")

	for item in unreadMessages:
		# print(item)

		assert(isinstance(item, Message))
		subreddit = cleanSubredditString(item.subject)
		body = str(item.body.lower())
		author = item.author
		print("New message from %s\n subject: %s \n body: %s " %(author, subreddit, body))

		if not table_exists(subreddit):
			# if subreddit is not in database, check if we're a mod
			item.reply("Your subreddit is not in our database. Message your moderators or please invite u/badgebot to moderate with flair permissions. If this is an error, contact u/huckingfoes by PM.")
			item.mark_read()

		elif table_exists(subreddit):

			if(checkValidMessage(item)):
			# if True:
				print("New valid message from: " + str(item.author))
				if body == "reset":
					print("New badge request... giving badge.")
					updateDate(item.author, today, subreddit)
					item.mark_read()
					item.reply("Request honored. Your badge has been updated.")
				elif isValidDate(body):
					if int(daysSince(item.body)) > 2880:
						# dont allow for manually updating flairs more than 4 years
						print("Replying to invalid date request")
						item.reply("You may only update a flair with up to 8 years in the past. Try again with a more recent date or contact moderators manually to update your flair accordingly.")
					else:
						updateDate(author, body, subreddit)
						item.reply("Update honored. Your badge has been updated.")
						print("Updated badge.")

					item.mark_read()

				elif body == 'remove':
					print("Message is remove request.")
					removeFromDatabase(author, subreddit)
					print("Removed " + str(author) + " from " + subreddit)
					removeFlair(author, subreddit)
					item.mark_read()
					item.reply("You've been removed from the badge database: " + subreddit)
					print("Replied to remove request.")
			else:
				s = "Hello %s, your message is invalid: \n %s \n %s" % (item.author, item.subject, item.body)
				print(s)
				item.reply(s)
				item.mark_read()

		else:
			s = "Hello %s, your message is invalid: \n %s \n %s" % (item.author, item.subject, item.body)
			print(s)
			item.reply(s)
			item.mark_read()



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
			print(str(date))
			date = parse(date)
			print(date)
			if date <= datetime.today():
				return True
				# print("Date  is before or equal today")
			elif date == datetime.today():
				return True
				# print("Date is today")
			else:
				print("Invalid date: " + str(date))
				return False
		except Exception as e:
			print(e)
			return False
	return False


count = 0



while True:
	t = datetime.today().strftime('%H:%M:%S')
	if count % 5 == 0:
		print(t + " Checking messages.")

	iterateMessageRequests()

	count += 1

	if count % 350 == 0:
		#update all badges every 12 hours or so
		print("Count is " + str(count))
		print("Updating all badges.")
		loopThroughTables()


	time.sleep(120)
