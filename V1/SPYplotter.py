import pandas as pd
from tqdm import tqdm
from datetime import (datetime)

file_prefix = "UnderlyingOptionsEODCalcs_"  
spy_data = pd.DataFrame(columns=["date", "price"])
last = 118.845

for current in tqdm(pd.date_range(start=datetime(2005, 1, 10),end=datetime(2021, 9, 2))):

    try:
        data = pd.read_csv("../data/" + file_prefix + str(current.date()) + ".csv")
        price = (data["underlying_bid_1545"].iloc[0] + data["underlying_ask_1545"].iloc[0]) / 2
        df = pd.DataFrame({"date":[str(current.date())], "price": [price]})
        spy_data = spy_data.append(df)
        last = price
    except FileNotFoundError:
        df = pd.DataFrame({"date":[str(current.date())], "price": [last]})
        spy_data = spy_data.append(df)


spy_data.to_csv("SPY_Prices.csv")