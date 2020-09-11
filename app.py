#!/usr/bin/env python3
import praw
import sqlite3
from praw.models import Message
# import datetime as dt
# from dateutil.parser import parse
# import time
import logging
from datesfunc import *

logging.basicConfig(level=logging.INFO, filename='app.log', filemode='a', format='%(asctime)s - %(message)s')

reddit = praw.Reddit("badge-bot", user_agent="badge-bot by u/huckingfoes")
# db = "badges.db"
db = 'test.db'

def sub_exists(sub):
	exists = True
	try:
		results = reddit.subreddits.search_by_name(sub, exact=True)
		if len(results) > 0:
			exists = True
	except:
		exists = False
	return exists

# String Helper
def cleanSubString(subreddit):
	subredditString = str(subreddit) # just make sure subreddit is a string
	subredditString = subredditString.replace('/r/', '')
	subredditString = subredditString.replace('r/', '')
	subredditString = subredditString.strip()
	print(subredditString)

	if subredditString == '' or ' ' in subredditString:
		logging.info("Invalid subreddit string: %s" % subredditString)
		print("Invalid subreddit string")
		return -1
	elif not sub_exists(subredditString):
		logging.info("Subreddit string cleaned: " + subredditString)
		logging.info("But subreddit does not exist.")

	# DEBUGGING: lets just check if we had to replace anything
	if(subredditString != subreddit):
		logging.info("Oh we had to remove a r/ from %s to %s" %(subreddit, subredditString))

	return subredditString.lower()

# Database Helpers
def create_table(subreddit):
	# connects to a db and creates new table for subreddit
	subredditString = cleanSubString(subreddit)
	conn = sqlite3.connect(db)
	c = conn.cursor()
	c.execute('CREATE TABLE IF NOT EXISTS ' + subredditString + ' (username TEXT NOT NULL, badgedate TEXT NOT NULL, dateadded TEXT NOT NULL);')

	conn.commit()
	conn.close()
	logging.info('Created table: ' + subredditString)

	return True

def table_exists(tableName):
	if not isinstance(tableName, str): # ensure input is a string
		return -1
	# return boolean if table exists or not

	try:
		conn = sqlite3.connect(db)
		c = conn.cursor()
		c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?;", (tableName,))
		exists = 0
		if c.fetchone()[0] == 1:
			# table exists
			logging.info("Table exists: " + tableName)
			exists = True
		else:
			# table doesn't exist
			logging.info("Table does not exist: " + tableName)
			exists = False
		conn.commit()
		conn.close()
		return exists
	except Exception as e:
		logging.critical(e)
		logging.critical("Exception occurred", exc_info=True)
		return -1

def addSubreddit(subreddit):
	# takes subreddit string
	subredditString = cleanSubString(subreddit)
	# assert(isinstance(subredditString, str))
	logging.info("addSubreddit(): Trying to add subreddit:" + subreddit)

	if(table_exists(subredditString)):
		# don't do anything and return false
		# technically we don't need this check because we only create unique
		#     tables due to the SQL IF NOT EXISTS
		logging.info("addSubreddit(): Table already exists.")
		return 0

	else:
		# if table doesn't exist, we make it
		create_table(subredditString)
		logging.info("adSubreddit(): Table doesn't exist... creating: " + subredditString)
		return 1

	return -1

def isInDatabase(username, subreddit):
	# check if redditor is in database
	if not isinstance(username, str):
		username = str(username)

	subreddit = cleanSubString(subreddit)

	try:
		conn = sqlite3.connect(db)
		cur = conn.cursor()
		cur.execute("SELECT * FROM " + subreddit + " WHERE username =" + " '" + username + "'")
		rows = cur.fetchall()
		conn.commit()
		conn.close()

		if len(rows) == 1:
			# user exists, we can update the date in the db and update flairText
			# logging.info("isInDatabase(): User exists, returning true.")
			return True

		elif len(rows) == 0:
			return False
		else:
			logging.critical("Exception occurred", exc_info=True)
			logging.critical("isInDatabase(): Returning -1")
			return -1
	except Exception as e:
		logging.error("isInDatabase() encountered an error.")
		logging.critical(e)
		logging.critical("Exception occurred", exc_info=True)

	return -1

def updateFlairsFromDatabase(db):
	logging.info("Looping through tables.")
	try:
		conn = sqlite3.connect(db)
		db_list = []

		mycursor = conn.cursor()
		for db_name in mycursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'"):
			db_list.append(db_name)
		conn.close()

		# update all badges in teach table
		for x in db_list:
			logging.info("Updating badges for " + str(x[0]))
			updateSubredditBadges(x[0])


	except sqlite3.Error as e:
		logging.critical('Db Not found', str(e))
		logging.critical("Exception occurred", exc_info=True)

