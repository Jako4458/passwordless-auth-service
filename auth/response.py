from flask import make_response, jsonify

def make_auth_valid(status_code=200):
    return make_response(jsonify({"status code": status_code, "status": "ok"}), status_code)

def make_verify_valid(data, status_code=200):
    return make_response(jsonify({"status code": status_code, "status": "ok", "data": data}), status_code)

def make_auth_error(status_code, err_msg):
    return make_response(jsonify({"status code": status_code, "error": err_msg}), status_code)

def make_verify(status_code, data=None, err_msg=""):
    # If successful
    if (status_code >= 200 and status_code < 400):
        return make_response(jsonify({"status code": status_code, "data":data}), status_code)

    return make_response(jsonify({"status code": status_code, "error": err_msg}), status_code)
