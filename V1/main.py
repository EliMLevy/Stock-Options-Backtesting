from backtester import backtest
import datetime
import grapher


params = {
    "start": datetime.datetime(2006, 1, 1),
    "end": datetime.datetime(2006, 4, 29),
    "starting balance": 100000,  # dollars
    "strategies": [
        {
            "name": "correctness tests",
            "SPY": 0.96,  # percent
            "hedge": 0.04,  # percent
            "rebalancing period": 60,  # months
            "target delta": [-0.03, -0.01],
            "slippage": 0,  # gap between the bid and the ask. Not important for SPY
            # calculate afterward. #of trades and quantity of options traded.
            "commision": 0,
            "expiry": 60,  # days
            "rollover": 30,  # days
            "trade frequency": 7,  # days
            "hedge fragmentation": 10,
        }
    ]

}


def main():
    name = params["strategies"][0]["name"]
    output = backtest(params)
    grapher.make_graph(params["start"], params["end"], output[name]["y axis"], name)
    file = open("./sim_data/"+name + ".txt", "w")
    file.write("\n".join(output[name]["logs"]))
    file.write("\n\n")
    file.write(str(output[name]["y axis"]))
    file.close()


if __name__ == "__main__":
    main()
