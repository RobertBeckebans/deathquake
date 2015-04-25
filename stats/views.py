import json
import operator
import math
from collections import defaultdict

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.views.generic import View, TemplateView
from django.http import HttpResponse

from stats.models import Game, Frag, Player, Scoreboard


def score_14(score):
    result = ''
    beers = int(math.floor(score))
    sips = int(round((score - beers) * 14))
    if beers == 0 and sips == 0:
        return result
    if sips == 14:
        beers += 1
        sips = 0
    if beers >= 1:
        result += str(beers)
    if beers == 1:
        result += ' beer'
    elif beers > 1:
        result += ' beers'

    if sips != 0:
        if beers >= 1:
            result += ' and '
        result += str(sips) + ' '

        if sips == 1:
            result += 'sip'
        else:
            result += 'sips'

    return result


def at_least_two_games():
    return Game.objects.all().filter(fraglimit__gt=0).count() > 1


class ScoreboardView(View):
    def __init__(self, **kwargs):
        super(ScoreboardView, self).__init__(**kwargs)
        self.scoreboard = defaultdict(lambda: defaultdict(dict))

    def get(self, request, *args, **kwargs):
        self.process_players()
        self.process_scoreboard()
        self.process_frags()
        self.ban_world()
        self.delete_banned()
        self.set_ranks()
        self.set_previous_ranks()
        self.set_rank_differences()
        self.assign_trophies()
        self.round_numbers()

        return HttpResponse(json.dumps((
            {"status": "success"},
            {"data": self.scoreboard},
        ),
            cls=DjangoJSONEncoder))

    def initialize_variables(self, player):
        self.scoreboard[player.id]['deaths'] = 0
        self.scoreboard[player.id]['fall_deaths'] = 0
        self.scoreboard[player.id]['gauntlet_kills'] = 0
        self.scoreboard[player.id]['highest_kill_streak'] = 0
        self.scoreboard[player.id]['kill_death_ratio'] = 0.0
        self.scoreboard[player.id]['kills'] = 0
        self.scoreboard[player.id]['previous_rank'] = 0
        self.scoreboard[player.id]['previous_score'] = 0.0
        self.scoreboard[player.id]['railgun_kills'] = 0
        self.scoreboard[player.id]['rank'] = 0
        self.scoreboard[player.id]['rank_difference'] = 0
        self.scoreboard[player.id]['rocket_kills'] = 0
        self.scoreboard[player.id]['score'] = 0.0
        self.scoreboard[player.id]['score_14'] = ""
        self.scoreboard[player.id]['score_14_difference'] = ""
        self.scoreboard[player.id]['score_difference'] = 0.0
        self.scoreboard[player.id]['trophy_deaths'] = False
        self.scoreboard[player.id]['trophy_fall_deaths'] = False
        self.scoreboard[player.id]['trophy_highest_kill_streak'] = False
        self.scoreboard[player.id]['trophy_kill_death_ratio'] = False
        self.scoreboard[player.id]['trophy_kills'] = False
        self.scoreboard[player.id]['trophy_railgun_kills'] = False
        self.scoreboard[player.id]['trophy_rocket_kills'] = False
        self.scoreboard[player.id]['trophy_winner'] = False
        self.scoreboard[player.id]['trophy_won_games'] = False
        self.scoreboard[player.id]['trophy_won_last_game'] = False
        self.scoreboard[player.id]['won_games'] = 0

    def process_players(self):
        for player in Player.objects.all():
            self.scoreboard[player.id]['name'] = player.name
            self.scoreboard[player.id]['is_banned'] = player.is_banned
            self.initialize_variables(player)

    def process_scoreboard(self):

        for score in Scoreboard.objects.all(

        ).select_related(
                'player', 'game'
        ).values(
                'player__id', 'game__fraglimit', 'score', 'game__id'
        ):
            scoreboard_player = self.scoreboard[score['player__id']]
            scoreboard_player['score'] += (float(score['score']) / float(score['game__fraglimit']))
            last_valid_game_id = Game.objects.all().filter(fraglimit__gt=0).last().id

            if score['game__id'] == last_valid_game_id:
                scoreboard_player['score_difference'] = float(score['score']) / float(score['game__fraglimit'])
                scoreboard_player['score_14_difference'] = score_14(scoreboard_player['score_difference'])
            else:
                scoreboard_player['previous_score'] += (float(score['score']) / float(score['game__fraglimit']))

            if score['score'] == score['game__fraglimit']:
                scoreboard_player['won_games'] += 1

        for player in self.scoreboard:
            self.scoreboard[player]['score_14'] = score_14(self.scoreboard[player]['score'])

    def process_frags(self):
        current_kill_streak = defaultdict(int)
        for frag in Frag.objects.all():
            attacker = self.scoreboard[frag.attacker_id]
            victim = self.scoreboard[frag.victim_id]
            if not frag.attacker_id == frag.victim_id:
                attacker['kills'] += 1
            else:
                attacker['kills'] -= 1
            victim['deaths'] += 1

            if frag.weapon == 'MOD_RAILGUN':
                attacker['railgun_kills'] += 1

            if frag.weapon == 'MOD_GAUNTLET':
                attacker['gauntlet_kills'] += 1

            if frag.weapon == 'MOD_ROCKET' or frag.weapon == 'MOD_ROCKET_SPLASH':
                attacker['rocket_kills'] += 1

            if frag.weapon == 'MOD_FALLING':
                victim['fall_deaths'] += 1

            current_kill_streak[frag.attacker_id] += 1
            current_kill_streak[frag.victim_id] = 0
            attacker['highest_kill_streak'] = max(attacker['highest_kill_streak'],
                                                  current_kill_streak[frag.attacker_id])

        for player in self.scoreboard:
            if self.scoreboard[player]['deaths'] == 0:
                self.scoreboard[player]['kill_death_ratio'] = self.scoreboard[player]['kills']
            else:
                self.scoreboard[player]['kill_death_ratio'] = \
                    float(self.scoreboard[player]['kills']) / float(self.scoreboard[player]['deaths'])

    def ban_world(self):
        for player in self.scoreboard:
            if self.scoreboard[player]['name'] == '<world>':
                self.scoreboard[player]['is_banned'] = True

    def delete_banned(self):
        entries_to_remove = []
        for player in self.scoreboard:
            if self.scoreboard[player]['is_banned']:
                entries_to_remove.append(player)
        for entry in entries_to_remove:
            del self.scoreboard[entry]

    def set_ranks(self):
        score_dictionary = dict()
        for player in self.scoreboard:
            score_dictionary[player] = self.scoreboard[player]['score']
        sorted_score_list = sorted(score_dictionary.items(), key=operator.itemgetter(1), reverse=True)
        for counter, score in enumerate(sorted_score_list):
            self.scoreboard[score[0]]['rank'] = counter + 1

    def set_previous_ranks(self):
        if at_least_two_games():
            score_dictionary = dict()
            for player in self.scoreboard:
                score_dictionary[player] = self.scoreboard[player]['previous_score']
            sorted_score_list = sorted(score_dictionary.items(), key=operator.itemgetter(1), reverse=True)
            for counter, score in enumerate(sorted_score_list):
                self.scoreboard[score[0]]['previous_rank'] = counter + 1

    def round_numbers(self):
        for player in self.scoreboard:
            self.scoreboard[player]['score'] = format(self.scoreboard[player]['score'], '0.4f')
            self.scoreboard[player]['kill_death_ratio'] = format(self.scoreboard[player]['kill_death_ratio'], '0.4f')

    def assign_trophies(self):
        # TODO: Woah! Do something here!
        max_railgun_kills = 0
        max_rocket_kills = 0
        max_won_games = 0
        max_highest_kill_streak = 0
        max_fall_deaths = 0
        max_gauntlet_kills = 0
        max_kills = 0
        max_deaths = 0
        max_kill_death_ratio = 0

        for player in self.scoreboard:
            scoreboard_player = self.scoreboard[player]
            if scoreboard_player['score_difference'] == 1:
                scoreboard_player['trophy_won_last_game'] = True
            if scoreboard_player['score'] >= settings.DEATHQUAKE_WINNER_SCORE and scoreboard_player['rank'] == 1:
                scoreboard_player['trophy_winner'] = True
            max_railgun_kills = max(max_railgun_kills, scoreboard_player['railgun_kills'])
            max_rocket_kills = max(max_rocket_kills, scoreboard_player['rocket_kills'])
            max_won_games = max(max_won_games, scoreboard_player['won_games'])
            max_highest_kill_streak = max(max_highest_kill_streak, scoreboard_player['highest_kill_streak'])
            max_fall_deaths = max(max_fall_deaths, scoreboard_player['fall_deaths'])
            max_gauntlet_kills = max(max_gauntlet_kills, scoreboard_player['gauntlet_kills'])
            max_kills = max(max_kills, scoreboard_player['kills'])
            max_deaths = max(max_deaths, scoreboard_player['deaths'])
            max_kill_death_ratio = max(max_kill_death_ratio, scoreboard_player['kill_death_ratio'])

        for player in self.scoreboard:
            scoreboard_player = self.scoreboard[player]
            if scoreboard_player['railgun_kills'] == max_railgun_kills and max_railgun_kills > 0:
                scoreboard_player['trophy_railgun_kills'] = True
            if scoreboard_player['rocket_kills'] == max_rocket_kills and max_rocket_kills > 0:
                scoreboard_player['trophy_rocket_kills'] = True
            if scoreboard_player['won_games'] == max_won_games and max_won_games > 0:
                scoreboard_player['trophy_won_games'] = True
            if scoreboard_player['highest_kill_streak'] == max_highest_kill_streak and max_highest_kill_streak > 0:
                scoreboard_player['trophy_highest_kill_streak'] = True
            if scoreboard_player['fall_deaths'] == max_fall_deaths and max_fall_deaths > 0:
                scoreboard_player['trophy_fall_deaths'] = True
            if scoreboard_player['gauntlet_kills'] == max_gauntlet_kills and max_gauntlet_kills > 0:
                scoreboard_player['trophy_gauntlet_kills'] = True
            if scoreboard_player['kills'] == max_kills and max_kills > 0:
                scoreboard_player['trophy_kills'] = True
            if scoreboard_player['deaths'] == max_deaths and max_deaths > 0:
                scoreboard_player['trophy_deaths'] = True
            if scoreboard_player['kill_death_ratio'] == max_kill_death_ratio and max_kill_death_ratio > 0:
                scoreboard_player['trophy_kill_death_ratio'] = True

    def set_rank_differences(self):
        if at_least_two_games():
            for player in self.scoreboard:
                self.scoreboard[player]['rank_difference'] = \
                    self.scoreboard[player]['previous_rank'] - self.scoreboard[player]['rank']


class StatsView(TemplateView):
    template_name = "stats.html"