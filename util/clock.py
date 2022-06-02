# import exchange_calendars as xcal
#
# xnasdaq = xcals.get_calendar("NASDAQ")
# date_today = pd.DatetimeIndex([datetime.utcnow()]).tz_localize("UTC").tz_convert("US/Eastern")[0].date()
# nasdaq_sessions = xnasdaq.sessions_in_range(
#     date_today + timedelta(days=-252),
#     date_today + timedelta(days=1)).tz_localize(None).date
# nasdaq_sessions_list = list(
#     map(str, nasdaq_sessions))
# today_di = nasdaq_sessions_list.index(str(date_today))
# self.today_str = nasdaq_sessions_list[today_di]
# self.yesterday_str = nasdaq_sessions_list[today_di - 1]

from datetime import datetime
import exchange_calendars as xcals
import pandas as pd
import numpy as np


def check_lock(f):
    def wrapper(*args):
        if args[0].running:
            return f(*args)
        else:
            return None

    return wrapper


class Clock:
    def __init__(self):
        self.running = True
        self.calendar = {
            "nasdaq": xcals.get_calendar("NASDAQ", side="left")
        }
        assert (xcals.__version__ == '3.6.3')

    def tick(self):
        if self.running:
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

            xnasdaq = self.calendar["nasdaq"]
            sesson_minutes = datetime.strftime(self.time_UTC, "%Y-%m-%d %H:%M")
            self.is_trading = xnasdaq.is_trading_minute(sesson_minutes)
            self.time_to_open = (xnasdaq.next_open(self.datestr_UTC_) - self.time_UTC).total_seconds()
            self.time_to_close = (xnasdaq.next_close(self.datestr_UTC_) - self.time_UTC).total_seconds()
            self.time_after_open = (self.time_UTC - xnasdaq.previous_open(self.datestr_UTC_)).total_seconds()
            self.time_after_close = (self.time_UTC - xnasdaq.previous_close(self.datestr_UTC_)).total_seconds()

    @check_lock
    def main_session(self):
        return self.is_trading

    @check_lock
    def session_progress(self):
        if self.is_trading:
            return self.time_after_open / (self.time_after_open + self.time_to_close)
        else:
            return np.nan

    @check_lock
    def session(self):
        if not self.is_trading:
            if self.time_to_open < 3600:
                return "pre"
            elif self.time_after_close < 3600:
                return "after"
            else:
                return "closed"
        else:
            if self.time_after_open < 3600:
                return "opening"
            elif self.time_to_close < 3600:
                return "closing"
            else:
                return "open"
