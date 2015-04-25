from django.core.management.base import BaseCommand
from stats.management.commands.parse import Database


class Command(BaseCommand):
    help = 'Truncate the relevant tables'

    def handle(self, *args, **options):
        database = Database()
        database.truncate()