import sqlite3
from random import randint


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
    def insert_new_location(self, location):
        sql_to_execute = "INSERT INTO location(prisoner_id, date, lat, lng) VALUES(?,?,?,?)"
        cursor = self.conn.cursor()
        time_format = '%Y-%m-%d %H:%M:%S.%f'
        record = (location.get_prisoner_id(), location.get_date().strftime(time_format), location.get_lat(), location.get_lng())
        print(record)
        cursor.execute(sql_to_execute, record)
        self.conn.commit()

    # insert new prisoner to database
    def insert_new_prisoner(self, prisoner, status=False):
        sql_to_execute = "INSERT INTO prisoners(prisoner_id, name, national_identifier, status) VALUES(?,?,?,?)"
        cursor = self.conn.cursor()
        record = (prisoner.get_prisoner_id(), prisoner.get_name(), prisoner.get_national_identifier(), status)
        cursor.execute(sql_to_execute, record)
        self.conn.commit()

    # get prisoner current locations list by prisoner_id
    def get_prisoner_locations(self, prisoner_id):
        cursor = self.conn.cursor()
        sql_to_execute = "select * from location where prisoner_id = ?"
        cursor.execute(sql_to_execute, (prisoner_id,))
        locations_list = cursor.fetchall()
        print(locations_list, prisoner_id)
        self.conn.commit()
        to_return = []
        for location in locations_list:
            """
            location:
            0 - location_id
            1 - prisoner_id
            2 - date
            3 - latitude
            4 - longitude
            """
            ready_location = Location(location_id=location[0], prisoner_id=location[1], date=location[2],
                                      lat=location[3], lng=location[4])
            to_return.append(ready_location)
        return to_return

    # get prisoner last location by prisoner_id
    def get_prisoner_last_location(self, prisoner_id):
        locations_list = self.get_prisoner_locations(prisoner_id)
        if len(locations_list) > 0:
            location = locations_list[-1]
            return location
        else:
            return None

    # get all prisoners as a list:
    def get_all_prisoners(self):
        cursor = self.conn.cursor()
        sql_to_execute = "select * from prisoners"
        cursor.execute(sql_to_execute)
        prisoners_list = cursor.fetchall()
        self.conn.commit()
        to_return = []
        for p in prisoners_list:
            """
            prisoner:
            0 - prisoner_id
            1 - name
            2 - national_identifier
            3 - prisoner_status
            """
            prisoner = Prisoner(prisoner_id=p[0], name=p[1], national_identifier=p[2],
                                prisoner_status=p[3])
            to_return.append(prisoner)
        return to_return

    # get prisoner`s personal data by prisoner_id
    def get_prisoner_personal_data(self, prisoner_id):
        cursor = self.conn.cursor()
        sql_to_execute = "select * from prisoners where prisoner_id = ?"
        cursor.execute(sql_to_execute, (prisoner_id,))
        prisoner_data_exist = cursor.fetchall()
        self.conn.commit()
        if len(prisoner_data_exist) > 0:
            prisoner_data = prisoner_data_exist[0]
            """
            prisoner:
            0 - prisoner_id
            1 - name
            2 - national_identifier
            3 - prisoner_status
            """
            prisoner = Prisoner(prisoner_id=prisoner_data[0], name=prisoner_data[1],
                                national_identifier=prisoner_data[2],
                                prisoner_status=prisoner_data[3])
            return prisoner
        else:
            return None

    # get prisoner`s personal data by national identifier
    def get_prisoner_personal_data_by_national_identifier(self, prisoner_national_id):
        cursor = self.conn.cursor()
        sql_to_execute = "select * from prisoners where national_identifier = ?"
        cursor.execute(sql_to_execute, (prisoner_national_id,))
        prisoner_data_exist = cursor.fetchall()
        self.conn.commit()
        """
        prisoner:
        0 - prisoner_id
        1 - name
        2 - national_identifier
        3 - prisoner_status
        """
        if len(prisoner_data_exist) > 0:
            prisoner_data = prisoner_data_exist[0]
            prisoner = Prisoner(prisoner_id=prisoner_data[0], name=prisoner_data[1],
                                national_identifier=prisoner_data[2],
                                prisoner_status=prisoner_data[3])
            return prisoner
        else:
            return None

    # get prisoner`s red circles
    def get_all_prisoner_red_circles(self, prisoner_id):
        cursor = self.conn.cursor()
        sql_to_execute = "select * from red_circles where prisoner_id = ?"
        cursor.execute(sql_to_execute, (prisoner_id,))
        prisoner_red_circles = cursor.fetchall()
        self.conn.commit()
        to_return = []
        for c in prisoner_red_circles:
            """
            circle:
            0 - circle_id
            1 - prisoner_id
            2 - radius
            3 - latitude
            4 - longitude
            5 - circle_type
            """
            circle = RedCircle(circle_id=c[0], prisoner_id=c[1], radius=c[2], lat=c[3], lng=c[4], circle_type=c[5])
            to_return.append(circle)
        return to_return

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
        # change the circles counter
        self.sequence_counter_change("location", -1)

    # remove red circle from prisoner
    def remove_prisoner(self, prisoner_id):
        # reduce the sequence of red circles by the number of circles deleted
        red_circles = self.get_all_prisoner_red_circles(prisoner_id)
        number_of_red_circles = len(red_circles)
        self.sequence_counter_change("red_circles", -number_of_red_circles)

        # reduce the sequence of location by the number of locations deleted
        locations = self.get_prisoner_locations(prisoner_id)
        number_of_locations = len(locations)
        self.sequence_counter_change("location", -number_of_locations)

        # remove prisoner from prisoners table
        sql_to_execute = "DELETE FROM prisoners WHERE prisoner_id = ?;"
        cursor = self.conn.cursor()
        cursor.execute(sql_to_execute, (prisoner_id,))
        self.conn.commit()

        # remove red circles from red_circles table
        sql_to_execute_2 = "DELETE FROM red_circles WHERE prisoner_id = ?;"
        cursor.execute(sql_to_execute_2, (prisoner_id,))
        self.conn.commit()

        # remove locations from locations table
        sql_to_execute_3 = "DELETE FROM location WHERE prisoner_id = ?;"
        cursor.execute(sql_to_execute_3, (prisoner_id,))
        self.conn.commit()

    # change sequence counter
    def sequence_counter_change(self, line, change_by):
        try:
            # gets the current number
            cursor = self.conn.cursor()
            sql_to_execute = "select * from sqlite_sequence WHERE name = ?"
            cursor.execute(sql_to_execute, (line,))
            # the 0 - the data comes in a list of one tuple, if the list is empty (no sequence table exist)
            # that means the UI had`t opened once
            current_status = cursor.fetchall()[0]
            self.conn.commit()

            # change the number
            sql_to_execute_2 = "UPDATE sqlite_sequence SET seq = ? WHERE name = ?;"
            record_2 = (int(current_status[1]) + change_by, line)
            cursor.execute(sql_to_execute_2, record_2)
            self.conn.commit()
        except:
            pass

    # creating new id for new prisoner
    def get_new_id(self):
        random_id = randint(10000000, 99999999)
        for current_prisoner in self.get_all_prisoners():
            if current_prisoner.get_prisoner_id() == random_id:
                return self.get_new_id()
            else:
                pass
        return random_id


