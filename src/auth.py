from flask import Blueprint, request
from flask import json
from flask.json import jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import validators
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flasgger import swag_from

from src.models import User, Bookmark, db
from src.constants.http_status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT


auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth.post("/register")
@swag_from("./docs/auth/register.yaml")
def register():
    username = request.json["username"]
    email = request.json["email"]
    password = request.json["password"]

    if len(password) < 6 :
        return jsonify({"error": "password is too short"}), HTTP_400_BAD_REQUEST

    else:
        pwd_hash = generate_password_hash(password)

    if len(username) < 3:
        return jsonify({"error": 
                        "the username is too short, it must be at least 6 characters"}), HTTP_400_BAD_REQUEST
    
    elif not username.isalnum() or " " in username:
        return jsonify({"error":
                        "the username must not contain spaces and must be alphanumeric"}), HTTP_400_BAD_REQUEST

    elif User.query.filter_by(username=username).first() is not None:
        return jsonify({"error": "username already taken"}), HTTP_409_CONFLICT


    if not validators.email(email):
        return jsonify({"error": "the email provided is not valid"}), HTTP_400_BAD_REQUEST

    elif User.query.filter_by(email=email).first() is not None:
        return jsonify ({"error": "email is already taken"}), HTTP_409_CONFLICT
 
    user = User(username=username, password=pwd_hash, email=email)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "user created",
        "user": {
            "username": username,
            "email": email
            }
        }), HTTP_201_CREATED


@auth.post("/login")
@swag_from("./docs/auth/login.yaml")
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    user = User.query.filter_by(email=email).first()

    if user:
        is_pass_correct = check_password_hash(user.password, password)

        if is_pass_correct:
            refresh_token = create_refresh_token(identity=user.id)
            access_token = create_access_token(identity=user.id)

            return jsonify({

                "user": {
                    "access": access_token,
                    "refresh": refresh_token,
                    "username": user.username,
                    "email": user.email
                }
            })

    return jsonify({"error": "wrong credentials"}), HTTP_401_UNAUTHORIZED


@auth.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()

    user = User.query.filter_by(id=user_id).first()

    return jsonify({

        "username": user.username,
        "email": user.email

    }), HTTP_200_OK


@auth.post("/token/refresh")
@jwt_required(refresh=True)
def refresh_users_token():
    user_identity = get_jwt_identity()
    accesss_token = create_access_token(identity=user_identity)

    return jsonify({

        "refresh": accesss_token
        
    }), HTTP_200_OK
