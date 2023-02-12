import io
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from app.main.routes_products import (
    MANDATORY_COLUMNS,
    _get_vendor,
    product_columns_to_json,
    products_excel_to_df,
)
from app.models import UserRoles, Vendor


def test_product_columns_to_json():
    row = pd.Series({"column_1": "apple, orange, pear", "column_2": "banana, cherry"})
    expected_result = (
        '{"column_1": ["apple", "orange", "pear"], "column_2": ["banana", "cherry"]}'
    )

    result = product_columns_to_json(row)
    assert result == expected_result, f"Expected {expected_result} but got {result}"

    row = pd.Series({"column_1": "apple, orange, pear", "column_2": None})
    expected_result = '{"column_1": ["apple", "orange", "pear"]}'

    result = product_columns_to_json(row)
    assert result == expected_result, f"Expected {expected_result} but got {result}"

    row = pd.Series({}, dtype=object)
    expected_result = ""

    result = product_columns_to_json(row)
    assert result == expected_result, f"Expected {expected_result} but got {result}"


def test_products_excel_to_df_raises():
    df = pd.DataFrame.from_dict({})
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    with pytest.raises(KeyError):
        products_excel_to_df(buffer, 1, {})


def test_products_excel_to_df():
    source = pd.DataFrame([{x: "1" for x in MANDATORY_COLUMNS}])
    source["category"] = "category"
    source["input_required"] = True
    source["opt1"] = "1,2 ,3"
    source["opt2"] = "qwer, qwer"
    source["opt3"] = "3"
    buffer = io.BytesIO()
    source.to_excel(buffer, index=False)
    buffer.seek(0)
    target = products_excel_to_df(buffer, 1, {"category": 1})
    source["vendor_id"] = 1
    source["cat_id"] = 1
    source["image"] = None
    source["price"] = source["price"].astype(float)
    source["options"] = '{"opt1": ["1", "2", "3"], "opt2": ["qwer"], "opt3": ["3"]}'
    source.drop(["category", "opt1", "opt2", "opt3"], axis=1, inplace=True)
    pd.testing.assert_frame_equal(
        source.sort_index(axis=1), target.sort_index(axis=1), check_names=True
    )


@pytest.fixture
def mock_vendor(monkeypatch):
    vendor = Vendor(id=1, email="test_vendor@example.com")
    monkeypatch.setattr(Vendor, "query", Mock())
    Vendor.query.filter_by.return_value.first.return_value = vendor
    return vendor


def test_get_vendor_when_user_is_vendor(mock_vendor):
    current_user = Mock()
    current_user.role = UserRoles.vendor
    current_user.email = mock_vendor.email
    with patch("app.main.routes_products.current_user", current_user):
        result = _get_vendor(2)
        assert result == mock_vendor
        Vendor.query.filter_by.assert_called_once_with(email=current_user.email)


def test_get_vendor_when_user_is_not_vendor(mock_vendor):
    current_user = Mock()
    current_user.role = UserRoles.admin
    with patch("app.main.routes_products.current_user", current_user):
        result = _get_vendor(1)
        assert result == mock_vendor
        Vendor.query.filter_by.assert_called_once_with(id=1)
