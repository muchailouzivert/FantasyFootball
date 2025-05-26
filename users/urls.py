from django.urls import path

from .views import fantasy_fotball_views
from .views import user_views
from .views import home_views

urlpatterns = [
    path("", user_views.home, name="home"),
    path('registration/', user_views.registration_view, name='registration'),  
    path('login/', user_views.login_view, name='login'),  
    path('logout/', user_views.logout_view, name='logout'),  
    path('stats/', home_views.search_player_stats, name='player_stats'),
    path('players/', home_views.all_players, name='all_players'),
    path('top-100-players/', home_views.top_100_players, name='top_100_players'),
    path('player/<int:player_id>/', user_views.player_profile, name='player_profile'),
    path('create-team/', fantasy_fotball_views.create_random_team, name='create_team'),
    path('get-random-players/', fantasy_fotball_views.get_random_players, name='get_random_players'),
    path('submit-team/', fantasy_fotball_views.submit_team, name='submit_team'),
    path('create_party/', fantasy_fotball_views.create_party, name='create_party'),
    path('parties/', fantasy_fotball_views.parties_list, name='parties_list'),
    path('success/', fantasy_fotball_views.team_success, name='team_success'),
    path('club/<int:club_id>/', fantasy_fotball_views.club_detail, name='club_detail'),
    path('user/<int:user_id>/', user_views.user_profile, name='user_profile'),
    path('test_sim/<int:club1_id>/<int:club2_id>/', fantasy_fotball_views.test_simulation, name='test_simulation'),
]