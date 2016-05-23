class ExpirationError(Exception):
    def __init__(self,object_name, current_time, expiration_time):
        self.object_name = object_name
        self.current_time = current_time
        self.expiration_time = expiration_time
    def __repr__(self):
        message = "Time is expired for "+self.object_name
        message += " (current_time="+repr(self.current_time)
        message += ", expiration_time="+repr(self.expiration_time)+")"
        return message
