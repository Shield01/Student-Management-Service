from flask import request
from flask_restx import Namespace, Resource, fields
from pydantic import BaseModel
from bson import ObjectId
from typing import List
from Database import courses_collection
from jwt_handeler import decode_token, verify_token

api = Namespace("courses", description="Courses related apis")


class StudentView(BaseModel):
    name: str
    email_address: str
    score: int


class CourseModel(BaseModel):
    name: str
    teacher: str
    students: List[StudentView]
    course_unit: int


class CourseUpdateModel(BaseModel):
    name: str
    teacher: str


course = api.model(
    "Course",
    {
        "name": fields.String(required=True, description="The course's name"),
        "teacher": fields.String(required=True, description="The course's tutor"),
        "course_unit": fields.Integer()
    }
)

course_display_view = api.model(
    "Course_display_view",
    {
        "_id": fields.String(),
        "name": fields.String(required=True, description="The course's name"),
        "teacher": fields.String(required=True, description="The course's tutor"),
        "course_unit": fields.Integer(),
        "response": fields.String(),
        "error": fields.String()
    }
)

student_registered_to_course_view = api.model(
    "Student_registered_to_course_view",
    {
        "name": fields.String(required=True, description="The student's name"),
        "email_address": fields.String(required=False, description="The student's email address"),
        "response": fields.String(),
        "error": fields.String()
    }
)

grades_of_students_registered_to_course_view = api.model(
    "Grades_of_students_registered_to_course_view",
    {
        "score": fields.Integer(required=True),
        "response": fields.String(),
        "error": fields.String()
    }
)


@api.route("/")
class Courses(Resource):
    @api.doc("list all courses")
    @api.marshal_list_with(course_display_view, code=200)
    @api.header('token', 'Authorization token')
    def get(self):
        """Get all courses"""
        token = request.headers.get("token")
        if token:
            if verify_token(token):
                decoded_token = decode_token(token)
                if (decoded_token):
                    courses = courses_collection.find()
                    list_courses = list(courses)
                    print(type(list_courses))
                    return list_courses
                return {"error": "Token not decoded"}
            return {"error": "Invalid token"}
        return {"error": "No token provided"}

    @api.doc("Create a course")
    @api.expect(course)
    @api.header('token', 'Authorization token')
    @api.marshal_with(course_display_view, code=201)
    def post(self):
        """Create a new course"""
        token = request.headers.get("token")
        if token:
            if verify_token(token):
                decoded_token = decode_token(token)
                if (decoded_token["users_role"] == "admin"):
                    data = request.get_json()

                    name = data.get("name")
                    teacher = data.get("teacher")
                    course_unit = data.get("course_unit")

                    course: Course = {}

                    course["name"] = name
                    course["teacher"] = teacher
                    course["course_unit"] = course_unit

                    task = courses_collection.insert_one(dict(course))

                    if task:
                        return course, 201
                    return {"error": "Failed"}
                return {"error": "Courses can only be created by admins"}
            return {"error": "Invalid token"}
        return {"error": "No token provided"}


@api.route("/<id>")
@api.param("id", "The course identifier")
@api.response(404, "Course not found")
class Course(Resource):
    @api.doc("Get a course")
    @api.marshal_with(course_display_view)
    @api.header('token', 'Authorization token')
    def get(self, id):
        """Get a course with given it's id"""
        token = request.headers.get("token")
        if token:
            if verify_token(token):
                decoded_token = decode_token(token)
                if decoded_token:
                    course = courses_collection.find_one({"_id": ObjectId(id)})
                    if course:
                        return course
                    return {"error": "Not Found"}
                return {"error": "Token not decoded"}
            return {"error": "Invalid token"}
        return {"error": "No token provided"}


@api.route("/<id>/student_list")
@api.param("id", "The course identifier")
@api.response(404, "Course not found")
class Students_Registered_To_Course(Resource):
    @api.doc("Get the student's registered to a course, given it's id")
    @api.header('token', 'Authorization token')
    @api.marshal_list_with(student_registered_to_course_view)
    def get(self, id):
        """Get students registered to a course, given it's id"""
        token = request.headers.get("token")
        if token:
            if verify_token(token):
                decoded_token = decode_token(token)
                if decoded_token["users_role"] == "admin":
                    data = courses_collection.find_one({"_id": ObjectId(id)})
                    if data:
                        value = data["students"]
                        return value
                    return {"error": "Not found"}
                return {"error": "Students registered to a course can only be viewed by a teacher"}
            return {"error": "Invalid token"}
        return {"error": "No token provided"}


@api.route("/<course_id>/<student_id>/student_grades")
@api.param("course_id", "The course's identifier")
@api.param("student_id", "The student's identifier")
@api.response(404, "Course not found")
class Grades_Of_Student_Registered_To_Course(Resource):
    @api.doc("Get the grades of each student registered to a course, given the course's id and student's id")
    @api.header('token', 'Authorization token')
    @api.marshal_list_with(grades_of_students_registered_to_course_view)
    def get(self, course_id, student_id):
        """Get the grades of each student registered to a course, given the course's id and student's id"""
        token = request.headers.get("token")
        if token:
            if verify_token(token):
                decoded_token = decode_token(token)
                if (decoded_token["users_role"] == "admin" or decoded_token["userId"] == student_id):
                    course = courses_collection.find_one(
                        {"_id": ObjectId(course_id)})

                    if course:
                        data = course["students"]
                        for x in data:
                            if x["_id"] == student_id:
                                result = x["score"]
                                return_value = {"score": result}
                                return return_value
                            return {"error": "Student is not registered to course"}
                    return {"error": "Course not found"}
                return {"error": "Grade can only be viewed by teacher or the student"}
            return {"error": "Invalid token"}
        return {"error": "No token provided"}
