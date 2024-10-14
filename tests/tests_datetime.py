import unittest
from pyshellscript import *
from datetime import datetime, date, time
from typing import Union, List, Optional


class TestDatetimeFormatting(unittest.TestCase):
    """
    Unit tests for datetime formatting functions.
    """

    def setUp(self):
        """
        Sets up example datetime and date objects for testing.
        """
        # Example datetime and date objects for testing
        self.example_datetime = datetime(2024, 10, 14, 12, 30, 45)
        self.example_date = date(2024, 10, 14)

    def test_datetime_to_yyyy_mm_dd_hh_mm_ss(self):
        """
        Tests the datetime_to_yyyy_mm_dd_hh_mm_ss function with both datetime and date inputs.
        """
        # Test with full datetime object
        formatted = datetime_to_yyyy_mm_dd_hh_mm_ss(self.example_datetime)
        self.assertEqual(formatted, '2024-10-14 12:30:45')

        # Test with date object (without time)
        formatted = datetime_to_yyyy_mm_dd_hh_mm_ss(self.example_date)
        self.assertEqual(formatted, '2024-10-14 00:00:00')

    def test_datetime_to_yyyy_mm_dd_hh_mm(self):
        """
        Tests the datetime_to_yyyy_mm_dd_hh_mm function with both datetime and date inputs.
        """
        # Test with full datetime object
        formatted = datetime_to_yyyy_mm_dd_hh_mm(self.example_datetime)
        self.assertEqual(formatted, '2024-10-14 12:30')

        # Test with date object (without time)
        formatted = datetime_to_yyyy_mm_dd_hh_mm(self.example_date)
        self.assertEqual(formatted, '2024-10-14 00:00')

    def test_custom_delimiters(self):
        """
        Tests the functions with custom delimiters for both date and time.
        """
        # Test with custom delimiters for datetime_to_yyyy_mm_dd_hh_mm_ss
        formatted = datetime_to_yyyy_mm_dd_hh_mm_ss(self.example_datetime, delimiter_date='/', delimiter_time='.')
        self.assertEqual(formatted, '2024/10/14 12.30.45')

        # Test with custom delimiters for datetime_to_yyyy_mm_dd_hh_mm
        formatted = datetime_to_yyyy_mm_dd_hh_mm(self.example_datetime, delimiter_date='.', delimiter_time='-')
        self.assertEqual(formatted, '2024.10.14 12-30')

    def test_single_delimiter(self):
        """
        Tests the functions with a single delimiter for both date and time.
        """
        # Test with single delimiter for datetime_to_yyyy_mm_dd_hh_mm_ss
        formatted = datetime_to_yyyy_mm_dd_hh_mm_ss(self.example_datetime, delimiter='.')
        self.assertEqual(formatted, '2024.10.14 12.30.45')

        # Test with single delimiter for datetime_to_yyyy_mm_dd_hh_mm
        formatted = datetime_to_yyyy_mm_dd_hh_mm(self.example_datetime, delimiter='/')
        self.assertEqual(formatted, '2024/10/14 12/30')


