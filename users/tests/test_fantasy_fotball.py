import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from users.models import Player, Team, Season, Player_Season_Stats, FantasyClub, Party, FantasyClubFootballer, Tournament

class FantasyFootballViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.season = Season.objects.create(season_id=1, season_name='2024')
        self.team = Team.objects.create(team_id=1, team_name='Test Team', country='UA', league='Test League')
        self.player = Player.objects.create(player_id=1, name='Test Player', position='GK')
        self.stats = Player_Season_Stats.objects.create(
            player=self.player, team=self.team, season=self.season, total_points=10
        )
        self.tournament = Tournament.objects.create(tournament_name='Test Tournament', start_date='2024-01-01', end_date='2024-12-31')
        self.party = Party.objects.create(tournament_id=self.tournament.id, partyname='Test Party')
        self.club = FantasyClub.objects.create(user=self.user, party=self.party, clubname='Test FC')
        FantasyClubFootballer.objects.create(fantasy_club=self.club, footballer=self.player)

    def test_get_random_players(self):
        url = reverse('get_random_players')
        response = self.client.get(url, {'position': 'goalkeepers', 'exclude': '[]'})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_create_random_team(self):
        url = reverse('create_team')
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 400])  

    def test_create_party(self):
        self.client.login(username='testuser', password='testpass')
        url = reverse('create_party')
        data = {'partyname': 'New Party', 'tournament_id': self.tournament.id}
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('party_id', response.json())

    def test_parties_list(self):
        self.client.login(username='testuser', password='testpass')
        url = reverse('parties_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'parties.html')

    def test_submit_team_wrong_method(self):
        self.client.login(username='testuser', password='testpass')
        url = reverse('submit_team')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_team_success(self):
        url = reverse('team_success')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'team_success.html')

    def test_club_detail(self):
        self.client.login(username='testuser', password='testpass')
        url = reverse('club_detail', args=[self.club.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'club_detail.html')

    def test_test_simulation(self):
        self.client.login(username='testuser', password='testpass')
        user2 = User.objects.create_user(username='testuser2', password='testpass2')
        club2 = FantasyClub.objects.create(user=user2, party=self.party, clubname='Test FC 2')
        url = reverse('test_simulation', args=[self.club.id, club2.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('goals1', response.json())