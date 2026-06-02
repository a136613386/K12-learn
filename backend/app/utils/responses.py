from flask import jsonify


def success_response(data=None, message: str = "success", code: int = 0):
    return jsonify({"code": code, "message": message, "data": data})


def error_response(message: str, status_code: int = 400, data=None):
    response = jsonify({"code": status_code, "message": message, "data": data})
    response.status_code = status_code
    return response
