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
MINUTES_GAP_CHECK = 1


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
            prisoner_personal_data = db.get_prisoner_personal_data(prisoner_id)[0]
            prisoner_location = db.get_prisoner_locations(prisoner_id)[-1]
            prisoner_red_circles = db.get_all_prisoner_red_circles(prisoner_id)
            data_to_return = [prisoner_id, prisoner_personal_data[1], prisoner_personal_data[2],
                              [prisoner_location[3], prisoner_location[4]], prisoner_location[2],
                              prisoner_personal_data[3], prisoner_red_circles]
        except IndexError:
            return "No Location Measured Yet"
        return json.dumps(data_to_return)
    except:
        return "Submit Prisoner Error"


def get_all_problems_and_new_alerts(db):
    try:
        all_new_log_data = []
        # running through all prisoners
        for prisoner_data in db.get_all_prisoners():
            # now, we will check if the prisoner is in unwanted place

            prisoner_id = prisoner_data[0]
            # data place holders for time differences
            last_location = -1
            time_stamp_place = 2
            # data place holders for red circles
            radius_placer = 2
            location_placer_lat = 3
            location_placer_lng = 4
            circle_type_placer = 5
            # data place holders for prisoner`s location data
            prisoner_location_placer_lat = 3
            prisoner_location_placer_lng = 4

            # getting all the prisoner`s red circles
            all_red_circles = db.get_all_prisoner_red_circles(prisoner_id)
            prisoner_last_location = db.get_prisoner_personal_data(prisoner_id)

            # getting the prisoner`s last timestamp and current timestamp
            last_timestamp = db.get_prisoner_locations(prisoner_id)[last_location][time_stamp_place]
            current_time = str(datetime.now())
            time_format = '%Y-%m-%d %H:%M:%S.%f'
            prisoner_time_delta = datetime.strptime(current_time, time_format) - datetime.strptime(last_timestamp, time_format)

            # the problem checker - if bigger than 0 - problem
            is_problem = 0

            # running through all the red circles
            for red_circle in all_red_circles:
                if Distance.coordinate_dis((red_circle[location_placer_lat], red_circle[location_placer_lng]),
                                           (prisoner_last_location[prisoner_location_placer_lat], prisoner_last_location[prisoner_location_placer_lng])) <= red_circle[radius_placer]:
                    # the prisoner is in the circle
                    if red_circle[circle_type_placer] == "1":
                        # Not allowed in the circle - Problem
                        is_problem += 1
                    else:
                        # allowed only in the circle - Good
                        is_problem += 0
                else:
                    # the prisoner is out of the circle
                    if red_circle[circle_type_placer] == "1":
                        # Not allowed in the circle - Good
                        is_problem += 0
                    else:
                        # allowed only in the circle - Problem
                        is_problem += 1

            # checking if the client didn't sent location for a while
            if prisoner_time_delta > timedelta(minutes=MINUTES_GAP_CHECK):
                is_problem += 1
            else:
                is_problem += 0

            # finally - checking the problem checker
            if is_problem >= 1:
                db.change_prisoner_status(prisoner_id, new_status=1)
            else:
                db.change_prisoner_status(prisoner_id, new_status=0)

            # adding the current prisoner to the list
            all_new_log_data.append(list(prisoner_data))

        return json.dumps(all_new_log_data)
    except:
        return "LogError"


def add_or_remove_red_circle(content, db):
    try:
        data = json.loads(content["input"])
        prisoner_id = data[0]
        lat = data[1]
        lng = data[2]
        add_remove_type = data[3]
        radius = data[4]
        circle_type = data[5]
        # function - adding
        if add_remove_type == "ADD":
            # checking radius
            if int(radius) > 0:
                db.add_red_circle(prisoner_id, radius, lat, lng, circle_type)
                return "Added Circle"
            else:
                return "Radius Can`t be 0 or negative! (Error)"
        # function - removing
        elif add_remove_type == "REMOVE":
            try:
                db.remove_red_circle(prisoner_id, lat, lng)
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
        prisoner_national_id = data[0]
        prisoner_name = data[1]
        db.insert_new_prisoner(prisoner_id=prisoner_national_id, name=prisoner_name,
                               national_identifier=prisoner_national_id, status=False)
        return "Good"
    except:
        return "ValueError"


def prisoner_new_location(content, db):
    try:
        data = json.loads(content["input"])
        # loading the data that received
        client_national_id = data[0]
        location_lat = data[1]
        location_lng = data[2]
        # creating timestamp
        date = datetime.now()
        # inserting the new location into the database
        db.insert_new_location(client_national_id, date, location_lat, location_lng)
        return "Good"
    except:
        return "LocationError"


def prisoner_unknown_location(content, db):
    prisoner_id = json.loads(content["input"])
    try:
        db.change_prisoner_status(prisoner_id, new_status=1)
        return "GettingPrisonerLocationError"
    except:
        print("Inner error. please call the code manager")
        return "GettingPrisonerLocationErrorAndDataBaseError"


# in use in get_help_text
def get_text_from_file(file_name):
    text = open(f"help_center\\" + file_name, "r").read()
    return json.dumps(text)


def get_help_text(content):
    help_type = content["input"]
    try:
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
        try:
            return json.dumps(db.get_all_prisoners())
        except:
            return "LoadingAllPrisonersForListError"

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
    app.run(host='0.0.0.0', debug=True)
