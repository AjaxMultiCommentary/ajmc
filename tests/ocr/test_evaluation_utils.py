import ajmc.ocr.utils
from ajmc.ocr.evaluation import utils

def test_count_chars_by_charset():
    string = 'abdεθ-:123ξ,'
    assert ajmc.ocr.utils.count_chars_by_charset(string, 'latin') == 3
    assert ajmc.ocr.utils.count_chars_by_charset(string, 'greek') == 3
    assert ajmc.ocr.utils.count_chars_by_charset(string, 'numbers') == 3
    assert ajmc.ocr.utils.count_chars_by_charset(string, 'punctuation') == 3


def test_count_errors_by_charset():
    gt_string = 'abdεθ-:123ξ,'
    ts_string = 'aaedεx-x1x3ξ,'
    assert utils.count_errors_by_charset(gt_string, ts_string, 'latin') == 2
    assert utils.count_errors_by_charset(gt_string, ts_string, 'greek') == 1
    assert utils.count_errors_by_charset(gt_string, ts_string, 'numbers') == 1
    assert utils.count_errors_by_charset(gt_string, ts_string, 'punctuation') == 1

