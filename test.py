import sqlite3
import base64
import dberror
import datetime
import expirationerror
import os

qr_code_token_b64 = "pORsYgX0d8BZ0j_e7ahNnAMW7K-yqTNUxrpfc3LyzxbaNqJP3jLj8rs4QJotDUHVQKkYDeX9j6zIX6B292bvmA=="
qr_code_token = base64.b64decode(qr_code_token_b64, "-_")

# Connect to sqlite db
db = sqlite3.connect('/srv/www/htdocs/db/users.sqlite')
try:
    # Retrieve expiration date
    db.text_factory = str
    cursor = db.cursor()
    cursor.execute("""SELECT qr_code_token, qr_code_exp_date FROM users WHERE qr_code_token=?""", (sqlite3.Binary(qr_code_token),))
    responses = cursor.fetchall()
    print(responses)
    # There should be one entry for a given token
    if len(responses) != 1:
        raise dberror.DbError("Inexisting token or too many ones")
    
    response = responses[0]
    expiration_time_str = response[1]
    expiration_time = datetime.datetime.strptime(expiration_time_str, "%Y-%m-%d %H:%M:%S.%f")
    print(expiration_time)
    
    # Check if qr_code_token is not expired
    current_time = datetime.datetime.now()
    if current_time > expiration_time:
        raise expirationerror.ExpirationError("qr_code_token", current_time, expiration_time)
    
    # Send QR Code file
    
    # Set QR Code fields to null
    cursor = db.cursor()
    cursor.execute("""UPDATE users SET qr_code_token=?, qr_code_exp_date=? WHERE qr_code_token=?""", (None, None, sqlite3.Binary(qr_code_token)))
    db.commit()
    
    # Delete QR Code file
    os.remove("/srv/www/htdocs/qr-codes/qr-code-"+ qr_code_token_b64 +".png")
    print("ok")
except dberror.DbError as e:
    print(repr(e))
except expirationerror.ExpirationError as e:
    print(repr(e))
finally:
    current_time = datetime.datetime.now()
    cursor = db.cursor()
    cursor.execute("""SELECT DISTINCT qr_code_token FROM users WHERE qr_code_exp_date<?""", (current_time,))
    qr_code_token_to_remove = cursor.fetchall()
    for qr_code_token in qr_code_token_to_remove:
        qr_code_token_b64 = base64.b64encode(qr_code_token[0], "-_")
        print(qr_code_token_b64)
        os.remove("/srv/www/htdocs/qr-codes/qr-code-"+ qr_code_token_b64 +".png")
    cursor = db.cursor()
    cursor.execute("""UPDATE users SET qr_code_token=?, qr_code_exp_date=? WHERE qr_code_exp_date<?""", (None, None, current_time))
    db.commit()
    
    # Delete untracked QR Code files
    cursor = db.cursor()
    cursor.execute("""SELECT DISTINCT qr_code_token FROM users""", ())
    qr_code_tokens_to_keep = cursor.fetchall()
    qr_code_files_to_keep = []
    for qr_code_token_to_keep in qr_code_tokens_to_keep:
        if qr_code_token_to_keep[0] != None:
            qr_code_files_to_keep.append("qr-code-"+base64.b64encode(qr_code_token_to_keep[0], "-_")+".png")
    for qr_code_file in os.listdir("/srv/www/htdocs/qr-codes"):
        if qr_code_file not in qr_code_files_to_keep:
            os.remove("/srv/www/htdocs/qr-codes/"+qr_code_file)
    
    db.close()
