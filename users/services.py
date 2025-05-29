from collections import Counter
from django.db import connection
from django.db.models import Sum
from .models import Player_Season_Stats, FantasyResult
from django.utils import timezone
from django.core.exceptions import ValidationError
import numpy as np
from datetime import datetime

def get_club_strength(club_id, season_id=3):
    stats = Player_Season_Stats.objects.filter(
        player__fantasyclub__id=club_id,
        season_id=season_id
    )

    strength = stats.aggregate(total=Sum('total_points'))['total'] or 0

    teams = list(stats.values_list('team_id', flat=True))
    bonus = 0
    most_common = Counter(teams).most_common(1)
    if most_common and most_common[0][1] >= 5:
        bonus = strength * 0.2  

    return strength + bonus

def fetch_club_footballers(club_id, season_id=3):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.player_id, p.name, p.position, ps.total_points, ps.team_id
            FROM fantasy_clubs_footballers fcf
            JOIN players p ON fcf.footballer_id = p.player_id
            LEFT JOIN player_season_stats ps 
                ON ps.player_id = p.player_id AND ps.season_id = %s
            WHERE fcf.fantasy_club_id = %s
        """, [season_id, club_id])
        return [
            {'id': row[0], 'name': row[1], 'position': row[2], 'total_points': row[3], 'team_id': row[4]}
            for row in cursor.fetchall()
        ]


def calculate_team_strength(fantasy_club_players):
    strength = 0
    team_bonus = 0

    for p in fantasy_club_players:
        strength += p.total_points or 0

    teams = [p.team_id for p in fantasy_club_players if getattr(p, 'team_id', None)]
    if teams:
        most_common_team, count = Counter(teams).most_common(1)[0]
        if count >= 5:
            team_bonus = strength * 0.2 

    return strength + team_bonus


def get_strength(club_id, season_id=3):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT ps.total_points
            FROM fantasy_clubs_footballers fcf
            JOIN player_season_stats ps ON fcf.footballer_id = ps.player_id
            WHERE fcf.fantasy_club_id = %s AND ps.season_id = %s
        """, [club_id, season_id])
        return sum(row[0] or 0 for row in cursor.fetchall())

def simulate_fantasy_match(club1, club2, n_attempts=90, scale=0.5, tour=1):
    if club1.id == club2.id:
        raise ValueError("Команда не може грати сама з собою!")

    if club1.party_id != club2.party_id:
        raise ValueError("Обидві команди мають бути з однієї party!")

    strength1 = get_strength(club1)
    strength2 = get_strength(club2)

    total_strength = strength1 + strength2
    if total_strength == 0:
        p_goal_1 = p_goal_2 = 0.05
    else:
        p_goal_1 = 0.02 + 0.18 * (strength1 / total_strength)  
        p_goal_2 = 0.02 + 0.18 * (strength2 / total_strength)

    goals1 = 0
    goals2 = 0
    current_p1 = p_goal_1
    current_p2 = p_goal_2

    for minute in range(1, n_attempts + 1):
        if np.random.rand() < current_p1:
            goals1 += 1
            current_p1 *= scale
        if np.random.rand() < current_p2:
            goals2 += 1
            current_p2 *= scale

    result = FantasyResult.objects.create(
        date=datetime.now(),
        tour=tour,
        party=club1.party,
        home_club=club1,
        away_club=club2,
        home_goals=goals1,
        away_goals=goals2,
        home_points=goals1,  
        away_points=goals2,  
    )

    return goals1, goals2, result