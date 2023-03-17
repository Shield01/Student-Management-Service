from flask import request
from flask_restx import Namespace, Resource, fields
from bson import ObjectId
from pydantic import BaseModel
from typing import Optional, List
from .Course import course_display_view, Course
from Database import students_collection, courses_collection, black_list_collection
from jwt_handeler import hashPassword, check_password, verify_token, decode_token


class CourseView(BaseModel):
    name: str
    teacher: str
    score: int
    course_unit: int


class StudentModel(BaseModel):
    name: str
    email_address: str
    courses: List[CourseView]
    grades: List[int]
    GPA: Optional[float]
    password: str
    role: str


class StudentUpdateModel(BaseModel):
    name: Optional[str]
    email_address: Optional[str]


api = Namespace("students", description="Students related apis")

admin = api.model(
    "Student",
    {
        "name": fields.String(required=True, description="The student's name"),
        "email_address": fields.String(required=False, description="The student's email address"),
        "role": fields.String(),
        "password": fields.String(required=True)
    }
)

student = api.model(
    "Student",
    {
        "name": fields.String(required=True, description="The student's name"),
        "email_address": fields.String(required=False, description="The student's email address"),
        "password": fields.String(required=True)
    }
)

student_display_view = api.model(
    "Student_display_view",
    {
        "_id": fields.String(),
        "name": fields.String(required=True, description="The student's name"),
        "email_address": fields.String(required=False, description="The student's email address"),
        "courses": fields.String(description="Courses offered by the student"),
        "error": fields.String(),
        "response": fields.String()
    }
)


score = api.model(
    "Score",
    {
        "score": fields.Integer()
    }
)

Login_Payload = api.model(
    "Login Payload",
    {
        "email_address": fields.String(),
        "password": fields.String()
    }
)

Token = api.model(
    "Token",
    {
        "token": fields.String(),
        "error": fields.String()
    }
)

Logout_Response = api.model(
    "Logout Response",
    {
        "response": fields.String()
    }
)


@api.route("/")
class Students(Resource):
    @api.doc("list_of_students")
    @api.marshal_list_with(student_display_view, envelope="Students")
    def get(self):
        """List all students"""
        students = students_collection.find()
        list_students = list(students)
        return list_students

    @api.doc("admin_signup")
    @api.expect(admin)
    @api.marshal_with(student_display_view)
    def post(self):
        """Admin Signup"""

        data = request.get_json()
        name = data.get("name")
        email_address = data.get("email_address")
        password = data.get("password")
        role = data.get("role")

        student: Student = {}
        student["name"] = name
        student["email_address"] = email_address
        student["password"] = hashPassword(password)
        student["role"] = role

        task = students_collection.insert_one(dict(student))

        if task:
            return {"response": "Admin Sucessfully created"}, 201


@api.route("/create_students")
class CreateStudents(Resource):
    @api.doc("create_students")
    @api.header('token', 'Authorization token')
    @api.expect(student)
    @api.marshal_with(student_display_view)
    def post(self):
        """Create student account"""

        token = request.headers.get("token")
        if token:
            if verify_token(token):
                decoded_token = decode_token(token)
                if (decoded_token["users_role"] == "admin"):

                    data = request.get_json()
                    name = data.get("name")
                    email_address = data.get("email_address")
                    password = data.get("password")

                    student: Student = {}
                    student["name"] = name
                    student["email_address"] = email_address
                    student["password"] = hashPassword(password)
                    student["role"] = "student"

                    task = students_collection.insert_one(dict(student))

                    if task:
                        return {"response": "Student Sucessfully created"}, 201
                return {"response": "Student account can only be created by an admin"}
            return {"response": "Invalid token"}
        return {"response": "No token provided"}


@api.route("/<id>")
@api.param("id", "The student identifier")
@api.response(404, "Student not found")
class Student(Resource):
    @api.doc("Get a student")
    @api.marshal_with(student_display_view)
    @api.header('token', 'Authorization token')
    def get(self, id):
        """Get a student with it's id"""
        token = request.headers.get("token")
        if token:
            if verify_token(token):
                decoded_token = decode_token(token)
                if (decoded_token["users_role"] == "admin" or decoded_token["userId"] == id):
                    student = students_collection.find_one(
                        {"_id": ObjectId(id)})
                    if student:
                        return student
                    return {"error": "Student not found"}
                return {"error": "Record can only be accessed by either an admin, or the student"}
            return {"error": "Invalid token"}
        return {"error": "No token provided"}

    @api.doc("Update a student details")
    @api.expect(student)
    @api.marshal_with(student_display_view)
    @api.header('token', 'Authorization token')
    def put(self, id):
        """Update a student's details, given it's id"""
        token = request.headers.get("token")
        if token:
            if verify_token(token):
                decoded_token = decode_token(token)
                if (decoded_token["users_role"] == "admin" or decoded_token["userId"] == id):

                    student = students_collection.find_one(
                        {"_id": ObjectId(id)})

                    if student:

                        data = request.get_json()

                        new_name = data.get("name")

                        new_email = data.get("email_address")

                        update_details: StudentUpdateModel = {}
                        if new_name:
                            update_details["name"] = new_name
                        if new_email:
                            update_details["email_address"] = new_email

                        task = students_collection.find_one_and_update(
                            {"_id": ObjectId(id)}, {"$set": update_details})
                        if task:
                            return students_collection.find_one({"_id": ObjectId(id)})
                        return {"error": "Couldn't update the details"}
                    return {"error": "Could not find the student record"}
                return {"error": "Student record can only be updated by the student, or an admin"}
            return {"error": "Invalid Token"}
        return {"error": "No token provided"}

    @api.doc("Delete a student record")
    @api.response(204, "Student record deleted")
    @api.header('token', 'Authorization token')
    def delete(self, id):
        """Delete a student's record, given it's id"""
        token = request.headers.get("token")
        if token:
            if verify_token(token):
                decoded_token = decode_token(token)
                if (decoded_token["users_role"] == "admin"):
                    students_collection.find_one_and_delete(
                        {"_id": ObjectId(id)})
                    return "Deleted"
                return "Student record can only be deleted by an admin"
            return "Invalid Token"
        return {"response": "No token provided"}


