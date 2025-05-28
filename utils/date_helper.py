import time
import calendar
import pytz
from datetime import datetime, timedelta, timezone

from utils.constants import IND_TIME_ZONE


class DateHelper(object):

    @staticmethod
    def convert_date_to_string(date: object, date_format: object) -> object:
        """
        :param date: Object of class datetime.datetime
        :param date_format: Object of class datetime.datetime
        :return: string
        """
        return datetime.strftime(date, date_format)

    @staticmethod
    def convert_string_to_date(date_str, date_format):
        """
        :param date_str: String eg.
        :param date_format : Format in which the date is to be converted
        :return:
        """
        if isinstance(date_format, list):
            for fmt in date_format:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    pass
            raise ValueError(f"time data {date_str} does not match any format from {date_format}")
        else:
            return datetime.strptime(date_str, date_format)

    @staticmethod
    def change_date_format_in_string(date_str, initial_date_format, req_date_format):
        """
        :param date_str: String date to change.
        :param initial_date_format : Existing date format
        :param req_date_format : Required date format
        :return:
        """
        return datetime.strptime(date_str, initial_date_format).strftime(req_date_format)

    @staticmethod
    def get_current_date():
        """
        :return: Returns the current datetime
        as a python datetime object
        """
        return datetime.now()

    @staticmethod
    def convert_date_to_epoch(date=None):
        """
        Converts a given datetime object to epoch in UTC
        :param date: datetime object
        :return:
        """
        if not date:
            date = DateHelper.get_current_date()

        utc_date = datetime.timetuple(date - timedelta(hours=5, minutes=30))
        return calendar.timegm(utc_date)

    @staticmethod
    def convert_epoch_to_date(epoch):
        utc_time = datetime.fromtimestamp(epoch, tz=timezone.utc)
        local_timezone = pytz.timezone(IND_TIME_ZONE)
        local_time = utc_time.astimezone(local_timezone)
        return local_time

    @staticmethod
    def create_a_slot(date):
        if date.hour % 2 == 0:
            slot_hour = date.hour
        else:
            slot_hour = date.hour - 1

        now = DateHelper.convert_date_to_string(datetime(date.year, date.month, date.day, slot_hour, 0, 0),
                                                '%Y-%m-%d %H:%M:%S')
        india = pytz.timezone('Asia/Kolkata')
        lower_bound = india.localize(datetime.strptime(now, '%Y-%m-%d %H:%M:%S'))
        return lower_bound

    @staticmethod
    def get_ist_now():
        local_tz = pytz.timezone('Asia/Kolkata')

        def utc_to_local(utc_dt):
            local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
            return local_tz.normalize(local_dt)

        return utc_to_local(datetime.now(timezone.utc))

    @staticmethod
    def get_utc_now():
        return datetime.now(timezone.utc)

    @staticmethod
    def convert_to_utc(local_time, local_timezone):
        your_local_timezone = pytz.timezone(local_timezone)
        localized_time = your_local_timezone.localize(local_time)
        utc_timezone = pytz.utc
        utc_time = localized_time.astimezone(utc_timezone)
        return utc_time
