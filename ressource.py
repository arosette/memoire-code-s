import autherror
import Cookie
import base64
import datetime
import expirationerror
import Cookie
import params
import sqlite3
    

def ressource(environ, start_response):
    # Store whether session_key or tmp_session_key have to be null
    modify_session_key = None
    modify_tmp_session_key = None
    
    try:
        response_body = "<html>fail</html>"
        status = '200 OK'
        response_headers = [
            ('Content-Type', 'text/html'),
            ('Content-Length', str(len(response_body)))
        ]
        
        
        if "HTTP_COOKIE" not in environ:
            raise autherror.AuthError("Wrong authentication !")
        cookie = Cookie.SimpleCookie(environ["HTTP_COOKIE"])

        # Retrieve protected info
        if "session_key_b64" in cookie and\
            cookie["session_key_b64"].value!="null":
            print("SESSION")
            # Retrieve session_key
            session_key_b64 = cookie["session_key_b64"].value
            session_key = base64.standard_b64decode(session_key_b64)
            
            # Retrieve session_key from db
            db = sqlite3.connect(params.base_dir+\
                'db/authserver-app.sqlite')
            db.text_factory = str
            cursor = db.cursor()
            cursor.execute("""
                SELECT userid, session_key, session_key_exp 
                FROM users WHERE session_key=?""",
                (sqlite3.Binary(session_key),))
            response = cursor.fetchone()
            
            # session_key does not exist in db
            if response == None:
                modify_session_key = "null"
                raise autherror.AuthError("Wrong authentication !")
            userid = response[0]
            session_key_exp = response[2]
            if session_key_exp != None:
                session_key_exp = datetime.datetime.strptime(
                    session_key_exp, "%Y-%m-%d %H:%M:%S.%f")
            current_time = datetime.datetime.now()
            
            # session_key has expired
            if session_key_exp < current_time:
                modify_session_key = "null"
                raise expirationerror.ExpirationError(
                    "session_key_exp", current_time, session_key_exp)
            
            # Access protected data
            response_body = "<html>Protected Data.</html>"
            response_headers = [
                ('Content-Type', 'text/html'),
                ('Content-Length', str(len(response_body)))
            ]
        
        # Generate session_key
        elif "tmp_session_key_b64" in cookie and\
            cookie["tmp_session_key_b64"].value!="null":
            print("TMP_SESSION")
            # Retrieve tmp_session_key
            tmp_session_key_b64 = cookie["tmp_session_key_b64"].value
            tmp_session_key = base64.standard_b64decode(
                tmp_session_key_b64)
            
            # Retrieve tmp_session_key from db
            db = sqlite3.connect(
                params.base_dir+'db/authserver-app.sqlite')
            db.text_factory = str
            cursor = db.cursor()
            cursor.execute("""
                SELECT userid, tmp_session_key, tmp_session_key_exp, 
                session_key, session_key_exp FROM users 
                WHERE tmp_session_key=?""",
                (sqlite3.Binary(tmp_session_key),))
            response = cursor.fetchone()
            
            # tmp_session_key does not exist in db
            if response == None:
                modify_tmp_session_key = "null"
                raise autherror.AuthError("Wrong authentication !")
            
            userid = response[0]
            tmp_session_key_exp = response[2]
            if tmp_session_key_exp != None:
                tmp_session_key_exp = datetime.datetime.strptime(
                    tmp_session_key_exp, "%Y-%m-%d %H:%M:%S.%f")
            session_key = response[3]
            if session_key != None:
                session_key_b64 = base64.\
                    standard_b64encode(session_key)
            session_key_exp = response[4]
            if session_key_exp != None:
                session_key_exp = datetime.datetime.strptime(
                    session_key_exp, "%Y-%m-%d %H:%M:%S.%f")
            current_time = datetime.datetime.now()
            
            # tmp_session_key has expired
            if tmp_session_key_exp < current_time:
                modify_tmp_session_key = "null"
                raise expirationerror.ExpirationError(
                    "tmp_session_key_exp", current_time,
                    tmp_session_key_exp)
            
            
            # Set session_key cookie
            if session_key_exp != None and\
                session_key_exp >= current_time:
                response_body = "<html>ok</html>"
                response_headers = [
                    ('Content-Type', 'text/html'),
                    ('Content-Length', str(len(response_body)))
                ]
                
                # Create session_key cookie
                cookie["session_key_b64"] = session_key_b64
                cookie["session_key_b64"]["path"] = "/ressource"
                cookie["session_key_b64"]["expires"] = \
                    session_key_exp.strftime("%a, %d %b %Y %H:%M:%S")
                cookie["session_key_b64"]["secure"] = "secure"
                cookie["session_key_b64"]["domain"] = \
                    params.server_hostname
                
                # Set tmp_session_key to null
                cookie["tmp_session_key_b64"] = "null"
                cookie["tmp_session_key_b64"]["path"] = "/ressource"
                cookie["tmp_session_key_b64"]["expires"] = \
                    datetime.datetime.now().strftime(
                        "%a, %d %b %Y %H:%M:%S")
                cookie["tmp_session_key_b64"]["secure"] = "secure"
                cookie["tmp_session_key_b64"]["domain"] = \
                    params.server_hostname
                
                response_headers = [("Set-Cookie",
                                     cookie["tmp_session_key_b64"].\
                                         OutputString()),
                ("Set-Cookie", cookie["session_key_b64"].OutputString())]\
                    + response_headers
                
                # Set tmp_session_key and tmp_session_key_exp to null
                cursor = db.cursor()
                cursor.execute("""UPDATE users SET tmp_session_key=?, 
                    tmp_session_key_exp=? WHERE userid=?""",
                    (None, None, userid))
                db.commit()
            
            
        else:
            raise autherror.AuthError("Wrong authentication !")
        start_response(status, response_headers)
        return [response_body]
    
    # Handle invalid authentication and expiration error
    except (autherror.AuthError, expirationerror.ExpirationError) as e:
        print(repr(e))
        response_body = '<html>'+ repr(e) +'</html>'
        status = '200 OK'
        response_headers = []
        if "HTTP_COOKIE" in environ:
            cookie = Cookie.SimpleCookie(environ["HTTP_COOKIE"])
            if modify_session_key != None:
                cookie["session_key_b64"] = modify_session_key
                cookie["session_key_b64"]["path"] = "/ressource"
                cookie["session_key_b64"]["expires"] = \
                    datetime.datetime.now().strftime(
                        "%a, %d %b %Y %H:%M:%S")
                cookie["session_key_b64"]["secure"] = "secure"
                cookie["session_key_b64"]["domain"] = \
                    params.server_hostname
                response_headers.append(
                    ('Set-Cookie',
                     cookie["session_key_b64"].OutputString()))
            if modify_tmp_session_key != None:
                cookie["tmp_session_key_b64"] = \
                    modify_tmp_session_key
                cookie["tmp_session_key_b64"]["path"] = "/ressource"
                cookie["tmp_session_key_b64"]["expires"] = \
                    datetime.datetime.now().strftime(
                        "%a, %d %b %Y %H:%M:%S")
                cookie["tmp_session_key_b64"]["secure"] = "secure"
                cookie["tmp_session_key_b64"]["domain"] = \
                    params.server_hostname
                response_headers.append(
                    ('Set-Cookie',
                     cookie["tmp_session_key_b64"].OutputString()))
        response_headers.append(('Content-Type', 'text/html'))
        response_headers.append(
            ('Content-Length', str(len(response_body))))
        start_response(status, response_headers)
        return [response_body]
