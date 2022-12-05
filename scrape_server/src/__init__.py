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
        filename = os.path.basename(self.path)

        # Don't overwrite files
        # if os.path.exists(filename):
        #     self.send_response(409, 'Conflict')
        #     self.end_headers()
        #     reply_body = '"%s" already exists\n' % filename
        #     self.wfile.write(reply_body.encode('utf-8'))
        #     return

        file_length = int(self.headers['Content-Length'])
        
        try:
            stock_data = yaml.full_load(self.rfile.read(file_length))
            print(stock_data)
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




# from crypt import methods
# from flask import Flask, request, Response, stream_with_context, after_this_request
# import os
# from flask_socketio import SocketIO, send
# from flask_sock import Sock
# app = Flask(__name__)

# def a():
#     print("abc")
#     import time
#     time.sleep(5)
#     print("ajd")

# # @app.route('/', methods=["POST"])
# # def test_ip():
# #     uploaded_file = request.files['file']
# #     print(uploaded_file.filename)
# #     print(uploaded_file)
    
# #     import yaml
# #     print(yaml.full_load(uploaded_file))
# #     @after_this_request
# #     def generate(abc):
# #         import time
# #         time.sleep(5)
# #         return "abc", 200
# #     # return "jdnfk" #Response(stream_with_context(generate()))
# #     # for string in uploaded_file:
# #     #     print(string)
# #     if uploaded_file.filename != '' and not os.path.exists(uploaded_file.filename):
# #         uploaded_file.save(uploaded_file.filename)
# #     # return Response()
# #     # send("anjffvj")
# #     return "Good", 200
# import asyncio

# @app.route('/', methods=['POST', 'GET'])
# def index():
#     # @app.teardown_request(request)
#     # def a(request):
#     #     return "dfmf"
#     async def add_header():
#         import time
#         time.sleep(5)
#         return "abc"

#     asyncio.run(add_header())
    
#     return "ksmk"

# app.run(host="0.0.0.0", port='5050')
