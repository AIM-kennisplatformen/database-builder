import pytest
from database_builder_libs.stores.typedb._query import (
    _validate_identifier,
    _escape_string,
)


class TestValidateIdentifier:
    def test_valid_identifiers(self):
        assert _validate_identifier("person") == "person"
        assert _validate_identifier("has_name") == "has_name"
        assert _validate_identifier("friendship") == "friendship"
        assert _validate_identifier("_private") == "_private"
        assert _validate_identifier("a") == "a"

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError, match="must be a non-empty string"):
            _validate_identifier("")

    def test_rejects_non_string(self):
        with pytest.raises(ValueError, match="must be a non-empty string"):
            _validate_identifier(None)  # type: ignore

    def test_rejects_leading_digit(self):
        with pytest.raises(ValueError, match="Invalid TypeDB"):
            _validate_identifier("1person")

    def test_rejects_special_characters(self):
        with pytest.raises(ValueError, match="Invalid TypeDB"):
            _validate_identifier("person; delete $x")

    def test_rejects_spaces(self):
        with pytest.raises(ValueError, match="Invalid TypeDB"):
            _validate_identifier("my type")

    def test_rejects_typeql_injection(self):
        with pytest.raises(ValueError, match="Invalid TypeDB"):
            _validate_identifier('entity"; $e isa "')

    def test_custom_label_in_error(self):
        with pytest.raises(ValueError, match="custom thing"):
            _validate_identifier("", "custom thing")


class TestEscapeString:
    def test_plain_string_unchanged(self):
        assert _escape_string("hello") == "hello"

    def test_escapes_double_quote(self):
        assert _escape_string('say "hi"') == 'say \\"hi\\"'

    def test_escapes_backslash(self):
        assert _escape_string("path\\to\\file") == "path\\\\to\\\\file"

    def test_escapes_both_backslash_and_quote(self):
        assert _escape_string('a\\"b') == 'a\\\\\\"b'

    def test_empty_string(self):
        assert _escape_string("") == ""

    def test_unicode_ok(self):
        assert _escape_string("café") == "café"

    def test_rejects_control_characters(self):
        with pytest.raises(ValueError, match="Invalid control character"):
            _escape_string("line\nbreak")

    def test_rejects_null_byte(self):
        with pytest.raises(ValueError, match="Invalid control character"):
            _escape_string("null\x00byte")

    def test_tab_is_allowed(self):
        assert _escape_string("col\tval") == "col\tval"
