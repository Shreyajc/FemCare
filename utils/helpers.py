import pandas as pd


def load_dataset(path):
    return pd.read_csv(path)


def format_number(value):
    return f"{value:,}"