class TestDatetimeParse(unittest.TestCase):
    """ `datetime_parse(...)` """

    def test_basic_usage(self):
        # Examples from the documentation
        self.assertEqual(
            datetime_parse("2022-12-31 23:59:01"),
            datetime(2022, 12, 31, 23, 59, 1)
        )

        self.assertEqual(
            datetime_parse("2022/12/31_23-02", delimiter_date='/', delimiter_time='-'),
            datetime(2022, 12, 31, 23, 2)
        )

        self.assertIsNone(
            datetime_parse("Log at 2022-12-31 23:03", require_start=True)
        )

        self.assertIsNone(
            datetime_parse("2022-12-31 23:04 Log", require_end=True)
        )

        self.assertEqual(
            datetime_parse("20221231T235905", delimiter_date_time='T', iso_basic=True),
            datetime(2022, 12, 31, 23, 59, 5)
        )

        self.assertIsNone(
            datetime_parse("Invalid date", raise_exception=False)
        )

        with self.assertRaises(ValueError):
            datetime_parse("Invalid date", raise_exception=True)

    def test_various_formats(self):
        # Testing different date formats from datetime_regexes
        # Format: YYYY-MM-DD_HH:MM[:SS]
        self.assertEqual(
            datetime_parse("2022-12-31 23:59:59"),
            datetime(2022, 12, 31, 23, 59, 59)
        )

        self.assertEqual(
            datetime_parse("2022-12-31 23:59"),
            datetime(2022, 12, 31, 23, 59)
        )

        # Format: YY-MM-DD_HH:MM[:SS]
        self.assertEqual(
            datetime_parse("22-12-31 23:59:59"),
            datetime(2022, 12, 31, 23, 59, 59)
        )

        # Format: DD-MM-YYYY_HH:MM[:SS]
        self.assertEqual(
            datetime_parse("31-12-2022 23:59:59"),
            datetime(2022, 12, 31, 23, 59, 59)
        )

        # Format: YYYY-MM-DD (date only)
        self.assertEqual(
            datetime_parse("2022-12-31", no_time=True),
            datetime(2022, 12, 31)
        )

        # Format: YYYYMMDD_HHMMSS
        self.assertEqual(
            datetime_parse("20221231 235959", delimiter_date_time=' ', iso_basic=True),
            datetime(2022, 12, 31, 23, 59, 59)
        )

        # Format: YYYYMMDD_HHMM
        self.assertEqual(
            datetime_parse("20221231 2359", delimiter_date_time=' '),
            datetime(2022, 12, 31, 23, 59)
        )

        # Format: YYYYMMDD (date only)
        self.assertEqual(
            datetime_parse("20221231", no_time=True),
            datetime(2022, 12, 31)
        )

    def test_invalid_numbers(self):
        # Invalid months
        self.assertIsNone(
            datetime_parse("2022-13-31 23:59:59", raise_exception=False)
        )

        with self.assertRaises(ValueError):
            datetime_parse("2022-13-31 23:59:59", raise_exception=True)

        # Invalid days
        self.assertIsNone(
            datetime_parse("2022-12-32 23:59:59", raise_exception=False)
        )

        with self.assertRaises(ValueError):
            datetime_parse("2022-12-32 23:59:59", raise_exception=True)

        # Invalid hours
        self.assertIsNone(
            datetime_parse("2022-12-31 24:00:00", raise_exception=False)
        )

        with self.assertRaises(ValueError):
            datetime_parse("2022-12-31 24:00:00", raise_exception=True)

        # Invalid minutes
        self.assertIsNone(
            datetime_parse("2022-12-31 23:60:00", raise_exception=False)
        )

        with self.assertRaises(ValueError):
            datetime_parse("2022-12-31 23:60:00", raise_exception=True)

        # Invalid seconds
        self.assertIsNone(
            datetime_parse("2022-12-31 23:59:60", raise_exception=False)
        )

        with self.assertRaises(ValueError):
            datetime_parse("2022-12-31 23:59:60", raise_exception=True)

    def test_edge_cases(self):
        # Leap year
        self.assertEqual(
            datetime_parse("2020-02-29 12:00:01"),
            datetime(2020, 2, 29, 12, 0, 1)
        )

        # Non-leap year (February 29th should be invalid)
        self.assertIsNone(
            datetime_parse("2019-02-29 12:00:02", raise_exception=False)
        )

        with self.assertRaises(ValueError):
            datetime_parse("2019-02-29 12:00:03", raise_exception=True)

        # Different delimiters
        self.assertEqual(
            datetime_parse("2022/12/31T23-59-04", delimiter_date='/', delimiter_time='-', delimiter_date_time='T'),
            datetime(2022, 12, 31, 23, 59, 4)
        )

        # Date at the start of the string
        self.assertEqual(
            datetime_parse("2022-12-31 data", require_start=True, no_time=True),
            datetime(2022, 12, 31)
        )

        # Date at the end of the string
        self.assertEqual(
            datetime_parse("data 2022-12-31", require_end=True, no_time=True),
            datetime(2022, 12, 31)
        )

        # Date in the middle of the string
        self.assertIsNone(
            datetime_parse("data 2022-12-31 data", require_start=True, require_end=True, no_time=True)
        )

        # Two-digit year with rollover
        self.assertEqual(
            datetime_parse("99-12-31 23:59:59"),
            datetime(2099, 12, 31, 23, 59, 59)
        )

        # Testing iso and iso_basic flags
        self.assertEqual(
            datetime_parse("2022-12-31 23:59:59", iso=True),
            datetime(2022, 12, 31, 23, 59, 59)
        )

        self.assertIsNone(
            datetime_parse("20221231 235959", iso=True)
        )

        self.assertEqual(
            datetime_parse("20221231 235959", iso_basic=True, delimiter_date_time=' '),
            datetime(2022, 12, 31, 23, 59, 59)
        )

        self.assertIsNone(
            datetime_parse("2022-12-31 23:59:59", iso_basic=True)
        )

        # Custom require_start and require_end patterns
        self.assertEqual(
            datetime_parse("Start2022-12-31End", require_start='Start', require_end='End', no_time=True),
            datetime(2022, 12, 31)
        )

        # Invalid custom require_start and require_end patterns
        self.assertIsNone(
            datetime_parse("Start2022-12-31", require_start='Start', require_end='End', no_time=True)
        )

        # Using multiple delimiters
        self.assertEqual(
            datetime_parse("2022.12.31-23:59:59", delimiter_date=['-', '.', '/'], delimiter_date_time='-', delimiter_time=':'),
            datetime(2022, 12, 31, 23, 59, 59)
        )

        # Missing components
        self.assertIsNone(
            datetime_parse("2022-12-31", iso=True)
        )

        self.assertIsNone(
            datetime_parse("2022-12", iso=True)
        )

    def test_invalid_inputs(self):
        # Empty string
        self.assertIsNone(
            datetime_parse("", raise_exception=False)
        )

        with self.assertRaises(ValueError):
            datetime_parse("", raise_exception=True)

        # None input
        with self.assertRaises(TypeError):
            datetime_parse(None)

        # Invalid type for delimiter_date
        with self.assertRaises(TypeError):
            datetime_parse("2022-12-31", delimiter_date=123, no_time=True)

        # Invalid type for require_start
        with self.assertRaises(TypeError):
            datetime_parse("2022-12-31", require_start=123, no_time=True)

    def test_performance(self):
        # Test with a large number of dates to check performance
        dates = ["2022-12-31 23:59:59"] * 1000
        for date_str in dates:
            self.assertEqual(
                datetime_parse(date_str),
                datetime(2022, 12, 31, 23, 59, 59)
            )

    def test_timezone_ignorance(self):
        # The function should ignore timezones if present
        self.assertEqual(
            datetime_parse("2022-12-31 23:59:59+02:00"),
            datetime(2022, 12, 31, 23, 59, 59)
        )

        self.assertEqual(
            datetime_parse("2022-12-31T23:59:59Z", delimiter_date_time='T'),
            datetime(2022, 12, 31, 23, 59, 59)
        )

    def test_fractional_seconds(self):
        # The function should handle fractional seconds if modified to do so
        # Currently, it should ignore them
        self.assertEqual(
            datetime_parse("2022-12-31 23:59:59.123"),
            datetime(2022, 12, 31, 23, 59, 59)
        )

    def test_non_matching_strings(self):
        # Strings that should not match any date format
        self.assertIsNone(
            datetime_parse("Just some random text")
        )

        self.assertIsNone(
            datetime_parse("1234567890", no_time=True)
        )

        self.assertIsNone(
            datetime_parse("2022/13/31", no_time=True)  # Invalid month
        )

# Run the tests
if __name__ == '__main__':
    unittest.main()
