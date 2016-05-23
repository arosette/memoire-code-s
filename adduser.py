import sqlite3
import sys
import params


if len(sys.argv) == 4:
    userid = sys.argv[1]
    pwd = sys.argv[2]
    phone_serial_number = sys.argv[3]
    
    db = sqlite3.connect(params.base_dir +
                         'db/authserver-app.sqlite')
    db.text_factory = str

    cursor = db.cursor()
    cursor.execute("""INSERT INTO users(userid,pwd,phone_serial_number
        ) VALUES(?, ?, ?)""", (userid, pwd, phone_serial_number))

    db.commit()
    db.close()
else:
    print("Usage : python adduser.py <userid> <pwd> "+
        "<phone-serial-number>")
