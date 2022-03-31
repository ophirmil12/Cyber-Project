# imports:
from flask import Flask, request, send_from_directory
import json
import DB_Miller_Library as DB
from _datetime import datetime, timedelta
import Distance_Library as Distance
import os

# flask argument
app = Flask(__name__)

# constants
LOCATIONS_MINUTES_GAP_CHECK = 1
LOCAL_HOST = '0.0.0.0'


def get_prisoner_data_and_current_location_and_red_circles(content, db):
    try:
        """
        data_to_return:
            0: ID
            1: name
            2: national_ID
            3: last_location[lat, lng]
            4: last_location_time
            5: status
            6: red_circles[[circle_id, prisoner_id, radius, lat, lng, type], [], []...]
        """
        prisoner_id = content["input"]
        try:
            # getting the required from the database
            prisoner_data = db.get_prisoner_personal_data(prisoner_id)
            prisoner_last_location = db.get_prisoner_last_location(prisoner_id)
            prisoner_red_circles = db.get_all_prisoner_red_circles(prisoner_id)
            # checking that all the data exist
            if prisoner_last_location is not None and prisoner_data is not None and prisoner_red_circles is not None:
                prisoner_red_circles_ready = []
                # assembling the data to sending
                for circle in prisoner_red_circles:
                    prisoner_red_circles_ready.append(circle.get_circle_listed())
                data_to_return = [prisoner_id, prisoner_data.get_name(), prisoner_data.get_national_identifier(),
                                  [prisoner_last_location.get_lat(), prisoner_last_location.get_lng()],
                                  prisoner_last_location.get_date(), prisoner_data.get_status(),
                                  prisoner_red_circles_ready]
                # sending the data
                return json.dumps(data_to_return)
            else:
                return "No prisoner in the system"

        except IndexError:
            return "No Location Measured Yet"
    except:
        # TODO i got error "submit error", why?
        return "Submit Prisoner Error"


# return list of all prisoners
def get_all_prisoners(db):
    try:
        # getting all the prisoners from the database
        prisoners_data = db.get_all_prisoners()
        ret_list = []
        # assembling the list of prisoners in pure data, not Prisoner variable
        for prisoner_ret in prisoners_data:
            listed_prisoner = [prisoner_ret.get_prisoner_id(), prisoner_ret.get_name(),
                               prisoner_ret.get_national_identifier(), prisoner_ret.get_status()]
            ret_list.append(listed_prisoner)
        # sending the data
        return json.dumps(ret_list)
    except:
        return "LoadingAllPrisonersForListError"


# HERE HAPPENS ALL THE MAGIC!
def get_all_problems_and_new_alerts(db):
    try:
        all_new_log_data = []
        # running through all prisoners
        for prisoner_data in db.get_all_prisoners():
            # now, we will check if the prisoner is in unwanted place

            prisoner_id = prisoner_data.get_prisoner_id()

            # getting all the prisoner`s red circles
            all_red_circles = db.get_all_prisoner_red_circles(prisoner_id)
            prisoner_last_location = db.get_prisoner_last_location(prisoner_id)
            # TODO prisoner_last_location might be None (no location measured yet)

            if prisoner_last_location is not None and all_red_circles is not None:
                # getting the prisoner`s last timestamp and current timestamp
                last_timestamp = prisoner_last_location.get_date()
                current_time = str(datetime.now())
                time_format = '%Y-%m-%d %H:%M:%S.%f'
                prisoner_time_delta = datetime.strptime(current_time, time_format) - datetime.strptime(last_timestamp,
                                                                                                       time_format)

                # the problem checker - if bigger than 0 - problem
                is_problem = 0

                # running through all the red circles
                for red_circle in all_red_circles:
                    circle_position = (red_circle.get_lat(), red_circle.get_lng())
                    prisoner_position = (prisoner_last_location.get_lat(), prisoner_last_location.get_lng())
                    if Distance.coordinate_dis(circle_position, prisoner_position) <= red_circle.get_radius():
                        # the prisoner is in the circle
                        if red_circle.get_circle_type() == "1":
                            # Not allowed in the circle - Problem
                            is_problem += 1
                        else:
                            # allowed only in the circle - Good
                            is_problem += 0
                    else:
                        # the prisoner is out of the circle
                        if red_circle.get_circle_type() == "1":
                            # Not allowed in the circle - Good
                            is_problem += 0
                        else:
                            # allowed only in the circle - Problem
                            is_problem += 1

                # checking if the client didn't sent location for a while
                if prisoner_time_delta > timedelta(minutes=LOCATIONS_MINUTES_GAP_CHECK):
                    is_problem += 1
                else:
                    is_problem += 0

                # finally - checking the problem checker
                if is_problem >= 1:
                    db.change_prisoner_status(prisoner_id, new_status=1)
                else:
                    db.change_prisoner_status(prisoner_id, new_status=0)
                # adding the current prisoner to the list
                all_new_log_data.append(prisoner_data.get_prisoner_listed())

            else:
                db.change_prisoner_status(prisoner_id, new_status=1)
                all_new_log_data.append(prisoner_data.get_prisoner_listed())

        return json.dumps(all_new_log_data)
    except:
        return "LogError"


