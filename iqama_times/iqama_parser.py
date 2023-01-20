import requests
import pandas as pd
from datetime import time

pd.options.mode.chained_assignment = None  # default='warn'

class buildIqamaSchedule: 
    def __init__(
        self,
        address: str, 
        year: int,
        fajr_delay: int,
        asr_delay: int, 
        dahur_time: str = "1:30",
        maghrib_delay: int = 10, 
        isha_delay: int = 10, 
        maghrib_ramzan_delay: int = 15, 
        method: int = 2,
        min_fajar_time: str = "5:00",
        max_isha_time: str = "9:30",
        ramzan_start: str = None, 
        ramzan_end: str = None,
    ): 
        self.address = address
        self.year = year
        # Add pydantic validation for method
        
        self.method = method
        self.fajr_delay = fajr_delay
        self.dahur_time = dahur_time
        self.asr_delay = asr_delay
        self.maghrib_delay = maghrib_delay
        self.isha_delay = isha_delay
        self.ramzan_start = ramzan_start
        self.ramzan_end = ramzan_end
        self.maghrib_ramzan_delay = maghrib_ramzan_delay
        self.min_fajar_time = min_fajar_time
        self.max_isha_time = max_isha_time
        self.prayer_cols = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

        
    def get_adhan_times(self) -> requests.Response:
        """Pulls Adhan times from the calendarByAddress api endpoint

        Args:
            address (str): US address for place to generate adhan times
            year (int): Year to generate adhan times
            method (int): Method of selection see: https://aladhan.com/calculation-methods

        """
        url = "http://api.aladhan.com/v1/calendarByAddress"
        filters = {
            "address": self.address,
            "iso8601": "true",
            "annual": "true",
            "year": self.year,
            "method": self.method,
        }
        return requests.get(url=url, params=filters)


    def build_adhan_df(self, adhan_resp: dict) -> pd.DataFrame:
        """Converts the adhan json response to a Pandas DataFrame object

        Args:
            adhan_resp (dict): Response from the  "http://api.aladhan.com/v1/calendarByAddress" endpoint

        Returns:
            pd.DataFrame: Response converted to a dataframe
        """
        mapping = {
            "timings.Fajr": "Fajr",
            "timings.Dhuhr": "Dhuhr",
            "timings.Asr": "Asr",
            "timings.Maghrib": "Maghrib",
            "timings.Isha": "Isha",
            "date.readable": "Date",
        }
        cols = [
            "date.readable",
            "timings.Fajr",
            "timings.Dhuhr",
            "timings.Asr",
            "timings.Maghrib",
            "timings.Isha",
            "date.gregorian.date",
        ]
        df_list = []
        for month in adhan_resp["data"].keys():
            df = pd.DataFrame(pd.json_normalize(adhan_resp["data"][str(month)]))
            # filters for only columns we care about and renames
            df = df[cols].rename(columns=mapping)
            df_list.append(df)
        df = pd.concat(df_list)
        df[self.prayer_cols] = df[self.prayer_cols].apply(pd.to_datetime)
        return df

    @staticmethod
    def parse_date_time(time_string: str) -> list:  
        """Extracts hour and minute from time formatted as hh:mm """
        return time_string.split(sep=":") 
    
    def update_fajr(self, fajr: pd.Series) -> pd.Series:
        """Updates fajar time based on certain parameters
        Args:
            fajr (pd.Series): Pandas series containing fajar datetime stamps

        Returns:
            pd.Series: Updates Fajr columns based on user inputs
        """
        time_split = parse_date_time(self.min_fajar_time)
        #applies minimum time for fajar
        fajr.loc[fajr.dt.time < time(time_split[0], time_split[1])] = fajr.loc[fajr.dt.time < time(time_split[0], time_split[1])].apply(
            lambda x: x.replace(hour=time_split[0], minute=time_split[1])
        )
        fajr = fajr + pd.Timedelta(minutes=self.fajr_delay)
        fajr = fajr.dt.ceil(freq="15T")
        fajr = pd.to_datetime(fajr, format="%H:%M").dt.time
        return fajr


    def update_dahur(dahur: pd.Series) -> pd.Series:
        dahur.loc[dahur.dt.time < time(5, 00)] = dahur.loc[dahur.dt.time < time(5, 00)].apply(
            lambda x: x.replace(hour=5, minute=0)
        )
        dahur = dahur + pd.Timedelta(minutes=self.dahur_delay)
        dahur = dahur.dt.ceil(freq="15T")
        dahur = pd.to_datetime(dahur, format="%H:%M").dt.time
        pass


    def update_maghrib(maghrib: pd.Series) -> pd.Series:
        pass


    def update_isha(isha: pd.Series) -> pd.Series:
        pass


    def execute(self): 
        resp = self.get_adhan_times()
        if resp.status_code == 200: 
            df = self.build_adhan_df(resp.json())
            df["Fajr_iqama"] = update_fajr(df["Fajr"])
            df["Dahur_iqama"] = update_dahur(df["Dahur"])
            df["Asr_iqama"] = update_fajr(df["Asr"])
            df["Maghrib_iqama"] = update_dahur(df["Maghrib"])
            df["Isha_iqama"] = update_dahur(df["Isha"])
