from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import Player, Season, Player_Season_Stats, Team, FantasyClub, Party

User = get_user_model()

class ViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        
        self.season = Season.objects.create(season_name='2024', season_id=1)
        self.team = Team.objects.create(team_name='Test Team', league='Test League', photo='team.jpg')
        self.player = Player.objects.create(player_id=1, name='John Doe')
        self.player_stats = Player_Season_Stats.objects.create(
            player_id=self.player.player_id,
            season_id=self.season.season_id,
            team=self.team,
            goals_scored=5,
            assists=3,
            saves=2,
            total_points=10,
            player=self.player
        )
        self.party = Party.objects.create(partyname='Test Party', tournament_id=1)
        self.fantasy_club = FantasyClub.objects.create(user=self.user, party=self.party)

    def test_home_page_status_and_context(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('seasons', response.context)
        self.assertIn('leagues', response.context)
        self.assertIn('top_players_by_league', response.context)

    def test_registration_get(self):
        response = self.client.get(reverse('registration'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_registration_post_valid(self):
        response = self.client.post(reverse('registration'), {
            'username': 'newuser',
            'email': 'sadad@ukr.net',
            'password': 'newpass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_login_post_valid(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)
                
    def test_logout_view_requires_login(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)

    def test_logout_view_after_login(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)

    def test_player_profile_exists(self):
        url = reverse('player_profile', args=[self.player.player_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('player', response.context)
        self.assertEqual(response.context['player'], self.player)

    def test_player_profile_not_found(self):
        url = reverse('player_profile', args=[999])  
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)  

    def test_user_profile_requires_login(self):
        url = reverse('user_profile', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  

    def test_user_profile_view(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('user_profile', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('profile_user', response.context)
        self.assertIn('clubs', response.context)

