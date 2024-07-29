from flask import make_response, jsonify

def create_error_message(error):
    error_message = {
        'error': error
    }
    return make_response(jsonify(error_message), 400)

def create_ok_message():
    ok_message = {
        'message': 'ok'
    }
    return make_response(jsonify(ok_message), 200)
