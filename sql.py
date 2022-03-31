import sqlite3


class SQL:
    def __init__(self, database_file):
        """
        Connecting to the database
        """
        self.connection = sqlite3.connect(database_file)
        self.cursor = self.connection.cursor()

    def user_exists(self, id):
        """
        Searching a given person in the database
        """
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `users` WHERE `id` = ?", (id,)).fetchall()
        return bool(len(result))

    def register(self, name, id, contact):  # maybe exclude username
        """
        Registration of a user
        """
        with self.connection:
            return self.cursor.execute("INSERT INTO `users` VALUES (?, ?, ?)", (name, id, contact))

    def tracked_id(self, contact):
        """
        Find id of a tracked person
        """
        with self.connection:
            return self.cursor.execute("SELECT id FROM `users` WHERE `contact` = ?", (contact,)).fetchall()

    def get_name(self, id):
        """
        Finds name of a person by his id
        """
        with self.connection:
            return self.cursor.execute("SELECT name FROM `users` WHERE `id` = ?", (id,)).fetchall()

    def get_contact(self, id):
        """
        Finds contact of a person by his id
        """
        with self.connection:
            return self.cursor.execute("SELECT contact FROM `users` WHERE `id` = ?", (id,)).fetchall()

    def add_to_tracking_trackable(self, id_tracking, tracking, id_trackable, trackable, name):
        """
        Registration of a user
        """
        with self.connection:
            return self.cursor.execute("INSERT INTO `tracking_trackable` VALUES (?, ?, ?, ?, ?, ?)", (id_tracking, tracking, id_trackable, trackable, name, 1))

    def get_first_name(self, phone_number):
        """
         Finds a name by a phone_number
        """
        with self.connection:
            return self.cursor.execute("SELECT `name` FROM `users` WHERE `contact` = ?", (phone_number,)).fetchall()

    def increase_counter(self, tracking_number, trackable_number):
        """
        Increases counter by adding 1
        """
        with self.connection:
            return self.cursor.execute("UPDATE `tracking_trackable` SET `counter` = `counter` + 1 WHERE `contact_tracking` = ? AND `contact_trackable` = ?", (tracking_number, trackable_number,)).fetchall()


    def user_existance(self, tracking, trackable):
        """
        Searching a given person in the database
        """
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `tracking_trackable` WHERE `id_tracking` = (?) AND `id_trackable` = (?)", (tracking, trackable)).fetchall()
        return bool(len(result))

    def tracking_existance(self, tracking_id):
        """
        Check whether a person is in database `tracking_trackable` or not
        """
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `tracking_trackable` WHERE `id_tracking` = ?", (tracking_id,)).fetchall()
        return bool(len(result))

    def get_trackable(self, tracking_id):
        """
        Retrieves all trackable people by tracking_id
        """
        with self.connection:
            return self.cursor.execute("SELECT `contact_trackable`"
                                       " FROM `tracking_trackable`"
                                       " WHERE `id_tracking` = ?"
                                       " ORDER BY `counter` DESC LIMIT 5", (tracking_id,)).fetchall()

    def get_contact_check(self, tracking_id, trackable_name):
        """
        Retrieves all trackable people by tracking_id
        """
        with self.connection:
            return self.cursor.execute("SELECT `contact_trackable` FROM `tracking_trackable` WHERE `id_tracking` = ? AND `trackable_name` = ?", (tracking_id, trackable_name,)).fetchall()

    def add_to_received_emoji_if_victory(self, id_received, id_sent):
        """
        Adds user to `received_emoji` table
        """
        with self.connection:
            return self.cursor.execute("INSERT INTO `received_emoji` VALUES (?, ?, 1, 0, 0, 0, 0, 0)", (id_received, id_sent,)).fetchall()

    def add_to_received_emoji_if_snowflake(self, id_received, id_sent):
        """
        Adds user to `received_emoji` table
        """
        with self.connection:
            return self.cursor.execute("INSERT INTO `received_emoji` VALUES (?, ?, 0, 0, 1, 0, 0, 0)", (id_received, id_sent,)).fetchall()

    def add_to_received_emoji_if_cold(self, id_received, id_sent):
        """
        Adds user to `received_emoji` table
        """
        with self.connection:
            return self.cursor.execute("INSERT INTO `received_emoji` VALUES (?, ?, 0, 1, 0, 0, 0, 0)", (id_received, id_sent,)).fetchall()

    def add_to_received_emoji_if_snowman(self, id_received, id_sent):
        """
        Adds user to `received_emoji` table
        """
        with self.connection:
            return self.cursor.execute("INSERT INTO `received_emoji` VALUES (?, ?, 0, 0, 0, 1, 0)", (id_received, id_sent,)).fetchall()

    def add_to_received_emoji_if_swear(self, id_received, id_sent):
        """
        Adds user to `received_emoji` table
        """
        with self.connection:
            return self.cursor.execute("INSERT INTO `received_emoji` VALUES (?, ?, 0, 0, 0, 0, 0, 1)",
                                       (id_received, id_sent,)).fetchall()

    def add_to_received_emoji_if_like(self, id_received, id_sent):
        """
        Adds user to `received_emoji` table
        """
        with self.connection:
            return self.cursor.execute("INSERT INTO `received_emoji` VALUES (?, ?, 0, 0, 0, 1, 0, 0)",
                                       (id_received, id_sent,)).fetchall()


    def add_to_received_emoji_if_fire(self, id_received, id_sent):
        """
        Adds user to `received_emoji` table
        """
        with self.connection:
            return self.cursor.execute("INSERT INTO `received_emoji` VALUES (?, ?, 0, 0, 0, 0, 1, 0)", (id_received, id_sent,)).fetchall()

    def existence_received_emoji(self, id_received, id_sent):
        """
        Checks existence in table `received_emoji`
        """
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `received_emoji` WHERE `id_received` = ? AND id_sent = ?", (id_received, id_sent, )).fetchall()
        return bool(result)

    def increase_received_victory_emoji_counter(self, received_id, sent_id):
        """
        Increases number of victory emojis by 1
        """
        with self.connection:
            return self.cursor.execute("UPDATE `received_emoji` SET `count_victory` = `count_victory` + 1 WHERE `id_received` = ? AND `id_sent` = ?", (received_id, sent_id,)).fetchall()

    def increase_received_cold_emoji_counter(self, received_id, sent_id):
        """
        Increases number of cold emojis by 1
        """
        with self.connection:
            return self.cursor.execute("UPDATE `received_emoji` SET `count_cold` = `count_cold` + 1 WHERE `id_received` = ? AND `id_sent` = ?", (received_id, sent_id,)).fetchall()

    def increase_received_snowflake_emoji_counter(self, received_id, sent_id):
        """
        Increases number of snowflake emojis by 1
        """
        with self.connection:
            return self.cursor.execute("UPDATE `received_emoji` SET `count_snowflake` = `count_snowflake` + 1 WHERE `id_received` = ? AND `id_sent` = ?", (received_id, sent_id,)).fetchall()

    def increase_received_snowman_emoji_counter(self, received_id, sent_id):
        """
        Increases number of snowman emojis by 1
        """
        with self.connection:
            return self.cursor.execute("UPDATE `received_emoji` SET `count_snowman` = `count_snowman` + 1 WHERE `id_received` = ? AND `id_sent` = ?", (received_id, sent_id,)).fetchall()

    def increase_received_fire_emoji_counter(self, received_id, sent_id):
        """
        Increases number of fire emojis by 1
        """
        with self.connection:
            return self.cursor.execute("UPDATE `received_emoji` SET `count_fire` = `count_fire` + 1 WHERE `id_received` = ? AND `id_sent` = ?", (received_id, sent_id,)).fetchall()

    def increase_received_like_emoji_counter(self, received_id, sent_id):
        """
        Increases number of like emojis by 1
        """
        with self.connection:
            return self.cursor.execute("UPDATE `received_emoji` SET `count_like` = `count_like` + 1 WHERE `id_received` = ? AND `id_sent` = ?", (received_id, sent_id,)).fetchall()

    def increase_received_swear_counter(self, received_id, sent_id):
        """
        Increases number of swear emojis by 1
        """
        with self.connection:
            return self.cursor.execute("UPDATE `received_emoji` SET `count_swear` = `count_swear` + 1 WHERE `id_received` = ? AND `id_sent` = ?", (received_id, sent_id,)).fetchall()


    def count_received_emojis_victory(self, received_id):
        """
        Counts number of all received victory emojis
        """
        with self.connection:
            return self.cursor.execute("WITH `count_emojis` AS"
                                       "(SELECT SUM(`count_victory`) as number, `id_received`"
                                       "FROM `received_emoji`"
                                       "GROUP BY `id_received`)"
                                       "SELECT `number`"
                                       "FROM `count_emojis`"
                                       "WHERE `id_received` = ?",(received_id, )).fetchall()

    def count_received_emojis_snowflake(self, received_id):
        """
        Counts number of all received snowflake emojis
        """
        with self.connection:
            return self.cursor.execute("WITH `count_emojis` AS"
                                       "(SELECT SUM(`count_snowflake`) as number, `id_received`"
                                       "FROM `received_emoji`"
                                       "GROUP BY `id_received`)"
                                       "SELECT `number`"
                                       "FROM `count_emojis`"
                                       "WHERE `id_received` = ?",(received_id, )).fetchall()

    def count_received_emojis_cold(self, received_id):
        """
        Counts number of all received cold emojis
        """
        with self.connection:
            return self.cursor.execute("WITH `count_emojis` AS"
                                       "(SELECT SUM(`count_cold`) as number, `id_received`"
                                       "FROM `received_emoji`"
                                       "GROUP BY `id_received`)"
                                       "SELECT `number`"
                                       "FROM `count_emojis`"
                                       "WHERE `id_received` = ?",(received_id, )).fetchall()

    def count_received_emojis_snowman(self, received_id):
        """
        Counts number of all received snowman emojis
        """
        with self.connection:
            return self.cursor.execute("WITH `count_emojis` AS"
                                       "(SELECT SUM(`count_snowman`) as number, `id_received`"
                                       "FROM `received_emoji`"
                                       "GROUP BY `id_received`)"
                                       "SELECT `number`"
                                       "FROM `count_emojis`"
                                       "WHERE `id_received` = ?",(received_id, )).fetchall()

    def count_received_emojis_swear(self, received_id):
        """
        Counts number of all received swear emojis
        """
        with self.connection:
            return self.cursor.execute("WITH `count_emojis` AS"
                                       "(SELECT SUM(`count_swear`) as number, `id_received`"
                                       "FROM `received_emoji`"
                                       "GROUP BY `id_received`)"
                                       "SELECT `number`"
                                       "FROM `count_emojis`"
                                       "WHERE `id_received` = ?",(received_id, )).fetchall()

    def count_received_emojis_fire(self, received_id):
        """
        Counts number of all received fire emojis
        """
        with self.connection:
            return self.cursor.execute("WITH `count_emojis` AS"
                                       "(SELECT SUM(`count_fire`) as number, `id_received`"
                                       "FROM `received_emoji`"
                                       "GROUP BY `id_received`)"
                                       "SELECT `number`"
                                       "FROM `count_emojis`"
                                       "WHERE `id_received` = ?",(received_id, )).fetchall()

    def count_received_emojis_like(self, received_id):
        """
        Counts number of all received like emojis
        """
        with self.connection:
            return self.cursor.execute("WITH `count_emojis` AS"
                                       "(SELECT SUM(`count_like`) as number, `id_received`"
                                       "FROM `received_emoji`"
                                       "GROUP BY `id_received`)"
                                       "SELECT `number`"
                                       "FROM `count_emojis`"
                                       "WHERE `id_received` = ?",(received_id, )).fetchall()

    def count_sent_emojis_victory(self, received_id):
        """
        Counts number of received victory emojis
        """
        with self.connection:
            return self.cursor.execute("WITH `count_emojis` AS"
                                       "(SELECT SUM(`count_victory`) as number, `id_sent`"
                                       "FROM `received_emoji`"
                                       "GROUP BY `id_sent`)"
                                       "SELECT `number`"
                                       "FROM `count_emojis`"
                                       "WHERE `id_sent` = ?",(received_id, )).fetchall()

    def count_sent_emojis_snowflake(self, received_id):
        """
        Counts number of received snowflake emojis
        """
        with self.connection:
            return self.cursor.execute("WITH `count_emojis` AS"
                                       "(SELECT SUM(`count_snowflake`) as number, `id_sent`"
                                       "FROM `received_emoji`"
                                       "GROUP BY `id_sent`)"
                                       "SELECT `number`"
                                       "FROM `count_emojis`"
                                       "WHERE `id_sent` = ?",(received_id, )).fetchall()

    def count_sent_emojis_cold(self, received_id):
        """
        Counts number of received cold emojis
        """
        with self.connection:
            return self.cursor.execute("WITH `count_emojis` AS"
                                       "(SELECT SUM(`count_cold`) as number, `id_sent`"
                                       "FROM `received_emoji`"
                                       "GROUP BY `id_sent`)"
                                       "SELECT `number`"
                                       "FROM `count_emojis`"
                                       "WHERE `id_sent` = ?",(received_id, )).fetchall()

    def count_sent_emojis_fire(self, received_id):
        """
        Counts number of received fire emojis
        """
        with self.connection:
            return self.cursor.execute("WITH `count_emojis` AS"
                                       "(SELECT SUM(`count_fire`) as number, `id_sent`"
                                       "FROM `received_emoji`"
                                       "GROUP BY `id_sent`)"
                                       "SELECT `number`"
                                       "FROM `count_emojis`"
                                       "WHERE `id_sent` = ?",(received_id, )).fetchall()

    def count_sent_emojis_snowman(self, received_id):
        """
        Counts number of received snowman emojis
        """
        with self.connection:
            return self.cursor.execute("WITH `count_emojis` AS"
                                       "(SELECT SUM(`count_snowman`) as number, `id_sent`"
                                       "FROM `received_emoji`"
                                       "GROUP BY `id_sent`)"
                                       "SELECT `number`"
                                       "FROM `count_emojis`"
                                       "WHERE `id_sent` = ?",(received_id, )).fetchall()

    def count_sent_emojis_like(self, received_id):
        """
        Counts number of received like emojis
        """
        with self.connection:
            return self.cursor.execute("WITH `count_emojis` AS"
                                       "(SELECT SUM(`count_like`) as number, `id_sent`"
                                       "FROM `received_emoji`"
                                       "GROUP BY `id_sent`)"
                                       "SELECT `number`"
                                       "FROM `count_emojis`"
                                       "WHERE `id_sent` = ?",(received_id, )).fetchall()

    def count_sent_emojis_swear(self, received_id):
        """
        Counts number of received swear emojis
        """
        with self.connection:
            return self.cursor.execute("WITH `count_emojis` AS"
                                       "(SELECT SUM(`count_swear`) as number, `id_sent`"
                                       "FROM `received_emoji`"
                                       "GROUP BY `id_sent`)"
                                       "SELECT `number`"
                                       "FROM `count_emojis`"
                                       "WHERE `id_sent` = ?",(received_id, )).fetchall()

    def existence_received_emoji_user_received(self, id_received):
        """
        Checks existence in table `received_emoji`
        """
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `received_emoji` WHERE `id_received` = ?", (id_received,)).fetchall()
        return bool(result)

    def existence_received_emoji_user_sent(self, id_sent):
        """
        Checks existence in table `received_emoji`
        """
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `received_emoji` WHERE `id_sent` = ?", (id_sent,)).fetchall()
        return bool(result)

    def add_location_name(self, client_id, location_name, longitude, latitude):
        """
        Appending location information in `fav_locations`
        """
        with self.connection:
            return self.cursor.execute("INSERT INTO `fav_locations` VALUES (?, ?, ?, ?)", (client_id, location_name, longitude, latitude))

    def existence_fav_locations(self, client_id):
        """
        Checking an existence in table `fav_locations`
        """
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `fav_locations` WHERE `id` = ?", (client_id, )).fetchall()
            return bool(result)

    def coordinates(self, client_id):
        """
        Retrieving coordinates of a person's locations
        """
        with self.connection:
            with self.connection:
                return self.cursor.execute("SELECT `location_name`, `longitude`, `latitude`"
                                           "FROM `fav_locations`"
                                           "WHERE `id` = ?", (client_id, )).fetchall()

    def ids(self):
        """
        Retrieving all id's of users
        """
        with self.connection:
            return self.cursor.execute("SELECT `id` FROM `users`").fetchall()