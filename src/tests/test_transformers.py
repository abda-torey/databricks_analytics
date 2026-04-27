# src/tests/test_transformers.py
import pytest
from src.common.transformers import (
    sanitise_string,
    sanitise_country_code,
    parse_iso_timestamp,
    is_valid_event_type,
    calculate_cart_abandonment_rate,
    calculate_conversion_rate,
    mask_user_id,
)
from datetime import datetime


class TestSanitiseString:
    def test_strips_and_lowercases(self):
        assert sanitise_string("  Chrome  ") == "chrome"

    def test_none_returns_none(self):
        assert sanitise_string(None) is None

    def test_empty_returns_none(self):
        assert sanitise_string("   ") is None

    def test_already_clean(self):
        assert sanitise_string("desktop") == "desktop"

    def test_mixed_case(self):
        assert sanitise_string("MOBILE") == "mobile"

    def test_single_space(self):
        assert sanitise_string(" ") is None


class TestSanitiseCountryCode:
    def test_lowercase_becomes_upper(self):
        assert sanitise_country_code("gb") == "GB"

    def test_already_valid(self):
        assert sanitise_country_code("US") == "US"

    def test_numeric_returns_none(self):
        assert sanitise_country_code("123") is None

    def test_three_letters_returns_none(self):
        assert sanitise_country_code("GBR") is None

    def test_none_returns_none(self):
        assert sanitise_country_code(None) is None

    def test_strips_whitespace(self):
        assert sanitise_country_code("  ie  ") == "IE"

    def test_single_letter_returns_none(self):
        assert sanitise_country_code("G") is None


class TestParseIsoTimestamp:
    def test_standard_z_format(self):
        result = parse_iso_timestamp("2024-01-15T10:30:00Z")
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_microseconds_format(self):
        result = parse_iso_timestamp("2024-01-15T10:30:00.123456Z")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1

    def test_no_z_format(self):
        result = parse_iso_timestamp("2024-01-15T10:30:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_invalid_returns_none(self):
        assert parse_iso_timestamp("not-a-date") is None

    def test_none_returns_none(self):
        assert parse_iso_timestamp(None) is None

    def test_empty_returns_none(self):
        assert parse_iso_timestamp("") is None


class TestIsValidEventType:
    @pytest.mark.parametrize("event_type", [
        "page_view",
        "product_view",
        "add_to_cart",
        "remove_from_cart",
        "checkout_start",
        "purchase",
        "search",
    ])
    def test_all_valid_types(self, event_type):
        assert is_valid_event_type(event_type) is True

    def test_unknown_is_invalid(self):
        assert is_valid_event_type("clicked_button") is False

    def test_none_is_invalid(self):
        assert is_valid_event_type(None) is False

    def test_empty_is_invalid(self):
        assert is_valid_event_type("") is False

    def test_uppercase_is_invalid(self):
        assert is_valid_event_type("PURCHASE") is False


class TestCalculateCartAbandonmentRate:
    def test_normal(self):
        assert calculate_cart_abandonment_rate(100, 25) == 75.0

    def test_zero_abandonment(self):
        assert calculate_cart_abandonment_rate(100, 100) == 0.0

    def test_full_abandonment(self):
        assert calculate_cart_abandonment_rate(100, 0) == 100.0

    def test_zero_cart_returns_none(self):
        assert calculate_cart_abandonment_rate(0, 0) is None

    def test_rounding(self):
        assert calculate_cart_abandonment_rate(3, 1) == 66.67

    def test_single_cart_single_purchase(self):
        assert calculate_cart_abandonment_rate(1, 1) == 0.0


class TestCalculateConversionRate:
    def test_normal(self):
        assert calculate_conversion_rate(1000, 35) == 3.5

    def test_zero_sessions_returns_none(self):
        assert calculate_conversion_rate(0, 0) is None

    def test_full_conversion(self):
        assert calculate_conversion_rate(100, 100) == 100.0

    def test_rounding(self):
        assert calculate_conversion_rate(3, 1) == 33.33

    def test_zero_purchases(self):
        assert calculate_conversion_rate(100, 0) == 0.0


class TestMaskUserId:
    def test_masks_long_id(self):
        result = mask_user_id("U1234")
        assert result.startswith("U1")
        assert "*" in result
        assert len(result) == len("U1234")

    def test_short_id_unchanged(self):
        assert mask_user_id("U9") == "U9"

    def test_single_char_unchanged(self):
        assert mask_user_id("U") == "U"

    def test_none_returns_none(self):
        assert mask_user_id(None) is None

    def test_length_preserved(self):
        original = "U9876543"
        result = mask_user_id(original)
        assert len(result) == len(original)

    def test_first_two_chars_preserved(self):
        result = mask_user_id("AB1234")
        assert result[:2] == "AB"
