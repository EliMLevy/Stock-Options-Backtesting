let lib = {}

lib["runSimulation"] = async function (params) {
    // Test the frontend without a backend
    if (params["fake api"]) {
        let data = []
        for (let i = 0; i < 100; i++) {
            data.push({ "Date": i, "Portfolio Value": Math.random() * 500 + 500, "No Hedge": Math.random() * 500 + 500 })
        }
        return data;
    }

    // Make the http request to the server
    var requestOptions = {
        method: 'GET',
        redirect: 'follow'
    };

    let queryString = `start=${params["start"]}&end=${params["end"]}&name=${params["name"]}&hedge=${params["hedge"]}&rebalancing_period=${params["rebalancing_period"]}&target_delta=${params["target_delta"]}&expiry=${params["expiry"]}&rollover=${params["rollover"]}&hedge_fragmentation=${params["hedge_fragmentation"]}&trade_frequency=${params["trade_frequency"]}`;
    let url = "http://localhost:8090/?";
    // Example queryString:
    // "start=2007-01-01
    //      &end=2010-01-01
    //      &name=test
    //      &hedge=0
    //      &rebalancing_period=365
    //      &target_delta=-0.01
    //      &expiry=60
    //      &rollover=15
    //      &hedge_fragmentation=8
    //      &trade_frequency=15"
    let response = await fetch(url + queryString, requestOptions)
    let result = await response.json();
    let data = {
        "datapoints": [],
        "stats": JSON.parse(result["stats"])
    }
    for (let i = 0; i < result["x vals"].length; i++) {
        data["datapoints"].push({ "Date": result["x vals"][i], "Portfolio Value": result["y vals"][i], "No Hedge": result["no hedge"][i] })
    }
    return data;




}


export default lib;