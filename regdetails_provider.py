#!/usr/bin/env python

#-----------------------------------------------------------------------
# reg_provider.py
# Author: Rohan Amin, Shameek Hargrave
# Purpose: Given a classid, will connect to reg.sqlite database and
# submit class_detailss query, returning all class information in a
# formatted string. More specifically, a tuple with a boolean result
# and the provided return value, be it a Database error or valid class
# details data.
#-----------------------------------------------------------------------

import contextlib
import sqlite3
import textwrap

#----------------------------------------------------------------------#

# { "course_id": "", "days": "", "start": "",
# "end": "", "building": "", "room": "",
# "dept_num_combo": "", "area": "", "title": "",
# "description": "", "prereqs": "","prof_names": ""}
def human_readable(all_data):
    # defensive copies of fields
    course_id = all_data["course_id"]
    days = all_data["days"]
    start = all_data["start"]
    end = all_data["end"]
    building = all_data["building"]
    room = all_data["room"]
    dept_num_combo = all_data["dept_num_combo"]
    area = all_data["area"]
    prereqs = all_data["prereqs"]
    prof_names = all_data["prof_names"]
    # wrap title/description
    title = "Title: " + all_data["title"]
    description = "Description: " + all_data["description"]
    # edge case
    if prereqs == "":
        prereqs = "Prerequisites:"
    else:
        prereqs = "Prerequisites: " + prereqs

    # wrap long text
    title = textwrap.fill(text=title,
        initial_indent='', subsequent_indent="", width=72)
    description = textwrap.fill(text=description,
        initial_indent='', subsequent_indent="", width=72)
    prereqs = textwrap.fill(text=prereqs,
        initial_indent='', subsequent_indent="", width=72)
    # text blocks
    text = "Course Id: " + course_id + "\n\n"
    text += "Days: " + days + "\nStart time: " + start
    text += "\nEnd time: " + end + "\nBuilding: " + building
    text += "\nRoom: " + room + "\n\n"
    text += dept_num_combo + "\nArea: " + area + "\n\n" + title
    text += "\n\n" + description + "\n\n" + prereqs + "\n"
    # edge case
    if prof_names != "":
        text += prof_names
    return text

#----------------------------------------------------------------------#

# returns class info query
def build_classid_query():
    stmt = "SELECT classes.courseid, classes.days, "
    stmt += "classes.starttime, classes.endtime, "
    stmt += "classes.bldg, classes.roomnum, "
    stmt += "crosslistings.dept, crosslistings.coursenum, "
    stmt += "courses.title, courses.descrip, "
    stmt += "courses.prereqs, courses.area, "
    stmt += "courses.courseid, classes.classid, "
    stmt += "crosslistings.courseid "
    stmt += "FROM crosslistings, courses, classes "
    stmt += "WHERE classes.classid = ? "
    stmt += "AND classes.courseid = courses.courseid "
    stmt += "AND crosslistings.courseid = classes.courseid "
    stmt += "ORDER BY crosslistings.dept ASC,"
    stmt += "crosslistings.coursenum ASC;"
    return stmt

#----------------------------------------------------------------------#
DATABASE_URL = 'file:reg.sqlite?mode=ro'

def core(class_id):
    all_data = {
        "course_id": "",
        "days": "",
        "start": "",
        "end": "",
        "building": "",
        "room": "",
        "dept_num_combo": "",
        "area": "",
        "title": "",
        "description": "",
        "prereqs": "",
        "prof_names": "",
    }

    try:
        with sqlite3.connect(DATABASE_URL, isolation_level=None,
        uri=True) as connection:
            with contextlib.closing(connection.cursor()) as cursor:
                stmt = build_classid_query()
                cursor.execute(stmt, [class_id])
                class_info = cursor.fetchall()
                # error handling (no classid in DB)
                if len(class_info) == 0:
                    error_str = "no class with classid "
                    error_str += class_id + " exists"
                    return (False, error_str)

                # parse information
                all_data["course_id"] = str(class_info[0][0])
                all_data["days"] = str(class_info[0][1])
                all_data["start"] = str(class_info[0][2])
                all_data["end"] = str(class_info[0][3])
                all_data["building"] = str(class_info[0][4])
                all_data["room"] = str(class_info[0][5])
                all_data["title"] = str(class_info[0][8])
                all_data["description"] = str(class_info[0][9])
                all_data["prereqs"] = str(class_info[0][10])
                all_data["area"] = str(class_info[0][11])

                # format multiple dept/course num: loop through
                # each result and find the dept/course num
                for course in enumerate(class_info):
                    combo = str(course[1][6]) + " " + str(course[1][7])
                    if combo not in all_data["dept_num_combo"]:
                        all_data["dept_num_combo"] += "Dept and "
                        all_data["dept_num_combo"] += "Number: "
                        all_data["dept_num_combo"] += combo + "\n"

                # find professor(s)
                stmt = "SELECT profs.profname "
                stmt += "FROM profs, coursesprofs "
                stmt += "WHERE coursesprofs.courseid = ? "
                stmt += "AND profs.profid = coursesprofs.profid "
                stmt += "ORDER BY profs.profname ASC;"

                cursor.execute(stmt, [all_data["course_id"]])
                professors_list = cursor.fetchall()
                # corner case: no professors reverts to default ""

                # format multiple profs by looping through each
                # result
                for professors in enumerate(professors_list):
                    prof = str(professors[1][0])
                    if prof not in all_data["prof_names"]:
                        all_data["prof_names"] += "\nProfessor: "
                        all_data["prof_names"] += prof
                return (True, human_readable(all_data))

    except Exception as ex:
        server_error_msg = "A server error occurred."
        server_error_msg+= " Please contact the system administrator."
        if isinstance(ex,sqlite3.OperationalError):
            return (False, server_error_msg)
        if isinstance(ex,sqlite3.DatabaseError):
            return (False, server_error_msg)
        return (False, str(ex))

#----------------------------------------------------------------------#

def main():
    core("")

#----------------------------------------------------------------------#

if __name__ == "__main__":
    main()

#----------------------------------------------------------------------#