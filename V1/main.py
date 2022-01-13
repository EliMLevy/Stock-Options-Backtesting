from backtester import backtest
import datetime
import grapher


params = {
    "start": datetime.datetime(2005, 1, 10),
    "end": datetime.datetime(2006, 8, 31),
    "starting balance": 100000,  # dollars
    "strategies": [
        {
            "name": "98_02_4_Frag",
            "SPY": 0.98,  # percent
            "hedge": 0.02,  # percent
            "rebalancing period": 60,  # day
            "target delta": [-0.03, -0.01],
            "slippage": 0,  # gap between the bid and the ask. Not important for SPY
            "commision": 0,
            "expiry": 60,  # days
            "rollover": 30,  # days
            "trade frequency": 7,  # days
            "hedge fragmentation": 10,
        },
        {
            "name": "98_02_2_Frag",
            "SPY": 0.98,  # percent
            "hedge": 0.02,  # percent
            "rebalancing period": 365,  # months
            "target delta": [-0.03, -0.01],
            "slippage": 0,  # gap between the bid and the ask. Not important for SPY
            # calculate afterward. #of trades and quantity of options traded.
            "commision": 0,
            "expiry": 60,  # days
            "rollover": 30,  # days
            "trade frequency": 7,  # days
            "hedge fragmentation": 2,
        },
        {
            "name": "98_02_8_Frag",
            "SPY": 0.98,  # percent
            "hedge": 0.02,  # percent
            "rebalancing period": 365,  # months
            "target delta": [-0.03, -0.01],
            "slippage": 0,  # gap between the bid and the ask. Not important for SPY
            # calculate afterward. #of trades and quantity of options traded.
            "commision": 0,
            "expiry": 60,  # days
            "rollover": 30,  # days
            "trade frequency": 7,  # days
            "hedge fragmentation": 8,
        }
    ],
    "verbose":False

}


def main():
    output = backtest(params)
    for strategy in params["strategies"]:
        name = strategy["name"]
        grapher.make_graph(params["start"], params["end"], output[name]["y axis"], name)
        file = open("./sim_data/"+name + ".txt", "w")
        file.write("\n".join(output[name]["logs"]))
        file.write("\n\n")
        file.write(str(output[name]["y axis"]))
        file.close()


if __name__ == "__main__":
    main()
