import pandas as pd
from tqdm import tqdm
from datetime import (datetime)

from sim_data import Pure_SPY

# file_prefix = "UnderlyingOptionsEODCalcs_"  
# spy_data = pd.DataFrame(columns=["date", "value"])


# for current in tqdm(pd.date_range(start=datetime(2005, 1, 10),end=datetime(2021, 9, 2))):

#     try:
#         # data = pd.read_csv("../data/" + file_prefix + str(current.date()) + ".csv")
#         # price = (data["underlying_bid_1545"].iloc[0] + data["underlying_ask_1545"].iloc[0]) / 2
#         df = pd.DataFrame({"date":[str(current.date())], "value": [price]})
#         spy_data = spy_data.append(df)
#         last = price
#     except FileNotFoundError:
#         df = pd.DataFrame({"date":[str(current.date())], "price": [last]})
#         spy_data = spy_data.append(df)


spy_data = pd.read_csv("SPY_Prices.csv", index_col=0)
# spy_data["value"] = Pure_SPY.y_vals

print(spy_data.head(5))
spy_data = spy_data.drop(["Unnamed: 0.1"], axis=1)
print(spy_data.head(5))


spy_data.to_csv("SPY_Prices.csv")