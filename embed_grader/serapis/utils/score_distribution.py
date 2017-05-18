from serapis.models import *
from serapis.utils import grading
import numpy as np


def get_class_statistics(assignment, include_hidden):
    """
    Return:
      (num_total_teams, num_attempting_teams, score_statistics)
      - num_total_teams: number of teams formed in the class of this assignment
      - num_attempting_teams: number of teams that have tried this assignment so far
      - score_statistics: class statistics such as max, mean, 25th/75th-percentiles
    """

    # list of all teams enrolled in this class
    #TODO: exclude the instructor in the statistics
    team_list = Team.objects.filter(assignment_id=assignment)

    last_submission_score_list = []
    for team in team_list:
        latest_submission = grading.get_last_fully_graded_submission(team, assignment)
        if latest_submission:
            _, sum_score, _ = Submission.retrieve_task_grading_status_and_score_sum(
                    latest_submission, include_hidden)
            last_submission_score_list.append(sum_score)

    num_total_teams = len(team_list)
    num_attempting_teams = len(last_submission_score_list)

    if num_attempting_teams == 0:
        score_statistics = None
    else:
        score_statistics = {
                'max_score': round(max(last_submission_score_list), 2),
                'first_quantile': round(np.percentile(last_submission_score_list, 75), 2),
                'mean_score': round(np.mean(last_submission_score_list), 2),
                'median_score': round(np.median(last_submission_score_list), 2),
                'third_quantile': round(np.percentile(last_submission_score_list, 25), 2),
        }

    return (num_total_teams, num_attempting_teams, score_statistics)
