from backtester import backtest
import datetime
import grapher


params = {
    "start": datetime.datetime(2007, 1, 10),
    "end": datetime.datetime(2010, 12, 31),
    "starting balance": 100000,  # dollars
    "strategies": [
        {
            "name": "Crash90_10No_Frag",
            "SPY": 0.9,  # percent
            "hedge": 0.1,  # percent
            "rebalancing period": 365,  # day
            "target delta": [-0.03, -0.01],
            "slippage": 0,  # gap between the bid and the ask. Not important for SPY
            "commision": 0,
            "expiry": 60,  # days
            "rollover": 30,  # days
            "trade frequency": 7,  # days
            "hedge fragmentation": 1,
        },
        {
            "name": "Crash95_5",
            "SPY": 0.95,  # percent
            "hedge": 0.05,  # percent
            "rebalancing period": 365,  # day
            "target delta": [-0.03, -0.01],
            "slippage": 0,  # gap between the bid and the ask. Not important for SPY
            "commision": 0,
            "expiry": 60,  # days
            "rollover": 30,  # days
            "trade frequency": 7,  # days
            "hedge fragmentation": 1,
        },
        {
            "name": "Crash85_15",
            "SPY": 0.85,  # percent
            "hedge": 0.15,  # percent
            "rebalancing period": 365,  # day
            "target delta": [-0.03, -0.01],
            "slippage": 0,  # gap between the bid and the ask. Not important for SPY
            "commision": 0,
            "expiry": 60,  # days
            "rollover": 30,  # days
            "trade frequency": 7,  # days
            "hedge fragmentation": 1,
        },
        {
            "name": "Crash75_25",
            "SPY": 0.75,  # percent
            "hedge": 0.25,  # percent
            "rebalancing period": 365,  # day
            "target delta": [-0.03, -0.01],
            "slippage": 0,  # gap between the bid and the ask. Not important for SPY
            "commision": 0,
            "expiry": 60,  # days
            "rollover": 30,  # days
            "trade frequency": 7,  # days
            "hedge fragmentation": 1,
        },
    ],
    "verbose": False

}


def main():
    output = backtest(params)
    for strategy in params["strategies"]:
        name = strategy["name"]
        # print(output[name])
        grapher.make_graph(params["start"], params["end"], output[name]["y axis"], name)
        # file = open("./sim_data/"+ name + ".txt", "w")
        # file.write("\n".join(output[name]["logs"]))
        # file.write("\n\n")
        # file.write(str(output[name]["y axis"]))
        # file.close()


if __name__ == "__main__":
    main()
