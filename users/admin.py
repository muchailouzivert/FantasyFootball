from django.contrib import admin
from .models import (
    Player, Team, Season, Player_Season_Stats,
    Tournament, Party, FantasyClub, FantasyClubFootballer)
from django.db.models import OuterRef, Subquery, IntegerField
from django.contrib import messages
from users.services import simulate_fantasy_match

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('player_id', 'name', 'position')
    search_fields = ('name', 'position')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('team_id', 'team_name', 'country', 'league')
    search_fields = ('team_name', 'country', 'league')

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('season_id', 'season_name')
    search_fields = ('season_name',)

@admin.register(Player_Season_Stats)
class PlayerSeasonStatsAdmin(admin.ModelAdmin):
    list_display = ('player', 'season', 'team', 'goals_scored', 'assists', 'total_points')
    search_fields = ('player__name', 'season__season_name', 'team__team_name')

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('id', 'tournament_name', 'start_date', 'end_date')
    search_fields = ('tournament_name',)

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('id', 'partyname', 'tournament_id')
    search_fields = ('partyname',)

class FantasyClubFootballerInline(admin.TabularInline):
    model = FantasyClubFootballer
    extra = 1
    can_delete = True
    verbose_name = "Гравець"
    verbose_name_plural = "Гравці"
    fields = ('footballer',)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == "footballer":
            used_player_ids = FantasyClubFootballer.objects.values_list('footballer_id', flat=True)
            stats = Player_Season_Stats.objects.filter(
                player=OuterRef('pk'), season_id=3
            ).values('total_points')
            kwargs["queryset"] = Player.objects.exclude(
                player_id__in=used_player_ids
            ).annotate(
                points=Subquery(stats[:1], output_field=IntegerField())
            ).order_by('-points', 'name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(FantasyClub)
class FantasyClubAdmin(admin.ModelAdmin):
    list_display = ('id', 'clubname', 'user', 'party')
    search_fields = ('clubname', 'user__username', 'party__partyname')
    inlines = [FantasyClubFootballerInline]
    actions = ['test_simulation']

    def test_simulation(self, request, queryset):
        if queryset.count() != 2:
            self.message_user(request, "Оберіть рівно 2 команди для симуляції!", level=messages.ERROR)
            return
        club1, club2 = queryset
        goals1, goals2, result_obj = simulate_fantasy_match(club1, club2)
        self.message_user(
            request,
            f"Симуляція: {club1.clubname} {goals1} : {goals2} {club2.clubname} (ID результату: {result_obj.id})",
            level=messages.SUCCESS
        )
    test_simulation.short_description = "Симулювати матч між двома обраними командами"

@admin.register(FantasyClubFootballer)
class FantasyClubFootballerAdmin(admin.ModelAdmin):
    list_display = ('fantasy_club', 'footballer')
    search_fields = ('fantasy_club__clubname', 'footballer__name')
