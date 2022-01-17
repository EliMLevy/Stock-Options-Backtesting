from backtester import (backtest, load_data)
import datetime
import grapher
import json

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
    "trade frequency": 7,   
    "hedge fragmentation": 1
}


def main():
    params = {
        "start": datetime.datetime(2005, 1, 10),
        "end": datetime.datetime(2021, 1, 10),
        "starting balance": 100000, 
        "strategy": no_hedge_strategy,
        "verbose": True
    }

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
        file = open("./output/"+ name + ".json", "w")
        file.write(json.dumps(output[name]["stats"]))
        file.write("\n".join(output[name]["logs"]))
        file.close()



if __name__ == "__main__":
    main()
