from pymongo import MongoClient

from dotenv import load_dotenv

import os

load_dotenv(".env")

conn = MongoClient(os.environ.get("MongoDb_URI"))

students_collection = conn.altSchoolAfricaThirdSemesterExam.students
courses_collection = conn.altSchoolAfricaThirdSemesterExam.courses
black_list_collection = conn.altSchoolAfricaThirdSemesterExam.blacklist
test_collection = conn.altSchoolAfricaThirdSemesterExam.test
