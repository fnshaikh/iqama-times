from iqama_times.iqama_parser import BuildIqamaSchedule
import pytest

class TestIqamaParser:

    @pytest.fixture
    def api_response(self):
        return {
            "code": 200,
            "status": "OK",
            "data": {
                "1": [
                    {
                        "timings": {
                            "Fajr": "2023-01-01T05:38:00-08:00 (PST)",
                            "Sunrise": "2023-01-01T06:51:00-08:00 (PST)",
                            "Dhuhr": "2023-01-01T11:52:00-08:00 (PST)",
                            "Asr": "2023-01-01T14:35:00-08:00 (PST)",
                            "Sunset": "2023-01-01T16:53:00-08:00 (PST)",
                            "Maghrib": "2023-01-01T16:53:00-08:00 (PST)",
                            "Isha": "2023-01-01T18:06:00-08:00 (PST)",
                            "Imsak": "2023-01-01T05:28:00-08:00 (PST)",
                            "Midnight": "2023-01-01T23:52:00-08:00 (PST)",
                            "Firstthird": "2023-01-01T21:32:00-08:00 (PST)",
                            "Lastthird": "2023-01-01T02:12:00-08:00 (PST)",
                        },
                        "date": {
                            "readable": "01 Jan 2023",
                            "timestamp": "1672592461",
                            "gregorian": {
                                "date": "01-01-2023",
                                "format": "DD-MM-YYYY",
                                "day": "01",
                                "weekday": {"en": "Sunday"},
                                "month": {"number": 1, "en": "January"},
                                "year": "2023",
                                "designation": {
                                    "abbreviated": "AD",
                                    "expanded": "Anno Domini",
                                },
                            },
                        },
                    }
                ]
            },
        }

    @pytest.fixture
    def default_inputs(self):
        return {
            "address": "12622 Springbrook Drive Unit D, San Diego, CA",
            "year": 2023,
            "fajr_delay": 15,
            "asr_delay": 15,
            "dhuhr_time": "1:30",
            "maghrib_delay": 10,
            "isha_delay": 10,
            "maghrib_ramzan_delay": 15,
            "method": 2,
            "min_fajar_time": "5:00",
            "max_isha_time": "9:30",
            "ramzan_start": None,
            "ramzan_end": None,
        }

    @pytest.mark.parametrize(
        "time",
        [
            "11:30",
            "11:30:22",
        ],
    )
    def test_time_parser(self, time: str) -> None:
        split = BuildIqamaSchedule.parse_date_time(time)
        assert split[0] == 11
        assert split[1] == 30
