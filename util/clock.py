import exchange_calendars as xcal

import asyncio
from datetime import datetime
import exchange_calendars as xcals
import pandas as pd


def check_lock(f):
    def wrapper(*args):
        if args[0].running:
            return f(*args)
        else:
            return None

    return wrapper


class Clock:
    def __init__(self):
        self.running = False
        self.calendar = {
            "nasdaq": xcals.get_calendar("NASDAQ")
        }

    async def tick(self):
        while self.running:
            self.time = datetime.utcnow()
            self.time_UTC = pd.to_datetime(self.time).tz_localize("UTC")
            self.time_NY = self.time_UTC.tz_convert("US/Eastern")
            self.datestr_UTC = datetime.strftime(self.time_UTC, "%Y%m%d")
            self.datestr_UTC_ = datetime.strftime(self.time_UTC, "%Y-%m-%d")
            self.datestr_NY = datetime.strftime(self.time_NY, "%Y%m%d")
            self.datestr_NY_ = datetime.strftime(self.time_NY, "%Y-%m-%d")
            self.timestr_UTC = datetime.strftime(self.time_UTC, "%H%M%S")
            self.timestr_UTC_ = datetime.strftime(self.time_UTC, "%H:%M:%S")
            self.timestr_NY = datetime.strftime(self.time_NY, "%H%M%S")
            self.timestr_NY_ = datetime.strftime(self.time_NY, "%H:%M:%S")
            sesson_minutes = self.session_minutes(self.datestr_NY_)
            self._main_session = self.calendar["nasdaq"].is_trading_minute(
                self.datestr_UTC + " " + self.timestr_UTC[:5])
            # xhkg.session_minutes("2021-01-04")
            asyncio.sleep(1)

    def start(self):
        self.running = True
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.tick())
        self.running = False

    @check_lock
    def main_session(self):
        return self._main_session

    @check_lock
    def hour_until_close(self):
        seconds_until_close = (self.calendar["nasdaq"].next_close(
            self.datestr_UTC + " " + self.timestr_UTC[:5]) - self.time_UTC).seconds
        return seconds_until_close / 3600