def add_or_remove_red_circle(content, db):
    try:
        data = json.loads(content["input"])
        """
        data:
        0 - prisoner_id
        1 - latitude
        2 - longitude
        3 - add/remove circle
        4 - radius
        5 - circle_type
        """
        # opening data and creating RedCircle
        add_remove_type = data[3]
        red_circle_data = DB.RedCircle(None, prisoner_id=data[0], radius=data[4], lat=data[1], lng=data[2],
                                       circle_type=data[5])

        # function - adding
        if add_remove_type == "ADD":
            # checking radius
            if int(red_circle_data.get_radius()) > 0:
                db.add_red_circle(red_circle_data.get_prisoner_id(), red_circle_data.get_radius(),
                                  red_circle_data.get_lat(), red_circle_data.get_lng(),
                                  red_circle_data.get_circle_type())
                return "Added Circle"
            else:
                return "Radius Can`t be 0 or negative! (Error)"
        # function - removing
        elif add_remove_type == "REMOVE":
            try:
                db.remove_red_circle(red_circle_data.get_prisoner_id(), red_circle_data.get_lat(),
                                     red_circle_data.get_lng())
                return "Removed Circle"
            except:
                return "Data Base Error!"
        else:
            return "No Such Command! (Error)"
    except:
        return "Value Error!"


def new_prisoner(content, db):
    try:
        data = json.loads(content["input"])
        """
        data:
        0 - prisoner_id
        1 - name
        """
        prisoner_data = DB.Prisoner(prisoner_id=data[0], name=data[1], national_identifier=data[0], prisoner_status=False)
        # inserting the new prisoner into the server
        db.insert_new_prisoner(prisoner_data, status=False)
        return "Good"
    except:
        return "ValueError"


def prisoner_new_location(content, db):
    try:
        data = json.loads(content["input"])
        """
        data:
        0 - prisoner_id
        1 - latitude
        2 - longitude
        """
        # creating timestamp
        date = datetime.now()
        # loading the data that received
        prisoner_id = data[0]
        check = 0
        all_prisoners = db.get_all_prisoners()
        for prisoner_check in all_prisoners:
            # that means that the prisoner still exist
            if prisoner_check.get_prisoner_id() == int(prisoner_id):
                check += 1
        if check == 1:
            location_data = DB.Location(location_id=None, prisoner_id=data[0], date=date, lat=data[1], lng=data[2])
            # inserting the new location into the database
            db.insert_new_location(location_data)
            return "Good"
        else:
            return "The prisoner deleted"
    except:
        return "LocationError"


