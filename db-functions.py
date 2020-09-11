
# Database Helpers
def create_table(subreddit):
	# connects to a db and creates new table for subreddit
	subredditString = cleanSubredditString(subreddit)
	conn = sqlite3.connect(db)
	c = conn.cursor()
	c.execute('CREATE TABLE IF NOT EXISTS ' + subredditString + ' (username TEXT NOT NULL, badgedate TEXT NOT NULL, dateadded TEXT NOT NULL);')

	conn.commit()
	conn.close()
	logging.info('Created table: ' + subredditString)

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
			# logging.info("Table exists: " + tableName)
			return True
		else:
			# table doesn't exist
			# logging.info("Table does not exist: " + tableName)
			return False
		conn.commit()
		conn.close()
	except Exception as e:
		logging.critical(e)
		logging.critical("Exception occurred", exc_info=True)
		
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
			# logging.info("isInDatabase(): User exists, returning true.")
			conn.commit()
			conn.close()
			return True

		elif len(rows) == 0:
			# user does not exist, we can insert a new row in the db and update flair
			conn.commit()
			conn.close()
			return False
		else:
			logging.critical("Exception occurred", exc_info=True)
			logging.critical("isInDatabase(): Returning -1")
			conn.commit()
			conn.close()
			return -1
	except Exception as e:
		logging.error("isInDatabase() encountered an error.")
		logging.critical(e)
		logging.critical("Exception occurred", exc_info=True)

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
			logging.info("Updating badges for " + str(x[0]))
			updateAllBadges(x[0])


	except sqlite3.Error as e:
		logging.critical('Db Not found', str(e))
		logging.critical("Exception occurred", exc_info=True)