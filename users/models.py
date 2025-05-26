from django.db import models
from django.contrib.auth.models import User

class Player(models.Model):
    player_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=10)

    class Meta:
        db_table = 'players'     
        managed = False          

    def __str__(self):
        return f"{self.name} ({self.position})"

class Team(models.Model):
    team_id = models.AutoField(primary_key=True)
    team_name = models.CharField(max_length=255)
    country = models.CharField(max_length=100)
    league = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='team_photos/', null=True, blank=True)  # Add this field

    class Meta:
        db_table = 'teams'
        managed = False

    def __str__(self):
        return f"{self.team_name} ({self.league})"

class Season(models.Model):
    season_id = models.AutoField(primary_key=True)
    season_name = models.CharField(max_length=10)

    class Meta:
        db_table = 'seasons'
        managed = False

    def __str__(self):
        return self.season_name

class Player_Season_Stats(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, db_column='player_id')
    season = models.ForeignKey(Season, on_delete=models.CASCADE, db_column='season_id')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, db_column='team_id')

    goals_scored = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    bonus = models.IntegerField(default=0)
    bps = models.IntegerField(default=0)
    clean_sheets = models.IntegerField(default=0)
    creativity = models.FloatField(default=0)
    ict_index = models.FloatField(default=0)
    influence = models.FloatField(default=0)
    minutes = models.IntegerField(default=0)
    own_goals = models.IntegerField(default=0)
    penalties_missed = models.IntegerField(default=0)
    penalties_saved = models.IntegerField(default=0)
    red_cards = models.BooleanField(default=False)
    saves = models.IntegerField(default=0)
    yellow_cards = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)

    class Meta:
        db_table = 'player_season_stats'
        unique_together = ('player', 'season', 'team')  
        managed = False

    def __str__(self):
        return f"{self.player.name} ({self.season.season_name})"
    
class Tournament(models.Model):
    id = models.AutoField(primary_key=True)
    tournament_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        db_table = 'tournaments'
        managed = False

    def __str__(self):
        return self.tournament_name

class Party(models.Model):
    tournament_id = models.IntegerField()
    partyname = models.CharField(max_length=255)

    class Meta:
        db_table = 'parties'
        managed = False

    def __str__(self):
        return self.partyname


class FantasyClub(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    clubname = models.CharField(max_length=255)

    class Meta:
        db_table = 'fantasy_clubs'
        managed = False

    def __str__(self):
        return self.clubname
    
    
class FantasyClubFootballer(models.Model):
    fantasy_club = models.ForeignKey(FantasyClub, on_delete=models.CASCADE)
    footballer = models.ForeignKey(Player, on_delete=models.CASCADE)

    class Meta:
        db_table = 'fantasy_clubs_footballers'
        unique_together = (('fantasy_club', 'footballer'),)
        managed = False  

class FantasyResult(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateTimeField()
    tour = models.IntegerField()
    party = models.ForeignKey(Party, on_delete=models.CASCADE, db_column='party_id')
    home_club = models.ForeignKey(FantasyClub, on_delete=models.CASCADE, related_name='home_results', db_column='home_club_id')
    away_club = models.ForeignKey(FantasyClub, on_delete=models.CASCADE, related_name='away_results', db_column='away_club_id')
    home_goals = models.IntegerField()
    away_goals = models.IntegerField()
    home_points = models.IntegerField()
    away_points = models.IntegerField()

    class Meta:
        db_table = 'fantasy_results'
        managed = False

    def __str__(self):
        return f"{self.home_club} vs {self.away_club} ({self.date.date()})"