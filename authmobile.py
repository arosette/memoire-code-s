import hmac
import hashlib
import base64
import sqlite3
import cgi
import os
import datetime
import params


def auth(environ, start_response):
    
    # Retrieve values of POST fields
    form = cgi.FieldStorage(fp=environ['wsgi.input'],
                            environ=environ)
    challenge_b64 = form['challenge'].value
    challenge = base64.standard_b64decode(challenge_b64)
    mac = form['mac'].value
    
    
    db = sqlite3.connect(params.base_dir+
                         'db/authserver-app.sqlite')
    db.text_factory = str
    cursor = db.cursor()
    cursor.execute("""SELECT userid, challenge, phone_serial_number 
        FROM users WHERE challenge=?""",
        (sqlite3.Binary(challenge),))
    response = cursor.fetchone()
    userid = response[0]
    serial_number = response[2]
    
    hmac_server = hmac.new(serial_number, msg=challenge,
                           digestmod=hashlib.sha256).digest()
    hmac_server_b64 = base64.standard_b64encode(hmac_server)
    
    hmac_server_b64 = hmac_server_b64.strip()
    mac = mac.strip()
    
    if hmac_server_b64 == mac:
        server_respone = "ok"
        
        # Generate session_key
        session_key = os.urandom(64)
        session_key_b64 = base64.standard_b64encode(session_key)
        current_time = datetime.datetime.now()
        available_time = datetime.timedelta(seconds=30)
        session_key_exp = current_time + available_time
        
        # Store session_key and session_key_exp in db
        cursor = db.cursor()
        cursor.execute("""UPDATE users 
            SET session_key=?, session_key_exp=? WHERE userid=?""",
            (sqlite3.Binary(session_key), session_key_exp, userid))
        db.commit()
    else:
        server_respone = "fail"
    response_body = "<html>"+ hmac_server_b64+ "<br />"
    response_body += mac.strip() + "<br />"+ server_respone +"</html>"
    
    status = '200 OK'
    response_headers = [
        ('Content-Type', 'text/html'),
        ('Content-Length', str(len(response_body)))
    ]
    start_response(status, response_headers)
    return [response_body]
