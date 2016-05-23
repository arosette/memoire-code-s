class AuthError(Exception):
    def __init__(self,msg):
        self.msg = msg
    def __repr__(self):
        return repr(self.msg)