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
            result = self.cursor.execute("SELECT * FROM `main` WHERE `id` = ?", (id,)).fetchall()
        return bool(len(result))

    def register(self, name, id, contact):  # maybe exclude username
        """
        Registration of a user
        """
        with self.connection:
            return self.cursor.execute("INSERT INTO `main` VALUES (?, ?, ?)", (name, id, contact))

    def tracked_id(self, contact):
        """
        Find id of a tracked person
        """
        with self.connection:
            return self.cursor.execute("SELECT id FROM `main` WHERE `contact` = ?", (contact,)).fetchall()

    def get_name(self, id):
        """
        Finds name of a person by his id
        """
        with self.connection:
            return self.cursor.execute("SELECT name FROM `main` WHERE `id` = ?", (id,)).fetchall()

    def get_contact(self, id):
        """
        Finds contact of a person by his id
        """
        with self.connection:
            return self.cursor.execute("SELECT contact FROM `main` WHERE `id` = ?", (id,)).fetchall()


    def delete_account(self, id):
        """
        Deletes a user from a database
        """
        with self.connection:
            return self.cursor.execute("DELETE FROM `main` WHERE `id` = ?", (id,)).fetchall()

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
            return self.cursor.execute("SELECT `name` FROM `main` WHERE `contact` = ?", (phone_number,)).fetchall()

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
            return self.cursor.execute("SELECT `contact_trackable` FROM `tracking_trackable` WHERE `id_tracking` = ? ORDER BY `counter` DESC LIMIT 3", (tracking_id,)).fetchall()

    def get_contact_check(self, tracking_id, trackable_name):
        """
        Retrieves all trackable people by tracking_id
        """
        with self.connection:
            return self.cursor.execute("SELECT `contact_trackable` FROM `tracking_trackable` WHERE `id_tracking` = ? AND `trackable_name` = ?", (tracking_id, trackable_name,)).fetchall()

    def add_id_message(self, message_id, sending_id, receiving_id):
        """
        Adds two users and message id to the table live_location_id
        """
        with self.connection:
            return self.cursor.execute("INSERT INTO `live_location_id` VALUES (?, ?, ?)", (message_id, sending_id, receiving_id)).fetchall()

    def add_to_received_emoji(self, id_received, id_sent):
        """
        Adds user to `received_emoji` table
        """
        with self.connection:
            return self.cursor.execute("INSERT INTO `received_emoji` VALUES (?, ?, ?)", (id_received, id_sent, 1)).fetchall()

    def existence_received_emoji(self, id_received):
        """
        Checks existence in table `received_emoji`
        """
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `received_emoji` WHERE `id_received` = ?", (id_received,)).fetchall()
        return bool(result)

    def increase_received_emoji_counter(self, received_id, sent_id):
        """
        Receives number of emojis by 1
        """
        with self.connection:
            return self.cursor.execute("UPDATE `received_emoji` SET `count` = `count` + 1 WHERE `id_received` = ? AND `id_sent` = ?", (received_id, sent_id,)).fetchall()

    def count_emojis(self, received_id):
        """
        Counts number of all received emojis
        """
        with self.connection:
            return self.cursor.execute("SELECT COUNT(`count`), `id_received` FROM `received_emoji` WHERE `id_received` = ? GROUP BY `id_received`",(received_id, )).fetchall()