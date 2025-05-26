from django.shortcuts import render
from django.http import HttpResponseBadRequest
from users.models import Player, Player_Season_Stats, Season

def search_player_stats(request):
    season_id = request.GET.get('season_id')

    if not season_id:
        return HttpResponseBadRequest("Season ID is required.")

    stats = Player_Season_Stats.objects.filter(
        season_id=season_id
    ).order_by('-total_points').values(
        'player__name', 'season__season_name', 'team__team_name', 'goals_scored', 'assists', 'total_points'
    ).first()  

    return render(request, 'stats_list.html', {'stats': stats})

def all_players(request):
    players = Player.objects.all()  
    stats = Player_Season_Stats.objects.select_related('player', 'season', 'team')  
    return render(request, 'players_list.html', {'players': players, 'stats': stats})

def top_100_players(request):
    season_id = request.GET.get('season_id')  
    sort_by = request.GET.get('sort_by', 'total_points') 
    order = request.GET.get('order', 'desc')  

    if not season_id:
        return HttpResponseBadRequest("Season ID is required.")

    try:
        selected_season = Season.objects.get(season_id=season_id)
    except Season.DoesNotExist:
        return HttpResponseBadRequest("Invalid Season ID.")

    sort_prefix = '-' if order == 'desc' else ''
    sort_field = f"{sort_prefix}{sort_by}"

    top_players = Player_Season_Stats.objects.filter(
        season_id=season_id
    ).order_by(sort_field).values(
        'player_id', 'player__name', 'team__team_name', 'goals_scored', 'assists', 'saves', 'total_points'
    )[:100] 

    seasons = Season.objects.all()

    return render(request, 'top_100_players.html', {
        'top_players': top_players,
        'selected_season': selected_season,
        'seasons': seasons,
        'sort_by': sort_by,
        'order': order,
    })
