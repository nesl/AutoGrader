import os
import psutil

from django.utils import timezone

from serapis.models import *


class GradingSchedulerHeartbeat():
    """
    `GradingSchedulerHeartbeat` is a helper class that stores a timestamp back to database. This
    class should be used in the following two scenarios: (1) In the case of leaving a heartbeat
    timestamp (usually in the grading scheduler), an object should be instantiated. (2) In the case
    that one in only interested in monitoring grading scheduler status (for example, to show the
    scheduler status on the web interface), the developer should only use the class method but not
    instantiate any objects.
    """

    def __init__(self):
        self.pid = os.getpid()
        self.start_time = timezone.now()

    def send_heartbeat(self):
        GradingSchedulerFootprint.objects.all().delete()
        GradingSchedulerFootprint.objects.create(
            pid=self.pid,
            woke_time=self.start_time,
            watchdog_time=timezone.now(),
        )
        
    @classmethod
    def get_last_heartbeat(cls):
        heartbeats = GradingSchedulerFootprint.objects.all()
        if len(heartbeats) == 0:
            return None
        return heartbeats[0]

    @classmethod
    def detect_if_other_scheduler_exists(cls):
        """
        we claim a second scheduler has existed (because the someone has executed that scheduler
        earlier) if that scheduler has a different PID and that process is still alive.
        """
        heartbeat = cls.get_last_heartbeat()
        if heartbeat is None:
            return False

        # if the caller scheduler (current process) match the PID in the database, then no other
        # scheduler is detected
        if heartbeat.pid == os.getpid():
            return False

        return psutil.pid_exists(heartbeat.pid)