def updateSubredditBadges(subreddit):
	subreddit = cleanSubString(subreddit)
	try:
		conn = sqlite3.connect(db)
		c = conn.cursor()
		c.execute('SELECT * from ' + subreddit)

		for row in c:
			username = row[0]
			badgedate = row[1]
			dateDiff = daysSince(badgedate)
			badgeText = getBadgeText(dateDiff)
			newBadge = str(badgeText)
			updateFlair(username, newBadge, subreddit)
			logging.info("updateSubredditBadges: updated " + username + " with " + newBadge + " in subreddit " + subreddit)
		conn.close()

	except Exception as e:
		logging.critical("Exception occurred", exc_info=True)
		logging.critical(e)

	return 1

def getRedditorQuitDate(redditor, subreddit):
	substr = cleanSubString(subreddit)
	redditor = str(redditor)
	try:
		conn = sqlite3.connect(db)
		c = conn.cursor()
		c.execute("SELECT * FROM " + subreddit + " WHERE username =?", (redditor,))
		quitDate = c.fetchall()
		c.close()
		return(quitDate[0][1])
	except Exception as e:
		logging.critical("Exception occurred", exc_info=True)
		logging.critical(e)




def removeFromDatabase(username, subreddit):
	username = str(username)
	subreddit = cleanSubString(subreddit)
	if not isInDatabase(username, subreddit):
		logging.error("removefromDatabase(): Tried to remove user not in database.")
		logging.error("Tried to remove user not in database")
		logging.error("user: %s subreddit: %s" % (username, subreddit))
		return 0

	try:
		logging.info("Trying to remove, user is in db: " + str(username))
		conn = sqlite3.connect(db)
		c = conn.cursor()
		sqlite_param = "DELETE FROM " + subreddit + " WHERE username = ?"

		c.execute(sqlite_param, (username,))
		conn.commit()
		conn.close()
		logging.info("removeFromDatabase(): Removed " + username + " from " + subreddit)

		return 1

	except Exception as e:
		logging.critical("Exception occurred", exc_info=True)
		logging.critical(e)
		return -1

	return 1


def updateDate(username, startDate, subreddit):
	dateDiff = daysSince(startDate)
	username = str(username)
	subreddit = cleanSubString(subreddit)

	if isInDatabase(username, subreddit):
		updateDatabase(username, startDate, subreddit)
		badgeText = getBadgeText(dateDiff)
		u = updateFlair(username, badgeText, subreddit)
	else:
		insertInDatabase(username, startDate, subreddit)
		badgeText = getBadgeText(dateDiff)
		u = updateFlair(username, badgeText, subreddit)

	return u

def updateDatabase(username, startDate, subreddit):
	try:
		subredditString = cleanSubString(subreddit)
		conn = sqlite3.connect(db)
		c = conn.cursor()
		c.execute('UPDATE ' + subredditString + ' SET badgedate = ? WHERE username = ?', (startDate, username))
		conn.commit()
		conn.close()
	except Exception as e:
		logging.critical(e)
		logging.info("updateDatabase() failed.")
		logging.error("Exception occurred", exc_info=True)

def insertInDatabase(username, startDate, subreddit):
	subreddit = cleanSubString(subreddit)
	assert(not isInDatabase(username, subreddit))

	if isinstance(startDate, datetime):
		startDate = dt.datetimestrptime(startDate, "%Y-%m-%d")
	try:
		conn = sqlite3.connect(db)
		c = conn.cursor()
		todayString = dt.datetimetoday().strftime("%Y-%m-%d")
		query1 = 'INSERT INTO ' + subreddit + ' '
		query2 = '(username, badgedate, dateadded) VALUES (?, ?, ?);'
		sqlite_insert_with_param = query1 + query2
		data_tuple = (username, startDate, todayString)

		c.execute(sqlite_insert_with_param, data_tuple)
		conn.commit()
		conn.close()

	except Exception as e:
		logging.critical(e)
		raise

	return 0

