import yaml
import time
from . import validators
from . import helpers

try:
    import http.server as server
except ImportError:
    # Handle Python 2.x
    import SimpleHTTPServer as server

balance_check_result = None

class HTTPRequestHandler(server.SimpleHTTPRequestHandler):
    """Extend SimpleHTTPRequestHandler to handle POST requests"""
    def do_POST(self):
        """Save a file following a HTTP POST request"""
        file_length = int(self.headers['Content-Length'])
        if self.path == "/balance_check":
            global balance_check_result
            balance_check_result = self.rfile.read(file_length).decode()
            response_tuple = response_tuple = (200, 'Ok')
            self.send_response(*response_tuple)
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            return
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
            self.send_response(*response_tuple)
            self.end_headers()
            helpers.generate_yaml_file(
                helpers.beautify_stock_data(stock_data),
                "config.yaml",
            )
            self.wfile.write(response.encode('utf-8'))
            for _ in range(30):
                if balance_check_result is not None:
                    self.wfile.write(balance_check_result.encode('utf-8'))
                    return
                time.sleep(1)
            second_response = """Now market is closed or some stocks aren't being sold,
so total order cost can't be estimated. Try some time later"""
            self.wfile.write(second_response.encode('utf-8'))
        else:
            response = probable_error + "\n"
            response_tuple = (400, 'Rejected')
            self.send_response(*response_tuple)
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))



server.test(HandlerClass=HTTPRequestHandler)
