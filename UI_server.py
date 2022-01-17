# imports:
from flask import Flask, request
import json
import DB_Miller_Library as DB
import datetime
import Distance_Library as Distance

# flask argument
app = Flask(__name__)


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
        prisoner_personal_data = db.get_prisoner_personal_data(prisoner_id)[0]
        prisoner_location = db.get_prisoner_locations(prisoner_id)[-1]
        prisoner_red_circles = db.get_all_prisoner_red_circles(prisoner_id)
        data_to_return = [prisoner_id, prisoner_personal_data[1], prisoner_personal_data[2],
                          [prisoner_location[3], prisoner_location[4]], prisoner_location[2],
                          prisoner_personal_data[3], prisoner_red_circles]
        return json.dumps(data_to_return)
    except:
        return "SubmitPrisonerError"


def get_all_problems_and_new_alerts(db):
    try:
        all_new_log_data = []
        for prisoner_data in db.get_all_prisoners():
            if prisoner_data[3] == 1:
                all_new_log_data.append(list(prisoner_data))
            elif prisoner_data[3] == 0:
                listed_prisoner = list(prisoner_data)
                all_new_log_data.append(listed_prisoner)
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
        if add_remove_type == "ADD":
            db.add_red_circle(prisoner_id, radius, lat, lng, circle_type)
            return "AddedCircle"
        elif add_remove_type == "REMOVE":
            db.remove_red_circle(prisoner_id, lat, lng)
            return "RemovedCircle"
        else:
            return "NoSuchCommandError"
    except:
        return "ValueError"


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
        client_national_id = data[0]
        location_lat = data[1]
        location_lng = data[2]
        date = datetime.datetime.now()
        db.insert_new_location(client_national_id, date, location_lat, location_lng)
        all_red_circles = db.get_all_prisoner_red_circles(client_national_id)
        radius_placer = 2
        location_placer_lat = 3
        location_placer_lng = 4
        circle_type_placer = 5
        for red_circle in all_red_circles:
            if Distance.coordinate_dis((red_circle[location_placer_lat], red_circle[location_placer_lng]),
                                       (location_lat, location_lng)) <= red_circle[radius_placer]:
                # the prisoner_data is in the circle
                if red_circle[circle_type_placer] == "1":
                    # Not allowed
                    db.change_prisoner_status(client_national_id, 1)
                else:
                    # allowed
                    db.change_prisoner_status(client_national_id, 0)
            else:
                # the prisoner_data is out of the circle
                if red_circle[circle_type_placer] == "1":
                    # Not allowed
                    db.change_prisoner_status(client_national_id, 0)
                else:
                    # allowed
                    db.change_prisoner_status(client_national_id, 1)
        return "Good"
    except:
        return "LocationError"


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
    # TODO display the data of the red circles somewhere

    # command type: inserting new prisoner to DB, from `/prisoner` tab
    elif content["type"] == "new_prisoner":
        return new_prisoner(content, db)

    # command type: reading new location and writing it to DB
    elif content["type"] == "prisoner_new_location":
        return prisoner_new_location(content, db)

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
