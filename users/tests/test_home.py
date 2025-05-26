from django.test import TestCase, Client
from django.urls import reverse
from users.models import Player, Team, Season, Player_Season_Stats

class HomeViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.season = Season.objects.create(season_id=1, season_name='2024')
        self.team = Team.objects.create(team_id=1, team_name='Test Team', country='UA', league='Test League')
        self.player = Player.objects.create(player_id=1, name='Test Player', position='GK')
        self.stats = Player_Season_Stats.objects.create(
            player=self.player, team=self.team, season=self.season,
            goals_scored=5, assists=2, saves=10, total_points=20
        )

    def test_search_player_stats_success(self):
        url = reverse('player_stats')
        response = self.client.get(url, {'season_id': self.season.season_id})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'stats_list.html')
        self.assertIn('stats', response.context)

    def test_search_player_stats_no_season(self):
        url = reverse('player_stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_all_players(self):
        url = reverse('all_players')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'players_list.html')
        self.assertIn('players', response.context)
        self.assertIn('stats', response.context)

    def test_top_100_players_success(self):
        url = reverse('top_100_players')
        response = self.client.get(url, {'season_id': self.season.season_id})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'top_100_players.html')
        self.assertIn('top_players', response.context)

    def test_top_100_players_no_season(self):
        url = reverse('top_100_players')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_top_100_players_invalid_season(self):
        url = reverse('top_100_players')
        response = self.client.get(url, {'season_id': 999})
        self.assertEqual(response.status_code, 400)