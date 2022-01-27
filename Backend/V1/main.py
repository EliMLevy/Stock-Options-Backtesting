from backtester import (backtest, load_data)
import datetime
import grapher
import json
import math
import pandas as pd

file = open("./simpleParams.json")
strategies = json.load(file)

no_hedge_strategy = {
    "name": "No_Hedge",
    "SPY": 1,   
    "hedge": 0,   
    "rebalancing period": 365,   
    "target delta": [-0.03, -0.01],
    "slippage": 0,   
    "commision": 0,
    "expiry": 120,   
    "rollover": 60,   
    "trade frequency": 15,   
    "hedge fragmentation": 1
}


def main():
    params = {
        "start": datetime.datetime(2012, 1, 10),
        "end": datetime.datetime(2016, 1, 10),
        "starting balance": 100000, 
        "strategy": no_hedge_strategy,
        "verbose": False
    }
    dates = [str(n.date()) for n in pd.date_range(start=params["start"],end=params["end"])]

    # Load in data
    data = load_data(params["start"], params["end"])
    # Run with no hedge
    no_hedge_data = backtest(params, data)
    # Overlay no hedge on strategies
    for strategy in strategies:
        params["strategy"] = strategy
        output = backtest(params, data)
        name = strategy["name"]
        grapher.make_graph(params["start"], params["end"], output[name]["y axis"], name, no_hedge_data["No_Hedge"]["y axis"])
    
        stats = open("./output/"+ name + "_stats.json", "w")
        stats.write(json.dumps(output[name]["stats"]))
        stats.close()
        jump = 3
        data_points = []
        dataPointsFile = open("./output/" + name + ".json", "w")
        for date, hedge, noHedge, hedge_pl in zip(dates[::jump], output[name]["y axis"][::jump], no_hedge_data["No_Hedge"]["y axis"][::jump], output[name]["hedge pl"][::jump]):
            data_points.append({"Date":date, "Portfolio Value": hedge, "No Hedge":noHedge, "Hedge PL": hedge_pl })
        dataPointsFile.write(json.dumps(data_points))
        dataPointsFile.close()

        # logs_file = open("./output/" + name + "_logs.txt", "w")
        # logs_file.write("\n".join(output[name]["logs"]))

        # hedge_pl_file = open("./output/" + name + "_hedgePL.json", "w")
        # hedge_pl_file.write(json.dumps(output[name]["hedge pl"][::3]))
        # hedge_pl_file.close()



if __name__ == "__main__":
    main()