def prisoner_unknown_location(content, db):
    prisoner_id = json.loads(content["input"])
    try:
        # the prisoner status changes to "problem" when the location is unknown -
        # mostly to alert the police officers that the prisoner isn`t connected
        db.change_prisoner_status(prisoner_id, new_status=1)
        return "GettingPrisonerLocationError"
    except:
        print("Inner error. please call the code manager")
        return "GettingPrisonerLocationErrorAndDataBaseError"


# in use in get_help_text function
def get_text_from_file(file_name):
    text = open(f"help_center\\" + file_name, "r").read()
    return json.dumps(text)


def get_help_text(content):
    help_type = content["input"]
    try:
        # returns the text of the file which requested
        if help_type == "for_users":
            return get_text_from_file("help_for_users.txt")
        elif help_type == "for_admins":
            return get_text_from_file("help_for_admins.txt")
        elif help_type == "for_developers":
            return get_text_from_file("help_for_developers.txt")
        elif help_type == "for_common":
            return get_text_from_file("common_f_and_q.txt")
        else:
            return json.dumps("CommandNotFound")
    except:
        return json.dumps("TextFileProblem")


# removing prisoner
def remove_prisoner(content, db):
    try:
        db.remove_prisoner(content["input"])
        return "Prisoner Removed Successfully"
    except:
        return "Prisoner Not Found"


# the ajax calls get checked by names
def commend_checker(content, db):
    # command type: when pressing the submit button - sending prisoner_data`s data to the UI
    if content["type"] == "get_prisoner_data_and_current_location_and_red_circles":
        return get_prisoner_data_and_current_location_and_red_circles(content, db)

    # command type: sending back all prisoners
    elif content["type"] == "get_all_prisoners_id_and_name_ect":
        return get_all_prisoners(db)

    # command type: get all new things that happened and all problems (status==1)
    elif content["type"] == "get_all_problems_and_new_alerts":
        return get_all_problems_and_new_alerts(db)

    # command type: adding and removing red circles (iframe command)
    elif content["type"] == "add_or_remove_red_circle":
        return add_or_remove_red_circle(content, db)

    # command type: inserting new prisoner to DB, from `/prisoner` tab
    elif content["type"] == "new_prisoner":
        return new_prisoner(content, db)

    # command type: reading new location and writing it to DB
    elif content["type"] == "prisoner_new_location":
        return prisoner_new_location(content, db)

    # error in getting the location from the client
    elif content["type"] == "prisoner_unknown_location":
        return prisoner_unknown_location(content, db)

    # help center texts and ect.
    elif content["type"] == "get_help_text":
        return get_help_text(content)

    # removing prisoner
    elif content["type"] == "remove_prisoner":
        return remove_prisoner(content, db)

    # command type: unknown
    else:
        return "CommendNotFoundError"


# the `background` page of the UI
@app.route('/ajax', methods=['POST'])
def user():
    # open database
    # TODO open the db only once
    db = DB.Database("test.db")
    # getting function type and data from JS
    get_content = request.data
    content = json.loads(get_content.decode())
    print(content)
    # checking what method need to be used
    return commend_checker(content, db)


# the favicon route
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


# help - mainly explanation on the functions in the site
@app.route('/help')
def help_page():
    return app.send_static_file("help_page.html")


# iframe #2 - the live alert log
@app.route('/log')
def alert_log():
    return app.send_static_file("alert_log_ui.html")


# iframe #1 - adding or removing red circles
@app.route('/circles')
def red_circles():
    return app.send_static_file("append_red_circles_ui.html")


# the `black-boxed`-closed prisoner`s page
@app.route('/prisoner')
def prisoner():
    return app.send_static_file("prisoner_client.html")


# the main page - map, data presenting and ect.
@app.route('/main')
def main_page():
    return app.send_static_file("map_and_console_ui.html")


# the main page - directing
@app.route('/')
def main_page_directing():
    return app.send_static_file("map_and_console_ui.html")


if __name__ == '__main__':
    app.run(host=LOCAL_HOST, debug=True)
