from pandas.api.types import is_numeric_dtype, is_string_dtype
from pandas.api.types import is_datetime64_any_dtype as is_datetime
from dateutil.parser import parse


# HELP FUNCTIONS
def is_numeric_column(df, column):
    return is_numeric_dtype(df[column]) or any(str(value).isnumeric() for value in df[column])


def is_repeatable_column(df, column):
    grouped_vales = df[column].value_counts()
    if any(value > 1 for value in grouped_vales):
        return True
    return False


def has_numbers(input_string):
    return any(char.isdigit() for char in str(input_string))


def is_string_column(df, column):
    return is_string_dtype(df[column])


def has_multiple_values(df, column):
    grouped_vales = df[column].value_counts()
    if len(grouped_vales) > 1:
        return True
    return False


def is_pure_string_column(df, column):
    if is_string_column(df, column):
        if any(has_numbers(value) for value in list(df[column])):
            return False
        else:
            return True
    else:
        return False


def is_date(string, fuzzy=False):
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False


def is_date_column(df, column):
    date_columns = []
    if is_datetime(df[column]):
        date_columns.append(column)
    elif not is_numeric_column(df, column):
        if any(is_date(str(value)) for value in df[column]):
            date_columns.append(column)
    return date_columns


# SELECTION FUNCTIONS

def get_case_id_columns(df):
    case_id_columns = []
    for column in df.columns:
        if is_numeric_column(df, column) and is_repeatable_column(df, column):
            case_id_columns.append(column)
    return case_id_columns


def get_activity_columns(df):
    activity_columns = []
    for column in df.columns:
        if is_pure_string_column(df, column) and is_repeatable_column(df, column) and has_multiple_values(df, column):
            activity_columns.append(column)
    return activity_columns


def get_date_columns(df):
    date_columns = []
    for column in df.columns:
        if is_date_column(df, column):
            date_columns.append(column)
    return date_columns
