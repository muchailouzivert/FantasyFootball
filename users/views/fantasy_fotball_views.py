import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseBadRequest, JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from users.models import Player_Season_Stats, FantasyClub, Party, FantasyClubFootballer, Tournament
from users.services import fetch_club_footballers, calculate_team_strength, simulate_fantasy_match
from random import sample

def get_random_players(request):
    frontend_position = request.GET.get('position')
    exclude_json = request.GET.get('exclude', '[]')

    try:
        exclude_ids = json.loads(exclude_json)
    except json.JSONDecodeError:
        exclude_ids = []

    position_map = {
        'goalkeepers': 'GK',
        'defenders': 'DEF',
        'midfielders': 'MID',
        'forwards': 'FWD',
    }
    position = position_map.get(frontend_position)
    if not position:
        return JsonResponse([], safe=False)

    latest_season_stats = Player_Season_Stats.objects.select_related('player', 'team').values(
        'player__player_id', 'player__name', 'player__position',
        'team__team_name', 'team__photo', 'total_points'
    ).filter(player__position=position).exclude(player__player_id__in=exclude_ids)

    stats_list = list(latest_season_stats)
    selected_players = sample(stats_list, min(4, len(stats_list))) if stats_list else []

    for p in selected_players:
        if p['team__photo']:
            p['team__photo'] = f"{settings.MEDIA_URL}teams/{p['team__photo']}"

    data = [
        {
            'id': p['player__player_id'],
            'name': p['player__name'],
            'club': p['team__team_name'],
            'club_photo': p['team__photo'],
            'position': p['player__position'],
            'total_points': p['total_points'],
        } for p in selected_players
    ]

    return JsonResponse(data, safe=False)

def create_random_team(request):
    selected_player_ids = json.loads(request.GET.get('selected_players', '[]'))
    used_player_ids = set(FantasyClubFootballer.objects.values_list('footballer_id', flat=True))
    exclude_ids = set(selected_player_ids) | used_player_ids

    stats = Player_Season_Stats.objects.select_related('player', 'team').filter(
        season_id=3
    ).exclude(player__player_id__in=exclude_ids).values(
        'player__player_id', 'player__name', 'player__position',
        'team__team_name', 'team__photo', 'total_points'
    )

    grouped = {'GK': [], 'DEF': [], 'MID': [], 'FWD': []}
    for stat in stats:
        grouped[stat['player__position']].append(stat)
        if stat['team__photo']:
            stat['team__photo'] = f"{settings.MEDIA_URL}teams/{stat['team__photo']}"

    def serialize(players, count):
        return [
            {
                'id': p['player__player_id'],
                'name': p['player__name'],
                'position': p['player__position'],
                'club': p['team__team_name'],
                'club_photo': p['team__photo'],
                'total_points': p['total_points']
            } for p in sample(players, min(count, len(players)))
        ]

    if any(len(grouped[pos]) < req for pos, req in [('GK', 1), ('DEF', 4), ('MID', 4), ('FWD', 2)]):
        return HttpResponseBadRequest("Недостатньо гравців для створення команди.")

    context = {
        'goalkeepers': serialize(grouped['GK'], 4),
        'defenders': serialize(grouped['DEF'], 4),
        'midfielders': serialize(grouped['MID'], 4),
        'forwards': serialize(grouped['FWD'], 4),
    }

    if any(len(grouped[pos]) < 4 for pos in ['GK', 'DEF', 'MID', 'FWD']):
        return HttpResponseBadRequest("Недостатньо гравців для створення команди.")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(context, safe=False)

    for key in context:
        context[key] = json.dumps(context[key])

    return render(request, 'create_team.html', context)

@login_required
def create_party(request):
    try:
        data = json.loads(request.body)
        party = Party.objects.create(
            tournament_id=data.get('tournament_id', 1),
            partyname=data.get('partyname', f"Команда {request.user.username}")
        )
        return JsonResponse({'party_id': party.id, 'partyname': party.partyname})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def parties_list(request):
    parties = Party.objects.all()
    tournaments = {t.id: t for t in Tournament.objects.all()}
    for party in parties:
        party.tournament_obj = tournaments.get(party.tournament_id)
        party.user_has_club = FantasyClub.objects.filter(user=request.user, party=party).exists()
    return render(request, 'parties.html', {'parties': parties})

@login_required
def submit_team(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Неправильний метод запиту.")

    try:
        data = json.loads(request.body)
        all_player_ids = [data.get('goalkeeper')] + data.get('defenders', []) + data.get('midfielders', []) + data.get('forwards', [])
        if len(all_player_ids) != 11 or not data.get('party_id'):
            return HttpResponseBadRequest("Невірна кількість гравців або відсутній party_id.")

        party = get_object_or_404(Party, id=data['party_id'])
        if FantasyClub.objects.filter(user=request.user, party=party).exists():
            return HttpResponseBadRequest("Ви вже створили команду для цієї party.")

        club = FantasyClub.objects.create(user=request.user, party=party, clubname=f"{request.user.username} FC")
        FantasyClubFootballer.objects.bulk_create([
            FantasyClubFootballer(fantasy_club=club, footballer_id=pid)
            for pid in all_player_ids
        ])
        return redirect('team_success')
    except Exception as e:
        return HttpResponseBadRequest(f"Помилка при збереженні: {str(e)}")

def team_success(request):
    return render(request, 'team_success.html')

@login_required
def club_detail(request, club_id):
    club = get_object_or_404(FantasyClub, id=club_id)
    footballers = fetch_club_footballers(club_id)
    total_strength = calculate_team_strength([
        type('obj', (object,), f) for f in footballers
    ])
    return render(request, 'club_detail.html', {
        'club': club,
        'footballers': footballers,
        'total_strength': int(total_strength),
    })

def test_simulation(request, club1_id, club2_id):
    club1 = FantasyClub.objects.get(id=club1_id)
    club2 = FantasyClub.objects.get(id=club2_id)
    goals1, goals2, result_obj = simulate_fantasy_match(club1, club2)
    return JsonResponse({
        "club1": club1.clubname,
        "club2": club2.clubname,
        "goals1": goals1,
        "goals2": goals2,
        "result": (
            "draw" if goals1 == goals2 else
            f"{club1.clubname} wins" if goals1 > goals2 else
            f"{club2.clubname} wins"
        ),
        "result_id": result_obj.id
    })


