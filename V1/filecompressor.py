import pandas as pd
from tqdm import tqdm
from datetime import (datetime)



# UnderlyingOptionsEODCalcs_2021-09-01.csv
file_prefix = "UnderlyingOptionsEODCalcs_"  
# end=datetime.datetime(2021, 9, 2)
        
for current in tqdm(pd.date_range(start=datetime(2005, 1, 10),end=datetime(2021, 9, 2))):
    try:
        data = pd.read_csv("../data_uncompressed/" + file_prefix + str(current.date()) + ".csv")
        compressed = data[["underlying_symbol","quote_date","root","expiration","strike","option_type","bid_1545","ask_1545", "underlying_bid_1545", "underlying_ask_1545", "delta_1545"]]
        compressed.to_csv("../data/" + file_prefix + str(current.date()) + ".csv" )

    except FileNotFoundError:
        continue