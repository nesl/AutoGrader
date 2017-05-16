import random

from serapis.models import *

from serapis.utils import user_info_helper


def _generate_passcode(team):
    return str(team.id * 100000 + random.randint(0, 99999))

def create_team(assignment, users):
    """
    Parameters:
      assignment: An Assignment object
      users: A list of User objects. The first user will be the leader of th team.
    Returns:
      (team, team_member_list)
    """
    if len(users) > assignment.num_max_team_members:
        raise Exception('Maximum number of team members exceeds')

    with transaction.atomic():
        team = Team.objects.create(assignment_id=assignment)
        team.passcode = _generate_passcode(team)
        team.save()

        team_member_list = []
        for idx, user in enumerate(users):
            is_leader = (idx == 0)
            team_member = TeamMember.objects.create(team_id=team, user_id=user,
                    assignment_id=assignment, is_leader=is_leader)
            team_member_list.append(team_member)

        return (team, team_member_list)

def check_passcode(passcode):
    """
    Parameter:
      passcode: a string presenting a passcode
    Return:
      A Team object if the passcode is valid, otherwise None
    """
    team_list = Team.objects.filter(passcode=passcode)
    return team_list[0] if team_list else None

def get_belonged_team(user, assignment):
    """
    Parameter:
      user: A User object
      assignment: An Assignment object
    Return:
      A Team object which the user belongs to, otherwise None
    """
    member_list = TeamMember.objects.filter(user_id=user, team_id__assignment_id=assignment)
    return member_list[0].team_id if member_list else None

def delete_team(team):
    team.delete()

def add_users_to_team(team, users):
    """
    Add users to an existing team. These users have to be followers.

    Parameters:
      team: A Team object
      users: A list of User
    """
    assignment = team.assignment_id
    if len(TeamMember.objects.filter(team_id=team)) + len(users) > assignment.num_max_team_members:
        raise Exception('Maximum number of team members exceeds')

    with transaction.atomic():
        for user in users:
            if TeamMember.objects.filter(team_id=team, user_id=user):
                raise Exception('Some users have had belonged team')
            TeamMember.objects.create(team_id=team, user_id=user,
                    assignment_id=assignment, is_leader=False)

    return True
            
def remove_users_from_team(team, users):
    """
    Remove users from an existing team. If a leader is among the user list, the entire team will
    be destroied.

    Parameters:
      team: A Team object
      users: A list of User
    """
    team_member_list = []
    for user in users:
        member_list = TeamMember.objects.filter(team_id=team, user_id=user)
        if not member_list:
            raise Exception('Some users do not belong this team')
        team_member_list.append(member_list[0])
    
    if any([m.is_leader for m in team_member_list]):
        team.delete()
    else:
        for m in team_member_list:
            m.delete()

def get_num_team_members(team):
    """
    Return:
      num_team_members: int
    """
    return TeamMember.objects.filter(team_id=team).count()

def get_team_members(team):
    """
    Return:
      team_members: A list of team members. The first member is the leader.
    """
    # Since the first member is assumed to be the leader when the team is created, sorting by 
    # object id and accessing the first object can retrieve the team leader.
    return [tm for tm in TeamMember.objects.filter(team_id=team).order_by('id')]

def get_specific_team_member(team, user):
    """
    Return:
      team_member: A TeamMember object, the specified team member
    """
    team_member_list = TeamMember.objects.filter(team_id=team, user_id=user)
    return team_member_list[0] if team_member_list else None

def get_team_member_full_name_list(team):
    """
    Return:
      name_list: A string
    """
    return ', '.join([user_info_helper.get_first_last_name(tm.user_id) for tm
            in TeamMember.objects.filter(team_id=team).order_by('id')])

def get_team_member_first_name_list(team):
    """
    Return:
      name_list: A string
    """
    return ', '.join([tm.user_id.first_name for tm
            in TeamMember.objects.filter(team_id=team).order_by('id')])
