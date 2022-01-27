def grand_selector(df, c_type, delta, expiry):
    correct_type_delta_and_expiration = df[(df["option_type"] == c_type) & (df["delta_1545"] >= delta[0]) & (
        df["delta_1545"] <= delta[1]) & (df["expiration"] >= str(expiry.date())) & (df["underlying_symbol"] == "SPY")]
    sorted = correct_type_delta_and_expiration.sort_values(
        by=["expiration", "delta_1545"])
    if len(sorted) < 1:
        # print(df)
        # print(df["quote_date"].iloc[0],c_type, delta, expiry)
        raise ValueError("Could not find contract with delta range")

    result = sorted.iloc[0]
    return result


def bid_ask_mean(contract):
    return float((contract["bid_1545"] + contract["ask_1545"])) / 2


def select_contract(df, c_type, expiration, strike):
    temp = df[(df["expiration"] == expiration) & (
        df["strike"] == strike) & (df["option_type"] == c_type)  & (df["underlying_symbol"] == "SPY")]

    assert len(temp) > 0, "Could not find contract: " + str(c_type) + ", " + str(expiration) + ", " + str(strike) + str(df.head(5))


    result = temp.iloc[0]
    if result["underlying_symbol"] != "SPY":
        raise Exception("Wrong underlying")
    return result



def update_hedge_info(data, portfolio):
    result = dict()
    for contract in portfolio.hedge_queue:
        current_info = portfolio.get_holding_info(contract["name"])
        expiration = current_info["data"]["expiration"]
        strike = current_info["data"]["strike"]
        try:
            updated_info = select_contract(data, "P",expiration, strike)
            new_price = bid_ask_mean(updated_info) * 100
            portfolio.update_holding(contract["name"], new_price, data=updated_info)
            result[contract["name"]] = str(current_info["price"])  + " ==> " + str(new_price)
        except AssertionError:
            print("Failed to locate contract...")
    return result


