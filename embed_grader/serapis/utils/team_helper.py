import random

from django.db import transaction

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
        team = Team.objects.create(assignment_fk=assignment)
        team.passcode = _generate_passcode(team)
        team.save()

        team_member_list = []
        for idx, user in enumerate(users):
            is_leader = (idx == 0)
            team_member = TeamMember.objects.create(team_fk=team, user_fk=user,
                    assignment_fk=assignment, is_leader=is_leader)
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
    member_list = TeamMember.objects.filter(user_fk=user, team_fk__assignment_fk=assignment)
    return member_list[0].team_fk if member_list else None

def delete_team(team):
    team.delete()

def add_users_to_team(team, users):
    """
    Add users to an existing team. These users have to be followers.

    Parameters:
      team: A Team object
      users: A list of User
    """
    assignment = team.assignment_fk
    if len(TeamMember.objects.filter(team_fk=team)) + len(users) > assignment.num_max_team_members:
        raise Exception('Maximum number of team members exceeds')

    with transaction.atomic():
        for user in users:
            if TeamMember.objects.filter(team_fk=team, user_fk=user):
                raise Exception('Some users have had belonged team')
            TeamMember.objects.create(team_fk=team, user_fk=user,
                    assignment_fk=assignment, is_leader=False)

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
        member_list = TeamMember.objects.filter(team_fk=team, user_fk=user)
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
    return TeamMember.objects.filter(team_fk=team).count()

def get_team_members(team):
    """
    Return:
      team_members: A list of team members. The first member is the leader.
    """
    # Since the first member is assumed to be the leader when the team is created, sorting by 
    # object id and accessing the first object can retrieve the team leader.
    return [tm for tm in TeamMember.objects.filter(team_fk=team).order_by('id')]

def get_specific_team_member(team, user):
    """
    Return:
      team_member: A TeamMember object, the specified team member
    """
    team_member_list = TeamMember.objects.filter(team_fk=team, user_fk=user)
    return team_member_list[0] if team_member_list else None

def get_team_member_full_name_list(team, last_and=False):
    """
    Parameter:
      last_and: Optional. When set to true, the output sounds more natural for humans.
    Return:
      name_list: A string
    """
    name_list = [user_info_helper.get_first_last_name(tm.user_fk) for tm
                    in TeamMember.objects.filter(team_fk=team).order_by('id')]
    result = ', '.join(name_list)

    if last_and: 
        if len(name_list) == 0:
            result = ''
        elif len(name_list) == 1:
            result = name_list[0]
        elif len(name_list) == 2:
            result = ' and '.join(name_list)
        else:
            result = ', '.join(name_list[:-1]) + ', and ' + name_list[-1]

    return result

def get_team_member_first_name_list(team):
    """
    Return:
      name_list: A string
    """
    return ', '.join([tm.user_fk.first_name for tm
            in TeamMember.objects.filter(team_fk=team).order_by('id')])