def checkValidMessage(item):
	# ensure type of item is Message
	if not (isinstance(item, Message)):
		if (item.subject == None or item.subject == ""):
			return False
		logging.warning("checkValidMessage passed item that is not message")
		return False

	redditor = item.author
	subject = cleanSubString(item.subject)
	body = str(item.body).strip().lower()

	acceptableCommands = ["remove", "reset"]
	logging.debug("Checking valid message")

	if body in acceptableCommands or isValidDateStr(body):
	# okay, seems to be within set of acceptable commands
		if not table_exists(subject):
			logging.info("Message invalid: table does not exist for " + subject)
			return False

		logging.debug("body in acceptableCommands or isValidDate")
		if body == 'remove':
			logging.debug("Date message okay!")
			return True
		elif body == 'reset':
			logging.debug("Reset message okay!")
			return True
		elif isValidDateStr(body):
			logging.debug("Remove message okay!")
			return True
		else:
			logging.debug("checkValidMessage failed (other)")
			return False
		return True

	return False

def updateFlair(redditor, flairText, subreddit):
	subredditString = cleanSubString(subreddit)
	sub = reddit.subreddit(subredditString)
	username = str(redditor)
	try:
		quitDate = getRedditorQuitDate(redditor, subreddit)
		soberDays = daysSince(quitDate)
		cssClass = getBadgeClass(subreddit, soberDays)
	except:
		logging.info("Couldn't get quit date.")
	try:
		if quitDate:
			return sub.flair.set(username, flairText, quitDate)
		return sub.flair.set(username, flairText, css_class='badge')
	except:
		return 0

	return 0

def removeFlair(redditor, subreddit):
	subredditString = cleanSubString(subreddit)
	sub = reddit.subreddit(subredditString)
	return sub.flair.delete(redditor)

def acceptModInvites():
	for message in reddit.inbox.unread(limit=None):
		if message.body.startswith('gadzooks!'):
			logging.info("Looks like we have a mod invite!")

			subredditInstance = message.subreddit
			subredditString = cleanSubString(message.subreddit)
			logging.info("Attempting to accept moderator role for: " + subredditString)
			message.mark_read()
			try:
				subredditInstance.mod.accept_invite()
				logging.info("Accepted mod invite!")
				strReply = "Thanks for the invite! I can now provide badges to your subreddit %s so long as I have flair permissions at least. \n\n[Check my userpage here](https://www.reddit.com/user/badge-bot/comments/ik7v4y/badgebot_alpha_version_now_available/) for more info on configuring badge-bot on your subreddit. \n\nFor any issues, please contact u/huckingfoes." %(subredditString)
				linkbase = "https://www.reddit.com/message/compose/?to=badge-bot&subject=[SUBREDDIT]&message=[MESSAGE]"
				linkbase = linkbase.replace("[SUBREDDIT]", subredditString)
				customSetLink = linkbase.replace("[MESSAGE]", "YYYY-MM-DD")
				customResetLink = linkbase.replace("[MESSAGE]", "reset")
				customRemoveLink = linkbase.replace("[MESSAGE]", "remove")
				reply2 = "\nHere are some custom links you can provide to your subreddit so that your community can use the bot more easily.\n"
				reply2 += "\n\n\n **[Click here to set your flair to a particular date.](%s)**\n\n **[Click here to rest flair to 0.](%s)**\n\n **[Click here to remove your flair.](%s)**" % (customSetLink, customResetLink, customRemoveLink)
				print(strReply + reply2)
				strReply += reply2
				message.reply(strReply)
				logging.info("\tReplied: " + strReply)
				# logging.debug("Checking all moderators.")
				# checkModPerms(subredditInstance)
				logging.info("\tCreating new table for subreddit: " + subredditString)
				addSubreddit(subredditString)
				logging.info("Subreddit added to db.")
			except:
				logging.error("Tried to accept invite, but invalid.")
		elif message.subject.startswith('/u/badge-bot has been removed as a moderator'):
			print("Removed as mod.")
			if "r/" in message.subject:
				sub = message.subject.split("r/")[1]
				logging.info("Removed as mod from " + sub)
			else:
				logging.warning("Can't figure out what sub we were removed from.")
			message.mark_read()
	return False

def checkModPerms(sub):
	# for the next version
	for moderator in reddit.subreddit(sub).moderator():
		if 'badge-bot' in str(moderator):
			if 'flair' in moderator.mod_permissions:
				print('I have flair permissions in ' + sub)
				return True

	return False

def getFlairTemplates(sub):
	subObj = reddit.subreddit(sub)
	flairs = []
	for template in subObj.flair.templates:
		flairs.append(template['css_class'])
	return flairs


