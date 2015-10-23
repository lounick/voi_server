#!/usr/bin/python
__author__ = 'nick'

#DB imports
import rethinkdb as r
from rethinkdb.errors import RqlDriverError, RqlRuntimeError
import queries

#ROS Imports
import rospy
import roslib
roslib.load_manifest("voi_Server")
from vehicle_interface.msg import AcousticModemStatus, AcousticModemPayload, AcousticModemAck

#Various imports
import calendar
import time
import struct

#The data exchange manager class and main method.

classes = ['target', 'vehicle', 'position3d']
uid_pack_format = "!HLH"

class dxm:

    conn = 0

    # ROS Parameters
    db_name = ""
    platform_id = 0 # Should be a parameter. Maybe the same as the modem address?

    # UID generation variables
    time = 0
    last_time = 0
    count = 1

    def init(self):
        # 1. Read the ros parameters
        self.db_name = rospy.get_param('db_name', "voi_ontology")
        self.platform_id = rospy.get_param('platform_id', 0)

        # 2. Make connection with the server
        try:
            self.conn = r.connect("localhost", 28015)
        except RqlDriverError:
            rospy.logerr("Couldn't establish connection with the server")
            return False

        # 3. List databases and create the ontology db if required.
        databases = r.db_list().run(self.conn)
        if not(self.db_name in databases):
            # Database not present, must create it
            try:
                r.db_create(self.db_name).run(self.conn)
            except RqlRuntimeError:
                rospy.logerr("Couldn't create the database")
                return False

        # 4. If database there drop old tables and create new versions (We need the db clean when starting the mission)
        tables = r.db(self.db_name).table_list().run(self.conn)
        for class_name in classes:
            if class_name in tables:
                try:
                    r.db(self.db_name).table_drop(class_name)
                except RqlRuntimeError:
                    rospy.logerr("Couldn't clear table from database")
                    return False
            try:
                r.db(self.db_name).table_create(class_name)
            except RqlRuntimeError:
                rospy.logerr("Couldn't create table in database")
                return False
        return True

    def generate_uid(self):
        # Method that generates a UID for storing an instance
        self.time = rospy.Time.now() #calendar.timegm(time.gmtime())

        if self.time.secs != self.last_time:
            self.last_time = self.time.secs
            self.count = 1
        else:
            self.count += 1

        if self.count > 65535:
            rospy.logwarn("Tried to create more than 65535 UIDs per second, pausing")
            return -1

        return struct.pack(uid_pack_format, self.platform_id, self.time.secs, self.count)

    def run(self):
        print("Running main loop")



def main():
    print("Hello DXM!!!")

if __name__ == "__main__":
    main()