from aiodesa.utils.types import IsDataclass
from typing import List, Tuple


def get_field_names(data_cls: IsDataclass) -> List[str]:
    """
    Get a list of field names from a data class.

    Parameters:
    - data_cls (IsDataclass): The data class.

    Returns:
    - List[str]: A list of field names.
    """
    return [field for field in data_cls.__annotations__ if field != "table_name"]


def get_field_values(data_cls: IsDataclass, field_names: List[str]) -> List:
    """
    Get the values of specified fields from a data class instance.

    Parameters:
    - data_cls (IsDataclass): The data class instance.
    - field_names (List[str]): List of field names.

    Returns:
    - List: A list of field values.
    """
    data_dict = data_cls
    return [data_dict[field] for field in field_names if data_dict[field] is not None]


def get_non_none_columns(field_names: List[str], values: List) -> List[Tuple[str, ...]]:
    """
    Get a list of non-None columns and their corresponding values.

    Parameters:
    - field_names (List[str]): List of field names.
    - values (List): List of field values.

    Returns:
    - List[Tuple[str, ...]]: A list of tuples representing non-None columns and values.
    """
    return [
        (field, value) for field, value in zip(field_names, values) if value is not None
    ]
