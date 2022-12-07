import yaml
import os
from . import validators
from . import helpers

try:
    import http.server as server
except ImportError:
    # Handle Python 2.x
    import SimpleHTTPServer as server

class HTTPRequestHandler(server.SimpleHTTPRequestHandler):
    """Extend SimpleHTTPRequestHandler to handle POST requests"""
    def do_POST(self):
        """Save a file following a HTTP POST request"""
        file_length = int(self.headers['Content-Length'])
        
        try:
            stock_data = yaml.full_load(self.rfile.read(file_length))
            probable_error = validators.validate_yaml_data(stock_data)
        except (yaml.parser.ParserError, yaml.scanner.ScannerError):
            probable_error = """Syntax error in yaml file
or invalid format used (e.g. not all elements are key: value pairs)
See pattern in samples folder in project root"""

        if probable_error is None:
            response = """File was accepted by intermediate server
Checking availability to buy stocks ...\n"""
            response_tuple = (201, 'Created')
            helpers.generate_yaml_file(
                helpers.beautify_stock_data(stock_data),
                "config.yaml",
            )
        else:
            response = probable_error + "\n"
            response_tuple = (400, 'Rejected')
        self.send_response(*response_tuple)
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))



server.test(HandlerClass=HTTPRequestHandler)
