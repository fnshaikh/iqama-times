import requests
import pandas as pd
from datetime import time

pd.options.mode.chained_assignment = None  # default='warn'

class BuildIqamaSchedule: 
    def __init__(
        self,
        address: str, 
        year: int,
        fajr_delay: int,
        asr_delay: int, 
        dhuhr_time: str = "1:30",
        maghrib_delay: int = 10, 
        isha_delay: int = 10, 
        maghrib_ramzan_delay: int = 15, 
        method: int = 2,
        min_fajar_time: str = "5:00",
        min_isha_time = str = "8:15",
        max_isha_time: str = "9:30",
        ramzan_start: str = None, 
        ramzan_end: str = None,
    ): 
        self.address = address
        self.year = year
        # Add pydantic validation for method
        
        self.method = method
        self.fajr_delay = fajr_delay
        self.dhuhr_time = dhuhr_time
        self.asr_delay = asr_delay
        self.maghrib_delay = maghrib_delay
        self.isha_delay = isha_delay
        self.ramzan_start = ramzan_start
        self.ramzan_end = ramzan_end
        self.maghrib_ramzan_delay = maghrib_ramzan_delay
        self.min_fajar_time = min_fajar_time
        self.min_isha_time = min_isha_time
        self.max_isha_time = max_isha_time
        self.prayer_cols = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

        
    def get_adhan_times(self) -> requests.Response:
        """Pulls Adhan times from the calendarByAddress api endpoint

        Args:
            address (str): US address for place to generate adhan times
            year (int): Year to generate adhan times
            method (int): Method of selection see: https://aladhan.com/calculation-methods

        Returns: 
            requests.Response: response from api call as a Response object
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
    def parse_date_time(time_string: str) -> tuple:  
        """Extracts hour and minute from time formatted as hh:mm """
        split = time_string.split(sep=":") 
        return (int(split[0]), int(split[1]))
    
    def update_fajr(self, fajr: pd.Series) -> pd.Series:
        """Updates Fajr time based on certain parameters

        Args:
            fajr (pd.Series): Pandas series containing Fajr datetime stamps

        Returns:
            pd.Series: Updates Fajr columns based on user inputs
        """
        time_split = BuildIqamaSchedule.parse_date_time(self.min_fajar_time)
        #applies minimum time for fajar
        mask = fajr.dt.time < time(time_split[0], time_split[1])
        fajr.loc[mask] = fajr.loc[mask].apply(
            lambda x: x.replace(hour=time_split[0], minute=time_split[1])
        )
        fajr = fajr + pd.Timedelta(minutes=self.fajr_delay)
        fajr = fajr.dt.ceil(freq="15T")
        fajr = pd.to_datetime(fajr, format="%H:%M").dt.time
        return fajr


    def update_dhuhr(self, dhuhr: pd.Series) -> pd.Series:
        """ Updates dhuhr prayer time based on user specification

        Args:
            dhuhr (pd.Series): Pandas series containing dhuhr datetime stamps

        Returns:
            pd.Series: Updates dhuhr columns based on user inputs
        """
        time_split = BuildIqamaSchedule.parse_date_time(self.dhuhr_time)
        dhuhr = dhuhr.apply(lambda x: x.replace(hour=time_split[0], minute=time_split[1]))
        dhuhr = pd.to_datetime(dhuhr, format="%H:%M").dt.time
        return dhuhr
    
    def update_asr(self, asr: pd.Series) -> pd.Series:
        """ Updates dhuhr prayer time based on user specification

        Args:
            dhuhr (pd.Series): Pandas series containing dhuhr datetime stamps

        Returns:
            pd.Series: Updates dhuhr columns based on user inputs
        """
        asr = asr + pd.Timedelta(minutes=self.asr_delay)
        asr = asr.dt.ceil(freq="15T")
        asr = pd.to_datetime(asr, format="%H:%M").dt.time
        return dhuhr
    
    def update_maghrib(self, maghrib: pd.Series) -> pd.Series:
        """ Updates maghrib prayer time based on user specification

        Args:
            dhuhr (pd.Series): Pandas series containing maghrib datetime stamps

        Returns:
            pd.Series: Updates maghrib columns based on user inputs
        
        Notes: 
            - Uses ramzan start and end to update based on those specifications
        """
        mask = (maghrib > self.ramzan_start) & (maghrib <= self.ramzan_end)
        maghrib.loc[mask] = maghrib.loc[mask] + pd.Timedelta(minutes=self.maghrib_ramzan_delay)
        maghrib.loc[~mask] = maghrib.loc[~mask] + pd.Timedelta(minutes=self.maghrib_delay)
        #maghrib = maghrib.dt.ceil(freq="15T")
        maghrib = pd.to_datetime(maghrib, format="%H:%M").dt.time
        return maghrib
        
    def update_isha(isha: pd.Series) -> pd.Series:
        pass


    def execute(self): 
        resp = self.get_adhan_times()
        if resp.status_code == 200: 
            df = self.build_adhan_df(resp.json())
            df["Fajr_iqama"] = update_fajr(df["Fajr"])
            df["Dhuhr_iqama"] = update_dhuhr(df["Dhuhr"])
            df["Asr_iqama"] = update_fajr(df["Asr"])
            df["Maghrib_iqama"] = update_maghrib(df["Maghrib"])
            df["Isha_iqama"] = update_isha(df["Isha"])
