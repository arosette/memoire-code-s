import form
import imageloader
import authmobile
import index
import ressource


def application(environ, start_response):
    script_name = environ["PATH_INFO"]
    
    if script_name == "/" or script_name == "/index.html":
        return index.index(environ, start_response)
    elif script_name == "/form":
        return form.login(environ, start_response)
    elif script_name == "/imageloader":
        return imageloader.loadImage(environ, start_response)
    elif script_name == "/authmobile":
        return authmobile.auth(environ, start_response)
    elif script_name == "/ressource":
        return ressource.ressource(environ, start_response)
    
