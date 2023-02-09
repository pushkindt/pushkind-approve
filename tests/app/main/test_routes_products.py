import pandas as pd

from app.main.routes_products import products_excel_to_df


def test_products_excel_to_df():
    products_excel_to_df(None)
    assert True
