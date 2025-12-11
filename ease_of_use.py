import pandas as pd

pd.options.display.width = 0


def pdf(df):
    print(df.to_string())
