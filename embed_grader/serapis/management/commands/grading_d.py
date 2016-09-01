from django.core.management.base import BaseCommand

from serapis.models import *
import requests

class Command(BaseCommand):
    help = 'Daemon of sending grading tasks to backend'

    def handle(self, *args, **options):
        files = {'firmware': ('filename', open('/Users/timestring/Desktop/mbed_blinky_11u24_LPC11U24.bin', 'rb'), 'text/plain')}
        r = requests.post('http://172.17.5.253:8889/dut/program/', data={'dut':1}, files=files)
