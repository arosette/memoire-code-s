import qrcode
import os
import sqlite3
import autherror
import datetime
import base64
import cgi
import hmac
import hashlib
import Cookie
import params


def login(environ, start_response):
    
    # Retrieve values of POST fields
    form = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
    userid = form["userid"].value
    hmac_b64 = form["pwd"].value
    challenge1_b64 = form["challenge"].value
    challenge1 = base64.standard_b64decode(challenge1_b64)
    
    # Connect to sqlite db
    db = sqlite3.connect(params.base_dir+'db/authserver-app.sqlite')
    db.text_factory = str
    
    try:
        
        # Retrieve challenge1 and challenge1 expiration time
        cursor = db.cursor()
        cursor.execute("""SELECT challenge, challenge_exp_date 
            FROM challenges WHERE challenge=?""",
            (sqlite3.Binary(challenge1),))
        response = cursor.fetchone()
        if response == None:
            raise autherror.AuthError("Wrong authentication !")
        expiration_time_str = response[1]
        expiration_time = datetime.datetime.strptime(
            expiration_time_str, "%Y-%m-%d %H:%M:%S.%f")
        
        # Delete used challenge1
        cursor = db.cursor()
        cursor.execute("""DELETE FROM challenges WHERE challenge=?""",
                       (sqlite3.Binary(challenge1),))
        db.commit()
        
        # Check if challenge1 is not expired
        current_time = datetime.datetime.now()
        if current_time > expiration_time:
            raise expirationerror.ExpirationError("challenge1",
                                                  current_time,
                                                  expiration_time)
        
        # Delete expired challenges1
        cursor = db.cursor()
        cursor.execute("""DELETE FROM challenges 
            WHERE challenge_exp_date<?""", (current_time,))
        db.commit()
        
        # Retrieve user from its userid
        cursor = db.cursor()
        cursor.execute("""SELECT userid, pwd 
            FROM users WHERE userid=?""", (userid,))
        response = cursor.fetchone()
        if response!=None:
            retrieved_userid, retrieved_pwd = response
            retrieved_hmac = hmac.new(
                retrieved_pwd,
                msg=challenge1_b64,
                digestmod=hashlib.sha256).digest()
            retrieved_hmac_b64 = base64.standard_b64encode(
                retrieved_hmac)
        else:
            retrieved_userid, retrieved_pwd = (None,None)
        # Raise exception if authentication is invalid
        if(response==None or hmac_b64!=retrieved_hmac_b64):
            raise autherror.AuthError("Wrong authentication !")
        
        
        # Generate challenge2 : random number of 512 bits (64 bytes)
        # + expiration date
        challenge2 = os.urandom(64)
        challenge2_b64 = base64.standard_b64encode(challenge2)
        current_time = datetime.datetime.now()
        available_time = datetime.timedelta(seconds=5)
        challenge_exp_date = current_time + available_time
        
        # Generate QR Code token : random number of 512 bits (64 bytes)
        # + expiration date
        qr_code_token = os.urandom(64)
        qr_code_token_b64 = base64.b64encode(qr_code_token, "-_")
        current_time = datetime.datetime.now()
        available_time = datetime.timedelta(seconds=5)
        qr_code_token_exp_date = current_time + available_time
        
        # Initialize QR code object
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4)
        
        # Store data in QR Code
        encoded_data = challenge2_b64
        qr.add_data(encoded_data)
        
        
        # Generate QR code
        qr.make(fit=True)
        
        # Convert QR Code to image
        img = qr.make_image()

        
        # Create file to store QR Code image
        filename = "qr-code"
        extension = "png"
        filename += '-' + qr_code_token_b64 + '.' + extension
        image_file = open(params.base_dir+"qr-codes/"+filename, 'w+')
        
        # Store QR Code in file
        img.save(image_file, extension.upper())
        image_file.close()
        
        # Generate tmp_session_key
        tmp_session_key = os.urandom(64)
        tmp_session_key_b64 = base64.standard_b64encode(
            tmp_session_key)
        current_time = datetime.datetime.now()
        available_time = datetime.timedelta(seconds=30)
        tmp_session_key_exp = current_time + available_time
        
        # Store challenge, challenge_exp_date, qr_code_token,
        # qr_code_token_exp_date, tmp_session_key
        # and tmp_session_key_exp in db
        cursor = db.cursor()
        cursor.execute("""UPDATE users 
            SET challenge=?, challenge_exp_date=?, qr_code_token=?, 
            qr_code_exp_date=?, tmp_session_key=?, 
            tmp_session_key_exp=? WHERE userid=?""",
            (sqlite3.Binary(challenge2), challenge_exp_date,
             sqlite3.Binary(qr_code_token), qr_code_token_exp_date,
             sqlite3.Binary(tmp_session_key),
             tmp_session_key_exp, userid))
        db.commit()
        
        # Create and send response
        response_body = '<html> <img alt="QR Code" src="https://'
        response_body += params.server_hostname
        response_body += '/imageloader?qr_code_token='
        response_body += qr_code_token_b64 +'" /></html>'
        
        # Create tmp_session_key cookie
        cookie = Cookie.SimpleCookie()
        cookie["tmp_session_key_b64"] = tmp_session_key_b64
        cookie["tmp_session_key_b64"]["path"] = "/ressource"
        cookie["tmp_session_key_b64"]["expires"] = tmp_session_key_exp.\
            strftime("%a, %d %b %Y %H:%M:%S")
        cookie["tmp_session_key_b64"]["secure"] = "secure"
        cookie["tmp_session_key_b64"]["domain"] = params.server_hostname
        
        # Send response with cookie
        status = '200 OK'
        response_headers = [
            ('Set-Cookie',
             cookie["tmp_session_key_b64"].OutputString()),
            ('Content-Type', 'text/html'),
            ('Content-Length', str(len(response_body)))
        ]
        print(response_headers)
        start_response(status, response_headers)
        return [response_body]
    
    # Handle invalid authentication
    except autherror.AuthError as e:
        print(repr(e))
        response_body = '<html>'+ repr(e) +'</html>'
        status = '200 OK'
        response_headers = [
            ('Content-Type', 'text/html'),
            ('Content-Length', str(len(response_body)))
        ]
        start_response(status, response_headers)
        return [response_body]
    # Close db
    finally:
        db.close()
