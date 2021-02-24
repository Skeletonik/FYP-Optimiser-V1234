from optimizer import main as uut
from scenarios2 import basic, adv

scenarios = {**basic, **adv}

scorecard = []

for name in scenarios:
    returned = uut(scenarios[name]['scenario'])
    print("Test: ", name)
    print(returned)

    # Check if optimiser status is as expected
    if returned['status'] == scenarios[name]['expectation']['status']:
        # If it was successful, check what we got
        if returned['status'] == 0:
            for v in returned['lp_variables']:
                if v.varValue != 0:
                    print(v.name, "=", v.varValue)
            # Check if (rounded) cost matches expectations
            if int(returned['cost']*100)/100 == scenarios[name]['expectation']['cost']:
                scorecard.append(1)
            else:
                scorecard.append(0)
        # If it wasn't successful, and that was expected, that's met expectations
        else:
            scorecard.append(1)
    else:
        scorecard.append(0)

print("Correctness: ", sum(scorecard)/len(scenarios))
