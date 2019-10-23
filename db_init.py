import time
import dalek_db as db

time_now = round(time.time())
person1 = {"_id":"person1","mac":"xx:xx:xx:xx:xx:xx", "device_detected":time_now, "last_seen":time_now, "in_house":False}
person2 = {"_id":"person1","mac":"xx:xx:xx:xx:xx:xx", "device_detected":time_now, "last_seen":time_now, "in_house":False}
person3 = {"_id":"person1","mac":"xx:xx:xx:xx:xx:xx", "device_detected":time_now, "last_seen":time_now, "in_house":False}

my_connection = db.get_connection()
my_db = db.db_read(my_connection, "dalek")
db.create_doc(my_db, person1)
db.create_doc(my_db, person2)
db.create_doc(my_db, person3)
