import unittest
import sys
import os

from utils.text_utils import merge_descriptions, _serialize_unknown_type


class TestTextUtils(unittest.TestCase):
    
    def test_merge_descriptions_both_empty(self):
        """Test merge_descriptions with both descriptions empty."""
        result = merge_descriptions("", "")
        self.assertEqual(result, "")
    
    def test_merge_descriptions_old_empty(self):
        """Test merge_descriptions with old description empty."""
        result = merge_descriptions("", "New description")
        self.assertEqual(result, "New description")
    
    def test_merge_descriptions_new_empty(self):
        """Test merge_descriptions with new description empty."""
        result = merge_descriptions("Old description", "")
        self.assertEqual(result, "Old description")
    
    def test_merge_descriptions_both_populated(self):
        """Test merge_descriptions with both descriptions populated."""
        result = merge_descriptions("Old description", "New description")
        self.assertEqual(result, "Old description\n\n---\nNew description")
    
    def test_merge_descriptions_with_whitespace(self):
        """Test merge_descriptions with whitespace in descriptions."""
        result = merge_descriptions("  Old description  ", "  New description  ")
        self.assertEqual(result, "Old description\n\n---\nNew description")
    
    def test_serialize_unknown_type(self):
        """Test _serialize_unknown_type with different objects."""
        self.assertEqual(_serialize_unknown_type(None), "None")
        self.assertEqual(_serialize_unknown_type(123), "123")
        self.assertEqual(_serialize_unknown_type("test"), "test")
        self.assertEqual(_serialize_unknown_type([1, 2, 3]), "[1, 2, 3]")
        self.assertEqual(_serialize_unknown_type({"a": 1}), "{'a': 1}")


if __name__ == '__main__':
    unittest.main()