import io
import json

import pandas as pd
import pytest

from app.main.routes_products import (
    MANDATORY_COLUMNS,
    product_columns_to_json,
    products_excel_to_df,
)


def test_products_columns_to_json():
    data = {"a": "1,2,3,4", "b": "qwer,qwer", "c": 3}
    ser = pd.Series(data)
    assert (
        product_columns_to_json(ser)
        == '{"a": ["1", "2", "3", "4"], "b": ["qwer"], "c": ["3"]}'
    )
    assert product_columns_to_json(pd.Series(dtype=object)) == ""
    data = pd.DataFrame([data])
    data["options"] = data[data.columns].apply(product_columns_to_json, axis=1)
    assert (
        data["options"][0] == '{"a": ["1", "2", "3", "4"], "b": ["qwer"], "c": ["3"]}'
    )


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
    source["input_required"] = False
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
