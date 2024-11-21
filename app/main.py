"""
Simple Flask application for generating random odd numbers.
"""

import random
import os
from flask import Flask, jsonify, make_response

app = Flask(__name__)
APP_READY = False

def initialize_app():
    """ Initialize the app and create log file."""
    file_path = os.path.join(os.path.dirname(__file__), 'odd-logs.txt')
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8'):
            pass
    return True


@app.route('/odd', methods=['GET'])
def get_random_odd():
    """ Generate odd number and write it to a log file."""
    odd_number = [n for n in range(1, 20) if n % 2 != 0]
    random_number = random.choice(odd_number)
    log_file_path = os.path.join(os.path.dirname(__file__), 'odd-logs.txt')
    with open(log_file_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"Odd number: {random_number}\n")
    return jsonify({"Odd number": random_number})


@app.route('/ready', methods=['GET'])
def readiness_check():
    """ Check if the app is ready to get requests."""
    if APP_READY:
        return make_response("Application is ready", 200)
    return make_response("Application is not ready", 503)


## Dont forget to remove debug=True after app is finished
if __name__ == '__main__':
    APP_READY = initialize_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