@api.route("/register_course/<course_id>/<student_id>")
@api.param("student_id", "The student's id")
@api.param("course_id", "The course to be registered")
@api.response(404, "Course not found")
class RegisterCourse(Resource):
    @api.doc("Register a course")
    @api.marshal_with(course_display_view)
    @api.header('token', 'Authorization token')
    def put(self, student_id, course_id):
        """Register a course to a student"""
        token = request.headers.get("token")
        if token:
            if verify_token(token):
                decoded_token = decode_token(token)
                if decoded_token["userId"] == student_id:

                    course = Course.get(Course, course_id)
                    if course:
                        student = Student.get(Student, student_id)
                        if student:
                            course_to_add: CourseView = {}

                            course_to_add["_id"] = course["_id"]
                            course_to_add["name"] = course["name"]
                            course_to_add["teacher"] = course["teacher"]
                            course_to_add["score"] = 0
                            course_to_add["course_unit"] = course["course_unit"]

                            students_collection.update_one({"_id": ObjectId(student_id)}, {
                                "$addToSet": {"courses": course_to_add}})

                            student_for_course: Student = {}
                            student_for_course["_id"] = student["_id"]
                            student_for_course["name"] = student["name"]
                            student_for_course["email_address"] = student["email_address"]

                            courses_collection.update_one({"_id": ObjectId(course_id)}, {
                                "$addToSet": {"students": student_for_course}})
                            return course
                        return {"error": "Student Not found"}
                    return {"error": "Course not found"}
                return {"error": "Course can only be registered by the student"}
            return {"error": "Invalid token"}
        return {"error": "No token provided"}


@api.route("/record_grade/<course_id>/<student_id>")
@api.param("student_id", "The student's id")
@api.param("course_id", "The course's id")
class Grades(Resource):
    @api.doc("Record Grades")
    @api.expect(score)
    @api.marshal_with(student_display_view)
    @api.header('token', 'Authorization token')
    def post(self, student_id, course_id):
        """Record a score"""
        token = request.headers.get("token")
        if token:
            if verify_token(token):
                decoded_token = decode_token(token)
                if (decoded_token["users_role"] == "admin"):

                    data = request.get_json()

                    student = students_collection.find_one(
                        {"_id": ObjectId(student_id)})

                    if student:
                        if student["courses"]:
                            for x in student["courses"]:
                                if x["_id"] == course_id:
                                    x["score"] = data["score"]
                                    students_collection.find_one_and_update(
                                        {"_id": ObjectId(student_id)}, {"$set": student})

                        course = courses_collection.find_one(
                            {"_id": ObjectId(course_id)})

                        if course:
                            if course["students"]:
                                for x in course["students"]:
                                    if x["_id"] == student_id:
                                        x["score"] = data["score"]
                                courses_collection.find_one_and_update(
                                    {"_id": ObjectId(course_id)}, {"$set": course})

                        total_score = 0
                        total_unit = 0
                        for x in student["courses"]:
                            score_product = x["score"] * x["course_unit"]
                            total_unit = total_unit + x["course_unit"]
                            total_score = total_score + score_product

                        gpa = total_score / total_unit
                        student["GPA"] = gpa
                        students_collection.find_one_and_update(
                            {"_id": ObjectId(student_id)}, {"$set": student})

                        return {"response": "Successfully recorded score"}, 200
                    return "Student Not Found"
                return {"error": "Grade can only be recorded by a teacher"}
            return {"error": "Invalid token"}
        return {"error": "No token provided"}


@api.route("/login")
class Login(Resource):
    @api.doc("User Login")
    @api.expect(Login_Payload)
    @api.marshal_with(Token)
    def post(self):
        """Login"""
        data = request.get_json()
        token = check_password(data)
        if token:
            return_value = {"token": token}
            return return_value
        return {"error": "Login failed"}


@api.route("/logout")
class Logout(Resource):
    @api.doc("User Logout")
    @api.header('token', 'Authorization token')
    @api.marshal_with(Logout_Response)
    def post(self):
        """Logout"""
        token = request.headers.get("token")
        if token:
            task = black_list_collection.insert_one({"token": token})
            if task:
                return {"response": "Logged Out"}
        return {"response": "You don't have a token"}
