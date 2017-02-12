from serapis.models import *
from serapis.utils import grading
import numpy as np


def get_class_statistics(assignment):
    course_user_list = CourseUserList.objects.filter(course_id=assignment.course_id)

    # list of all students enrolled in this class
    student_list=[]
    for cu in course_user_list:
        if cu.role == CourseUserList.ROLE_STUDENT:
        	student_list.append(cu.user_id)

    last_submission_score_list=[]
    for student in student_list:
        latest_submission = grading.get_last_fully_graded_submission(student, assignment)
        if latest_submission != None:
            _,sum_student_score, _ = Submission.retrieve_task_grading_status_and_score_sum(latest_submission, False)
            last_submission_score_list.append(sum_student_score)


    enrollment = len(student_list)
    contributors = len(last_submission_score_list)

    if contributors > 0:
    	max_score = max(last_submission_score_list)
    	mean_score = np.mean(last_submission_score_list)
    	median = np.median(last_submission_score_list)
    else:
    	max_score = 0.0
    	mean_score = 0.0
    	median = 0.0

    return enrollment, contributors, max_score, mean_score, median