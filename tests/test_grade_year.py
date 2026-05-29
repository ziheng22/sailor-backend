from app.utils.grade_year import member_list_sort_key, parse_grade_year


def test_parse_grade_year():
    assert parse_grade_year("2024 级") == 2024
    assert parse_grade_year("2020 届") == 2020
    assert parse_grade_year("2023届") == 2023
    assert parse_grade_year("管理员") is None
    assert parse_grade_year("") is None


def test_member_list_sort_key_ascending():
    keys = [
        member_list_sort_key("2024 级", 0, 3),
        member_list_sort_key("2020 届", 0, 1),
        member_list_sort_key("2023届", 0, 2),
    ]
    assert sorted(keys) == keys
