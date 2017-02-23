from serapis.models import *
from serapis.utils import grading
import numpy as np


def get_class_statistics(assignment, include_hidden):
    """
    Return:
      (num_enrolled_students, num_contributors, score_statistics)
      - num_enrolled_students: number of students enrolled in the class of this assignment
      - num_contributors: number of students who have tried this assignment so far
      - score_statistics: class statistics such as max, mean, 25th/75th-percentiles
    """

    # list of all students enrolled in this class
    student_list = [cu.user_id for cu in CourseUserList.objects.filter(
        course_id=assignment.course_id, role=CourseUserList.ROLE_STUDENT)]

    last_submission_score_list = []
    for student in student_list:
        latest_submission = grading.get_last_fully_graded_submission(student, assignment)
        if latest_submission:
            _, sum_student_score, _ = Submission.retrieve_task_grading_status_and_score_sum(latest_submission, include_hidden)
            last_submission_score_list.append(sum_student_score)

    num_enrolled_students = len(student_list)
    num_contributors = len(last_submission_score_list)

    if num_contributors == 0:
        score_statistics = None
    else:
        score_statistics = {
                'max_score': max(last_submission_score_list),
                'first_quantile': np.percentile(last_submission_score_list, 75),
                'mean_score': np.mean(last_submission_score_list),
                'median_score': np.median(last_submission_score_list),
                'third_quantile': np.percentile(last_submission_score_list, 25),
        }

    return (num_enrolled_students, num_contributors, score_statistics)
