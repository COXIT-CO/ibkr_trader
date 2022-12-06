import yaml
import os
from . import validators

try:
    import http.server as server
except ImportError:
    # Handle Python 2.x
    import SimpleHTTPServer as server

class HTTPRequestHandler(server.SimpleHTTPRequestHandler):
    """Extend SimpleHTTPRequestHandler to handle POST requests"""
    def do_POST(self):
        """Save a file following a HTTP PUT request"""
        filename = os.path.basename(self.path)

        # Don't overwrite files
        if os.path.exists(filename):
            self.send_response(409, 'Conflict')
            self.end_headers()
            reply_body = '"%s" already exists\n' % filename
            self.wfile.write(reply_body.encode('utf-8'))
            return

        file_length = int(self.headers['Content-Length'])
        
        try:
            data = yaml.full_load(self.rfile.read(file_length))
            probable_error = validators.validate_yaml_data(data)
        except (yaml.parser.ParserError, yaml.scanner.ScannerError):
            probable_error = "Syntax error in yaml file \
or invalid format used (e.g. not all elements are key: value pairs)\n\
See pattern in samples folder in project root"

        if probable_error is None:
            with open("config_buy.yaml", "w") as file:
                file.write(yaml.dump(data))
            response = 'File was accepted by intermediate server\nChecking availability to buy stocks ...\n'
            response_tuple = (201, 'Created')
        else:
            response = probable_error + "\n"
            response_tuple = (400, 'Rejected')
        self.send_response(*response_tuple)
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))



server.test(HandlerClass=HTTPRequestHandler)