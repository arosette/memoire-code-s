import sqlite3
import base64
import dberror
import datetime
import expirationerror
import os
import params

def urlArgToTuple(url_arg):
    url_arg = url_arg.split('=', 1)
    return (url_arg[0], url_arg[1])

def createDictFromUrlArgs(url_args):
    url_args = url_args.split('&')
    url_args = map(urlArgToTuple, url_args)
    return dict(url_args)

def loadImage(environ, start_response):
    
    # Retrieve GET args
    args = environ["QUERY_STRING"]
    
    # Retrieve QR Code token
    qr_code_token_b64 = createDictFromUrlArgs(args)["qr_code_token"]
    qr_code_token = base64.b64decode(qr_code_token_b64, "-_")
    
    # Connect to sqlite db
    db = sqlite3.connect(params.base_dir+'db/authserver-app.sqlite')
    try:
        # Retrieve expiration date
        db.text_factory = str
        cursor = db.cursor()
        cursor.execute("""SELECT qr_code_token, qr_code_exp_date 
            FROM users WHERE qr_code_token=?""",
            (sqlite3.Binary(qr_code_token),))
        responses = cursor.fetchall()

        # There should be one entry for a given token
        if len(responses) != 1:
            raise dberror.DbError("Inexisting token or too many ones")
        
        response = responses[0]
        expiration_time_str = response[1]
        expiration_time = datetime.datetime.strptime(
            expiration_time_str, "%Y-%m-%d %H:%M:%S.%f")
        
        # Check if qr_code_token is not expired
        current_time = datetime.datetime.now()
        if current_time > expiration_time:
            raise expirationerror.ExpirationError(
                "qr_code_token",current_time, expiration_time)
        
        # Load QR Code file in memory
        qr_code_file = open(params.\
            base_dir+"qr-codes/qr-code-"+ qr_code_token_b64 +".png",'rb')
        qr_code_content = qr_code_file.read()
        qr_code_file.close()
        
        # Set QR Code fields to null
        cursor = db.cursor()
        cursor.execute("""UPDATE users 
            SET qr_code_token=?, qr_code_exp_date=? 
            WHERE qr_code_token=?""",
            (None, None, sqlite3.Binary(qr_code_token)))
        db.commit()
        
        # Delete QR Code file
        os.remove(params.\
            base_dir+"qr-codes/qr-code-"+ qr_code_token_b64 +".png")
        
        # Send image
        response_body = qr_code_content
        status = '200 OK'
        response_headers = [
            ('Content-Type', 'image/png'),
            ('Content-Length', str(len(response_body)))
        ]
        start_response(status, response_headers)
        return [response_body]
        
    except dberror.DbError as e:
        print(repr(e))
    except expirationerror.ExpirationError as e:
        print(repr(e))
    finally:
        current_time = datetime.datetime.now()
        
        # Delete QR Code files of expired QR Code
        cursor = db.cursor()
        cursor.execute("""SELECT DISTINCT qr_code_token 
            FROM users WHERE qr_code_exp_date<?""", (current_time,))
        qr_code_tokens_to_remove = cursor.fetchall()
        for qr_code_token_to_remove in qr_code_tokens_to_remove:
            qr_code_token_b64_to_remove = base64.\
                b64encode(qr_code_token_to_remove[0], "-_")
            os.remove(params.base_dir+"qr-codes/qr-code-"+\
                qr_code_token_b64_to_remove +".png")
        
        # Set QR Code fields to null of expired QR Code tokens
        cursor = db.cursor()
        cursor.execute("""UPDATE users SET qr_code_token=?, 
            qr_code_exp_date=? WHERE qr_code_exp_date<?""",
            (None, None, current_time))
        db.commit()
        
        # Delete untracked QR Code files
        cursor = db.cursor()
        cursor.execute("""SELECT DISTINCT qr_code_token 
            FROM users""", ())
        qr_code_tokens_to_keep = cursor.fetchall()
        qr_code_files_to_keep = []
        for qr_code_token_to_keep in qr_code_tokens_to_keep:
            if qr_code_token_to_keep[0] != None:
                qr_code_files_to_keep.append(
                    "qr-code-"+base64.b64encode(
                        qr_code_token_to_keep[0], "-_")+".png")
        for qr_code_file in os.listdir(params.base_dir+"qr-codes"):
            if qr_code_file not in qr_code_files_to_keep:
                os.remove(params.base_dir+"qr-codes/"+qr_code_file)
        
        db.close()
