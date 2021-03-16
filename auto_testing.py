from optimizer import DHWOptimizer
from scenarios2 import basic, adv

scenarios = {**basic, **adv}

scorecard = []

for name in scenarios:
    # Run the Optimizer on this scenario
    lp = DHWOptimizer(scenarios[name]['scenario'])
    print("Test: ", name)
    print(lp.result())

    # Check if optimiser status is as expected
    if lp.result('status') == scenarios[name]['expectation']['status']:
        # If it was successful, check what we got
        if lp.result('status') == 0:
            for v in lp.result('lp_variables'):
                if v.varValue != 0:
                    print(v.name, "=", v.varValue)
            # Check if (rounded) cost matches expectations
            if int(lp.result('cost')*100)/100 == scenarios[name]['expectation']['cost']:
                scorecard.append(1)
            else:
                scorecard.append(0)
        # If it wasn't successful, and that was expected, that's met expectations
        else:
            scorecard.append(1)
    else:
        scorecard.append(0)

print("Correctness: ", sum(scorecard)/len(scenarios))
