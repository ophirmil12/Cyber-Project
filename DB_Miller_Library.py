import sqlite3

# table for each prisoner
# row for each location check


class Database:

    def __init__(self, file_name):
        # open database file
        self.conn = sqlite3.connect(file_name, check_same_thread=False)
        self.create_location_table()
        self.create_red_circles_table()
        self.create_prisoners_table()

    # auto function, works when create Database object
    def create_location_table(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS location
                ( location_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,  
                prisoner_id INT NOT NULL, 
                date TEXT NOT NULL, 
                lat REAL NOT NULL, 
                lng REAL NOT NULL )''')

    # auto function, works when create Database object
    def create_red_circles_table(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS red_circles
                ( circle_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,  
                prisoner_id INT NOT NULL, 
                radius REAL NOT NULL, 
                lat REAL NOT NULL, 
                lng REAL NOT NULL, 
                type TEXT NOT NULL)''')

    # auto function, works when create Database object
    def create_prisoners_table(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS prisoners
                        ( prisoner_id INTEGER PRIMARY KEY NOT NULL,  
                        name TEXT NOT NULL, 
                        national_identifier INT, 
                        status NUMERIC NOT NULL )''')

    # close database file, and emptying all tables
    def disconnect_to_data_base(self):
        my_tables = ["location, red_circles, prisoners"]
        for table in my_tables:
            sql_to_execute = "DELETE FROM ?"
            cursor = self.conn.cursor()
            cursor.execute(sql_to_execute, table)
            self.conn.commit()
        self.conn.close()
        print("Closed database successfully")

    # insert new location to database
    def insert_new_location(self, prisoner_id, date, lat, lng):
        sql_to_execute = "INSERT INTO location(prisoner_id, date, lat, lng) VALUES(?,?,?,?)"
        cursor = self.conn.cursor()
        record = (prisoner_id, date, lat, lng)
        cursor.execute(sql_to_execute, record)
        self.conn.commit()

    # insert new prisoner to database
    def insert_new_prisoner(self, prisoner_id, name, national_identifier, status=False):
        sql_to_execute = "INSERT INTO prisoners(prisoner_id, name, national_identifier, status) VALUES(?,?,?,?)"
        cursor = self.conn.cursor()
        record = (prisoner_id, name, national_identifier, status)
        cursor.execute(sql_to_execute, record)
        self.conn.commit()

    # get prisoner current locations list by prisoner_id
    def get_prisoner_locations(self, prisoner_id):
        cursor = self.conn.cursor()
        sql_to_execute = "select * from location where prisoner_id = ?"
        cursor.execute(sql_to_execute, (prisoner_id, ))
        locations_list = cursor.fetchall()
        self.conn.commit()
        return locations_list

    # get all prisoners as a list:
    def get_all_prisoners(self):
        cursor = self.conn.cursor()
        sql_to_execute = "select * from prisoners"
        cursor.execute(sql_to_execute)
        prisoners_list = cursor.fetchall()
        self.conn.commit()
        return prisoners_list

    # get prisoner`s personal data
    def get_prisoner_personal_data(self, prisoner_id):
        cursor = self.conn.cursor()
        sql_to_execute = "select * from prisoners where prisoner_id = ?"
        cursor.execute(sql_to_execute, (prisoner_id, ))
        prisoner_personal_data = cursor.fetchall()
        self.conn.commit()
        return prisoner_personal_data

    # get prisoner`s red circles
    def get_all_prisoner_red_circles(self, prisoner_id):
        cursor = self.conn.cursor()
        sql_to_execute = "select * from red_circles where prisoner_id = ?"
        cursor.execute(sql_to_execute, (prisoner_id,))
        prisoner_red_circles = cursor.fetchall()
        self.conn.commit()
        return prisoner_red_circles

    # change prisoner`s status
    def change_prisoner_status(self, prisoner_id, new_status):
        sql_to_execute = "UPDATE prisoners SET status = ? WHERE prisoner_id = ?;"
        cursor = self.conn.cursor()
        record = (new_status, prisoner_id)
        cursor.execute(sql_to_execute, record)
        self.conn.commit()

    # add red circle to prisoner
    def add_red_circle(self, prisoner_id, radius, lat, lng, circle_type):
        sql_to_execute = "INSERT INTO red_circles(prisoner_id, radius, lat, lng, type) VALUES(?,?,?,?,?)"
        cursor = self.conn.cursor()
        record = (prisoner_id, radius, lat, lng, circle_type)
        cursor.execute(sql_to_execute, record)
        self.conn.commit()

    # remove red circle from prisoner
    def remove_red_circle(self, prisoner_id, lat, lng):
        sql_to_execute = "DELETE FROM red_circles WHERE prisoner_id = ? AND lat = ? AND lng = ?;"
        cursor = self.conn.cursor()
        record = (prisoner_id, lat, lng)
        cursor.execute(sql_to_execute, record)
        self.conn.commit()

    # change prisoner`s personal data?
