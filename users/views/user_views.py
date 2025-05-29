from django.shortcuts import render, redirect
from users.forms import UserRegistrationForm, LoginForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from users.models import Player_Season_Stats, Season, Player, Team, User, FantasyClub
from django.db.models import Sum
from django.conf import settings
from django.http import HttpResponseBadRequest


def home(request):
    seasons = Season.objects.all()

    leagues = Team.objects.all()

    top_players_by_league = {}
    for league in leagues:
        top_players = Player_Season_Stats.objects.filter(
            team__league=league.league  
        ).order_by('-total_points').values(
            'player_id', 'player__name', 'team__team_name', 'total_points'
        )[:10]
        top_players_by_league[league.league] = top_players

    random_season = seasons.order_by('?').first()
    best_player = None
    best_player_team_photo = None

    if random_season:
        best_player = Player_Season_Stats.objects.filter(
            season_id=random_season.season_id
        ).order_by('-total_points').values(
            'player_id', 'player__name', 'team__team_name', 'goals_scored', 'assists', 'total_points'
        ).first()

        if best_player and best_player.get('team__team_name'):
            team = Team.objects.filter(
                team_name=best_player['team__team_name']
            ).values('photo').first()

            if team and team['photo']:
                best_player_team_photo = f"{settings.MEDIA_URL}/teams/{team['photo']}"

    return render(request, 'home.html', {
        'seasons': seasons,
        'random_season': random_season,
        'best_player': best_player,
        'best_player_team_photo': best_player_team_photo,
        'leagues': leagues,
        'top_players_by_league': top_players_by_league,
    })

def registration_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save() 
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Ви успішно зареєструвалися та увійшли в систему.")
                return redirect("home")
    else:
        form = UserRegistrationForm()

    return render(request, "users/registration.html", {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            print(f"Attempting to authenticate user: {username}") 
            user = authenticate(request, username=username, password=password)
            if user is not None:
                print(f"Authenticated user: {user}")  
                login(request, user)
                return redirect('home')
            else:
                print("Authentication failed")  
                messages.error(request, "Неправильний логін або пароль.")
        else:
            print("Form is invalid")  
            messages.error(request, "Будь ласка, виправте помилки у формі.")
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Ви успішно вийшли з системи.")
    return redirect('home') 

def player_profile(request, player_id):
    season_id = request.GET.get('season_id') 

    try:
        player = Player.objects.get(player_id=player_id)
    except Player.DoesNotExist:
        return HttpResponseBadRequest("Player not found.")

    seasons = Season.objects.all()

    if not season_id:
        season_id = seasons.first().season_id if seasons.exists() else None

    stats = None
    team_photo = None
    if season_id:
        stats = Player_Season_Stats.objects.filter(
            player_id=player_id, season_id=season_id
        ).order_by('-total_points').values(
            'season__season_name',
            'team__team_name',
            'goals_scored',
            'assists',
            'saves',
            'total_points'
        ).first()

        if stats and stats.get('team__team_name'):
            team = Team.objects.filter(
                team_name=stats['team__team_name']
            ).values('photo').first()
            if team and team['photo']:
                team_photo = f"{settings.MEDIA_URL}/teams/{team['photo']}"

    total_seasons = Player_Season_Stats.objects.filter(player_id=player_id).values('season_id').distinct().count()
    total_goals = Player_Season_Stats.objects.filter(player_id=player_id).aggregate(Sum('goals_scored'))['goals_scored__sum'] or 0
    total_assists = Player_Season_Stats.objects.filter(player_id=player_id).aggregate(Sum('assists'))['assists__sum'] or 0

    return render(request, 'players.html', {
        'player': player,
        'stats': stats,
        'team_photo': team_photo,  
        'seasons': seasons,
        'selected_season_id': season_id,
        'total_seasons': total_seasons,
        'total_goals': total_goals,
        'total_assists': total_assists,
    })

@login_required
def user_profile(request, user_id):
    user = User.objects.get(id=user_id)
    clubs = FantasyClub.objects.filter(user=user).select_related('party')
    return render(request, 'users/user_profile.html', {
        'profile_user': user,
        'clubs': clubs,
    })\
    
