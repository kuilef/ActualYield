import locale
import os
import threading
from copy import deepcopy
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import yaml
from plotly import express as px
from st_aggrid import AgGrid, GridOptionsBuilder

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


def load_parameters() -> dict:
    if parameter_file := st.sidebar.file_uploader("upload parameters", type=['yaml']):
        result = yaml.safe_load(parameter_file)
    elif 'parameters' not in st.session_state:
        with open(os.path.join(os.sep, os.getcwd(), "config", 'params.yaml'), 'r') as fp:
            result = yaml.safe_load(fp)
    else:
        result = st.session_state.parameters

    return result


def prompt_plex_interval():
    date_col, time_col = st.columns(2)
    now_datetime = datetime.now()
    with time_col:
        start_time = st.time_input("start time", value=now_datetime.time())
        end_time = st.time_input("end time", value=now_datetime.time())
    with date_col:
        start_date = st.date_input("start date", value=now_datetime - timedelta(days=7))
        end_date = st.date_input("end date", value=now_datetime)
    start_datetime = datetime.combine(start_date, start_time)
    end_datetime = datetime.combine(end_date, end_time)

    return start_datetime, end_datetime


def display_pivot(grid: pd.DataFrame, rows: list[str], columns: list[str], values: list[str], hidden: list[str]):
    gb = GridOptionsBuilder()
    options_dict = {
        "pivotMode": True,
        "rowSelection": 'multiple',
        "columnSelection": 'multiple',
        "suppressAggFuncInHeader": True,
        "pivotColumnGroupTotals": "after",
        "pivotRowTotals": "before",
        "enableRangeSelection": True,
        "groupIncludeTotalFooter": True,  # show total footer for each group
        "groupIncludeGroupFooter": True,  # show group footer for each group
        "groupAggFields": values,  # fields to aggregate for group footers
        "groupAggFunc": 'sum',  # aggregation function to use for group footers
    }
    gb.configure_grid_options(**options_dict)

    gb.configure_selection(selection_mode='multi')
    gb.configure_side_bar(defaultToolPanel='columns')
    gb.configure_default_column(
        resizable=True,
        filterable=True,
        sortable=True,
        editable=False,
        groupable=True
    )
    columns_defs = ({row: {'field': row, 'rowGroup': True} for row in rows}
                    | {col: {'field': col, 'pivot': True} for col in columns}
                    | {val: {'field': val, 'aggFunc': 'sum', 'type': ["numericColumn"],
                             'cellRenderer': 'agGroupCellRenderer',
                            # 'valueFormatter': lambda number: locale.currency(number, grouping=True),
                             'cellRendererParams': {'innerRenderer': 'sumRenderer'}} for val in values}
                    | {hide: {'field': hide} for hide in hidden})
    for col in columns_defs.values():
        gb.configure_column(**col)

    go = gb.build()
    grid = grid.fillna(0)
    grid[values] = grid[values].astype(int)
    grid = grid.sort_values(by=values[0], ascending=False)
    AgGrid(grid, gridOptions=go)
