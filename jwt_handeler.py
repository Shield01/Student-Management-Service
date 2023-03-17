from passlib.context import CryptContext
from dotenv import load_dotenv
from Database import students_collection, black_list_collection
from bson import ObjectId
from datetime import datetime, timedelta
import jwt
import os

load_dotenv(".env")

JWT_SECRET = os.environ.get("secret")
JWT_ALGORITHM = os.environ.get("algorithm")
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# This function hashes the password
def hashPassword(password):
    return password_context.hash(password)


# Check that the password is correct
def check_password(data):
    the_user = students_collection.find_one(
        {"email_address": data["email_address"]})
    if the_user:
        verify_password = password_context.verify(
            data["password"], the_user["password"])
        if verify_password:
            return sign_jwt(the_user["_id"])
    else:
        return False


# This function builds the payload to be signed, signs it and then returns it
def sign_jwt(user_id: str):
    user = students_collection.find_one({"_id": ObjectId(user_id)})
    payload = {
        "userId": str(user_id),
        "expires": (datetime.now() + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S.%f"),
        "users_role": user["role"]
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


# This function decodes the token and returns the token, if it is not expired
def decode_token(token):
    decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    if decoded_token:
        expiry_time = datetime.strptime(
            decoded_token['expires'], "%Y-%m-%d %H:%M:%S.%f")
        if expiry_time >= datetime.now():
            return decoded_token
        else:
            return False
    else:
        return False


# This function verifies that a token is valid, by confirming it's not on the blacklist and it is not expired
def verify_token(token: str):
    is_token_valid: bool = False
    check_blacklist = black_list_collection.find_one({"token": token})
    if check_blacklist:
        return is_token_valid
    else:
        payload = decode_token(token)
        if payload:
            is_token_valid = True
            return is_token_valid
        else:
            return is_token_valid
