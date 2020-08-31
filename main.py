import praw
import sqlite3
from datetime import datetime
from praw.models import Message
from dateutil.parser import parse
import time
from datesfunc import *

bot = praw.Reddit("badge-bot", user_agent="badge-bot by u/huckingfoes")
db = "badges.db"

def cleanSubredditString(subreddit):
	subreddit = str(subreddit) # just make sure subreddit is a string
	subredditString = subreddit.replace('/r/', '')
	subredditString = subreddit.replace('r/', '')

	# DEBUGGING: lets just check if we had to replace anything
	if(subredditString != subreddit):
		print("Oh we had to remove a r/ from %s to %s" %(subreddit, subredditString))

	return subredditString.lower()


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
			print("Table exists: " + tableName)
			return True
		else:
			# table doesn't exist
			print("Table does not exist: " + tableName)
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

	if(table_exists(subredditString)):
		# don't do anything and return false
		# technically we don't need this check because we only create unique
		#     tables due to the SQL IF NOT EXISTS
		print("Table already exists.")
		return 0

	else:
		# if table doesn't exist, we make it
		create_table(subredditString)
		print("Table doesn't exist... creating.")
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
			print(rows)
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
		c.execute('SELECT * from users')

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

def removeFromDatabase(username, subreddit):
	username = str(username)
	subreddit = cleanSubredditString(subreddit)
	if not isInDatabase(username, subreddit):
		print("Tried to remove user not in database.")
		return 0

	try:
		print("Trying to remove, user is in db: " + str(username))
		conn = sqlite3.connect(db)
		c = conn.cursor()
		sqlite_param = "DELETE FROM " + subreddit + " WHERE username = ?"

		c.execute(sqlite_param, (username,))
		conn.commit()
		conn.close()
		print("Removed " + username + " from database.")

		return 1

	except Exception as e:
		print(e)
		return -1

	return 1

def updateDate(username, startDate, subreddit):
	dateDiff = daysSince(startDate)
	username = str(username)

	if isInDatabase(username):
		updateDatabase(username, startDate, subreddit)
		updateFlair(username, str(dateDiff + " days"))
	else:
		insertInDatabase(username, startDate, subreddit)
		updateFlair(username, str(dateDiff + " days"))

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
	subject = item.subject.strip().lower()
	body = item.body.strip().lower()

	acceptableCommands = ["update", "remove", "reset"]
	print("Checking valid message")

	if body in acceptableSubjects or isValidDate(body):
	# okay, seems to be within set of acceptable commands
		if not isInDatabase(subject):
			return False

		if isValidDate(body):
			print("Update message recieved with valid body: " + body)
			return True
		elif subject == 'reset':
			return True
		elif subject == 'remove':
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
			print("Found invite to " + subredditString)
			message.mark_read()
			try:
				subredditInstance.mod.accept_invite()
				print("Accepted mod invite!")
				message.reply("Thanks for the invite. I can now provide badges for your subreddit as long as I have flair permissions. Check my userpage for more info.")
				# print("Checking all moderators.")
				# checkModPerms(subredditInstance)
				print("Creating new table for subreddit...")
				addSubreddit(subredditString)
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

		assert(isinstance(item, Message))
		subreddit = cleanSubredditString(item.subject)
		body = str(item.body.lower())

		if not table_exists(subreddit):
			# if subreddit is not in database, check if we're a mod
			item.reply("Your subreddit is not in our database. Message your moderators or please invite u/badgebot to moderate with flair permissions.")
			item.mark_read()

		elif table_exists(subreddit):

			if(checkValidMessage(item)):
				print("New message is valid, from " + str(item.author))
				if body == "reset":
					print("New badge request... giving badge")
					updateDate(item.author, today, subreddit)
					item.mark_read()
					item.reply("Request honored. Your badge has been updated.")
				elif isValidDate(body):
					if int(daysSince(item.body)) > 1440:
						# dont allow for manually updating flairs more than 4 years
						item.reply("You may only update a flair with up to 4 years in the past. Try again with a more recent date or contact moderators manually to update your flair accordingly.")
					else:
						updateDate(item.author, item.body)
						item.reply("Update honored. Your badge has been updated.")

					item.mark_read()

				elif body == 'remove':
					print("Message is remove request.")
					removeFromDatabase(author, subject)
					print("Removed from database")
					removeFlair(item.author, subject)
					item.mark_read()
					item.reply("You've been removed from the badge database.")
		else:
			s = "Hello %s, your message is invalid: \n %s \n %s" % (item.author, item.subject, item.body)
			print(s)
			item.reply(s)
			item.mark_read()



count = 0
while True:
	count += 1
	t = datetime.today().strftime('%H:%M:%S')
	print(t + " Main loop, checking messages.")
	iterateMessageRequests()

	if count % 500 == 0:
		print("Count is " + str(count))
		print("Updating all badges.")
		updateAllBadges()

	time.sleep(30)
