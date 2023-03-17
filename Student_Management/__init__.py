from flask_restx import Api

from .Student import api as student_api

from .Course import api as course_api

api = Api(
    title="Student Management Service",
    version="1.0",
    description="AltSchool Africa Third Semester Exam"
)

api.add_namespace(student_api)
api.add_namespace(course_api)