class RedCircle:
    def __init__(self, circle_id, prisoner_id, radius, lat, lng, circle_type):
        self.__circle_id = circle_id
        self.__prisoner_id = prisoner_id
        self.__radius = radius
        self.__lat = lat
        self.__lng = lng
        self.__circle_type = circle_type

    def get_circle_id(self):
        return self.__circle_id

    def get_prisoner_id(self):
        return self.__prisoner_id

    def get_radius(self):
        return self.__radius

    def get_lat(self):
        return self.__lat

    def get_lng(self):
        return self.__lng

    def get_circle_type(self):
        return self.__circle_type

    def get_circle_listed(self):
        circle = [self.__circle_id, self.__prisoner_id, self.__radius,
                  self.__lat, self.__lng, self.__circle_type]
        return circle


class Location:

    def __init__(self, location_id, prisoner_id, date, lat, lng):
        self.__location_id = location_id
        self.__prisoner_id = int(prisoner_id)
        self.__date = date
        self.__lat = lat
        self.__lng = lng

    def get_location_id(self):
        return self.__location_id

    def get_prisoner_id(self):
        return self.__prisoner_id

    def get_date(self):
        return self.__date

    def get_lat(self):
        return self.__lat

    def get_lng(self):
        return self.__lng


class Prisoner:
    def __init__(self, prisoner_id, name, national_identifier, prisoner_status):
        self.__prisoner_id = int(prisoner_id)
        self.__name = name
        self.__national_identifier = int(national_identifier)
        self.__prisoner_status = prisoner_status

    def get_prisoner_id(self):
        return self.__prisoner_id

    def get_name(self):
        return self.__name

    def get_national_identifier(self):
        return self.__national_identifier

    def get_status(self):
        return self.__prisoner_status

    def get_prisoner_listed(self):
        prisoner = [self.__prisoner_id, self.__name,
                    self.__national_identifier, self.__prisoner_status]
        return prisoner
