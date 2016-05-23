import sqlite3
import os
import base64
import datetime
import params

def index(environ, start_response):
    
    # Connect to sqlite db
    db = sqlite3.connect(params.base_dir+'db/authserver-app.sqlite')
    
    # Generate challenge : random number of 512 bits (64 bytes)
    # + expiration date
    challenge = os.urandom(64)
    challenge_b64 = base64.standard_b64encode(challenge)
    current_time = datetime.datetime.now()
    available_time = datetime.timedelta(seconds=30)
    challenge_exp_date = current_time + available_time
    
    # Store challenge, challenge_exp_date,
    # qr_code_token and qr_code_token_exp_date in db
    cursor = db.cursor()
    cursor.execute("""INSERT INTO 
        challenges(challenge, challenge_exp_date) 
        VALUES(?, ?)""",
        (sqlite3.Binary(challenge), challenge_exp_date))
    db.commit()
    db.close()
    
    response_body = """
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
    <head>
        <title>Multifactor authentication</title>
        <meta http-equiv="Content-Type"
            content="text/html;charset=utf-8" />
        <script type="text/javascript" src="jssha/sha.js"></script>
        <script type="text/javascript">
            function calcHMAC() {
                try {
                        var hmacText =
                            document.getElementById("challenge").value;
                        var hmacTextType = "TEXT";
                        var hmacKeyInput =
                            document.getElementById("pwd").value;
                        var hmacKeyInputType = "TEXT";
                        var hmacVariant = "SHA-256";
                        var hmacOutputType = "B64";
                        var hmacOutput =
                            document.getElementById("pwd");
                        var hmacObj = new jsSHA(
                                hmacVariant,
                                hmacTextType
                        );
                        hmacObj.setHMACKey(
                                hmacKeyInput,
                                hmacKeyInputType
                        );
                        hmacObj.update(hmacText);

                        hmacOutput.value =
                            hmacObj.getHMAC(hmacOutputType);
                        return true;
                } catch(e) {
                        hmacOutput.value = e.message;
                        return false;
                }
            }
        </script>
    </head>
    <body>
        Enter user id and password.
        <p>
        <form action="/form" method="POST"
            onsubmit="return calcHMAC()">
            User ID:   <input type="text" name="userid" id="userid"/>
            <br />
            Password:   <input type="password" name="pwd" id="pwd"/>
            <br />
            <input type="hidden" name="challenge" id="challenge"
                value=\""""+challenge_b64+"""\"/>
            <input value="Login" type="submit"/>
        </form>
    </body>
</html>"""
    
    status = '200 OK'
    response_headers = [
        ('Content-Type', 'text/html'),
        ('Content-Length', str(len(response_body)))
    ]
    start_response(status, response_headers)
    return [response_body]