def iterateMessageRequests():
	unreadMessages = reddit.inbox.unread(limit=None)
	# unread_messages = []

	# get any mod invites out of the way
	acceptModInvites()

	today = dt.datetime.today().strftime("%Y-%m-%d")

	for item in unreadMessages:

		if "username mention" in item.subject or item.was_comment:
			try:
				logging.warning("Mentioned in comment. Marking read.")
				item.mark_read()
				# item.reply("If you'd like to add me to your subreddit, read more [here](https://www.reddit.com/user/badge-bot/comments/imzh45/badgebot_is_in_beta_and_accepting_invites/)")
				print("Marked comment mention read.")
			except:
				item.mark_read()
				logging.critical("Tried to mark item that is not message instance read. Failed.")

		elif isinstance(item, Message):
			subreddit = cleanSubString(item.subject)
			body = str(item.body.lower())
			author = item.author
			print("New message from %s\n subject: %s \n body: %s " %(author, subreddit, body))
			logging.info("New message from %s\n subject: %s \n body: %s " %(author, subreddit, body))

			if not table_exists(subreddit):
				# if subreddit is not in database, check if we're a mod
				try:
					item.reply("Your subreddit is not in our database. Message your moderators or please invite u/badge-bot to moderate with flair permissions. If this is an error, contact u/huckingfoes by PM.")
					item.mark_read()
					logging.info("Replied to message.")
				except:
					logging.info("Tried to reply to message, but failed.")
					item.mark_read()


			elif table_exists(subreddit):

				if(checkValidMessage(item)):
				# if True:
					# logging.info("New valid message from: " + str(item.author))
					if body == "reset":
						logging.info("New badge request... giving badge.")
						updateDate(item.author, today, subreddit)
						item.mark_read()
						item.reply("Request honored. Your badge has been updated.")
					elif isValidDateStr(body):
						if int(daysSince(item.body)) > 2880:
							# dont allow for manually updating flairs more than 4 years
							logging.error("Replying to invalid date request")
							item.reply("You may only update a flair with up to 8 years in the past. Try again with a more recent date or contact moderators manually to update your flair accordingly.")
						else:
							b = updateDate(author, body, subreddit)
							if b == 0:
								item.error("Issue updating date. Probably permissions error.")
								item.reply("There may be a permissions issue in your subreddit. Ensure u/badge-bot has flair permissions.")
							item.reply("Update honored. Your badge has been updated.")
							logging.info("Updated badge.")

						item.mark_read()

					elif body == 'remove':
						logging.debug("Message is remove request.")
						removeFromDatabase(author, subreddit)
						logging.info("Removed " + str(author) + " from " + subreddit)
						removeFlair(author, subreddit)
						item.mark_read()
						item.reply("You've been removed from the badge database: " + subreddit)
						logging.info("Replied to remove request.")
				else:
					s = "Hello %s, your message is invalid: \n %s \n %s" % (item.author, item.subject, item.body)
					logging.debug(s)
					try:
						logging.info("Trying to reply to invalid message...")
						item.reply(s)
						logging.info("Sent reply: " + s)
					except:
						logging.info("Couldn't reply to invalid message. Marking as read.")

					item.mark_read()

		else:
			s = "Hello %s, your message is invalid: \n %s \n %s" % (item.author, item.subject, item.body)
			logging.error(s)
			try:
				item.reply(s)
			except:
				log.error("Couldn't reply to message. Marking read.")

			item.mark_read()

def getBadgeClass(sub, days):
	cssflairs = getFlairTemplates(sub)
	days = int(days)

	if days >= 30 and days < 60 and '30days' in cssflairs:
		return '30days'
	elif days >= 60 and days < 90 and '60days' in cssflairs:
		return '60days'
	elif days >= 90 and days < 180 and '90days' in cssflairs:
		return '180days'
	elif days >= 180 and days < 365 and '180days' in cssflairs:
		return '180days'
	elif days >= 365 and days < 730 and '1year' in cssflairs:
		return '1year'
	elif days >= 730 and '2years' in cssflairs:
		return '2years'
	else:
		return 'badge'
	logging.info('No colored badges found.')
	return 'badge'

def getBadgeText(daysDiff):
	daysDiff = int(daysDiff)
	# return str(daysDiff) + " days"
	if (daysDiff < 365):
		return str(daysDiff) + " days"
	elif daysDiff >= 365:
		numYears = int(daysDiff / 365)
		if numYears == 1:
			return str(numYears) + " year"
		else:
			return str(numYears) + " years"
	return str(daysDiff) + " days"


count = 0

while False:
	count += 1
	t = dt.datetime.today().strftime('%H:%M:%S')
	if count % 100 == 1:
		logging.info(t + " Checking messages.")
		print(t + " Still working")

	iterateMessageRequests()

	if time_between(dt.time(23,45), dt.time(00,15)):
		updateFlairsFromDatabase(db)

	time.sleep(30)
