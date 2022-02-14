from backtester import (backtest, load_data)
import datetime
import grapher
import json
import math
import pandas as pd

file = open("./params.json")
strategies = json.load(file)

no_hedge_strategy = {
    "name": "No_Hedge",
    "SPY": 1,   
    "hedge": 0,   
    "rebalancing period": 365,   
    "target delta": [-0.03, -0.01],
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
        "verbose": True
    }

    # Load in data
    data = load_data(params["start"], params["end"])
    # Run with no hedge
    no_hedge_data = backtest(params, data)

    for strategy in strategies:
        params["strategy"] = strategy
        output = backtest(params, data)
        name = strategy["name"]
        grapher.make_graph(params["start"], params["end"], output["y axis"], name, no_hedge_data["y axis"])
        grapher.make_graph(params["start"], params["end"], output["hedge pl"], name + "_hedgepl", None)
    
        stats = open("./output/"+ name + "_stats.json", "w")
        stats.write(json.dumps(output["stats"]))
        stats.close()

        logs_file = open("./output/" + name + "_logs.txt", "w")
        logs_file.write("\n".join(output["logs"]))



if __name__ == "__main__":
    main()
