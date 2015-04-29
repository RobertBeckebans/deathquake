from django.core.management import call_command
from django.test import TestCase
from stats.models import Scoreboard, Player, Frag, Game
from stats.management.commands import parse


class TestParserMethods(TestCase):
    def setUp(self):
        self.parseCommand = parse.Command()

    def test_extract_attacker_and_victim_from_frag(self):
        frag1 = "Kill: 1 3 7: Cramer killed Sobuno by MOD_ROCKET_SPLASH\n"
        frag2 = "Kill: 6 7 2: DenGraeskeAdonis killed Der Uber Mensh by MOD_GAUNTLET\n"
        frag3 = "Kill: 6 7 2: Der Uber Mensh killed DenGraeskeAdonis by MOD_GAUNTLET\n"
        self.assertEqual('Cramer', parse.Command.extract_attacker_from_frag(self.parseCommand, frag1))
        self.assertEqual('Sobuno', parse.Command.extract_victim_from_frag(self.parseCommand, frag1))
        self.assertEqual('DenGraeskeAdonis', parse.Command.extract_attacker_from_frag(self.parseCommand, frag2))
        self.assertEqual('Der Uber Mensh', parse.Command.extract_victim_from_frag(self.parseCommand, frag2))
        self.assertEqual('Der Uber Mensh', parse.Command.extract_attacker_from_frag(self.parseCommand, frag3))
        self.assertEqual('DenGraeskeAdonis', parse.Command.extract_victim_from_frag(self.parseCommand, frag3))

    def test_killed_player_names_are_caught(self):
        frag1 = "Kill: 1 3 7: Cramer killed Sobuno by MOD_ROCKET_SPLASH\n"
        self.assertFalse(parse.Command.contains_more_than_one_killed_string(self.parseCommand, frag1))
        frag2 = "Kill: 6 7 2: Der Uberkilled Mensh killed DenGraeskeAdonis by MOD_GAUNTLET\n"
        self.assertTrue(parse.Command.contains_more_than_one_killed_string(self.parseCommand, frag2))


class TestParserOnGameWithBots(TestCase):
    def setUp(self):
        args = ['testcases/game_with_bots.txt', '--test']
        call_command('parse', *args)

    def player_tank_jr_has_a_total_score_of_193(self):
        player_tank_jr = Player.objects.get(name='TankJr')
        total_score = 0
        for scoreboard in Scoreboard.objects.filter(player=player_tank_jr):
            total_score += scoreboard.score
        self.assertEqual(total_score, 193)

    def test_correct_number_of_objects_have_been_created(self):
        self.assertEqual(Scoreboard.objects.all().count(), 56)
        self.assertEqual(Frag.objects.all().count(), 1894)
        self.assertEqual(Player.objects.all().count(), 9)
        self.assertTrue(Player.objects.get(name='TankJr'))
        self.player_tank_jr_has_a_total_score_of_193()


class TestParserOnKills(TestCase):
    def setUp(self):
        args = ['testcases/kills.txt', '--test']
        call_command('parse', *args)

    def test_names_with_spaces_gets_parsed(self):
        von = Player.objects.get(name='von Schpandh')
        self.assertTrue(von)
        jonathan = Player.objects.get(name='jonathan store haj')
        self.assertTrue(jonathan)


class TestTruncate(TestCase):
    def test_objects_get_removed_after_truncate_command(self):
        attacker = Player(name='AttackerTest')
        attacker.save()
        self.assertEqual(Player.objects.all().count(), 1)
        victim = Player(name='VictimTest')
        victim.save()
        self.assertEqual(Player.objects.all().count(), 2)
        game = Game(id=10, fraglimit=50)
        game.save()
        self.assertEqual(Game.objects.all().count(), 1)
        frag = Frag(attacker=attacker, victim=victim, game=game, weapon='MOD_SHOTGUN')
        frag.save()
        self.assertEqual(Frag.objects.all().count(), 1)
        score = Scoreboard(player=attacker, score=12, game=game)
        score.save()
        self.assertEqual(Scoreboard.objects.all().count(), 1)
        call_command('truncate')
        self.assertEqual(Frag.objects.all().count(), 0)
        self.assertEqual(Player.objects.all().count(), 0)
        self.assertEqual(Scoreboard.objects.all().count(), 0)
        self.assertEqual(Game.objects.all().count(), 0)


class TestScoreboardView(TestCase):
    def test_scoreboard_returns_status_success_with_empty_database(self):
        response = self.client.get('/scoreboard.json')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "\"status\": \"success\"")

    def test_root_url_renders_stats_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'stats.html')


class TestParserIgnoresIllegalNames(TestCase):
    def setUp(self):
        args = ['testcases/ignore_illegal_names.txt', '--test']
        call_command('parse', *args)

    def test_ignore_illegal_names(self):
            # Kill: 11 12 1: jonathan store haj killed Memex killed by MOD_SHOTGUN
            memex = Player.objects.filter(name__contains='Memex').first()
            self.assertIsNone(memex)