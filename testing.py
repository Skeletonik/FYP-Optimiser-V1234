from optimizer_zero import main as uut
from scenarios import basic, loss, solar, export, adv

scenarios = {**basic, **loss, **solar, **export, **adv}

scorecard = []

for name in scenarios:
    returned = uut(scenarios[name]['params'], scenarios[name]['config'])
    print("Test: ", name)
    print(returned)
    for v in returned['lp_variables']:
        if v.varValue != 0:
            print(v.name, "=", v.varValue)
    # Check if (rounded) cost and optimiser status match expectations
    if int(returned['cost']*100)/100 == scenarios[name]['expectation']['cost'] and returned['lp_status'] == scenarios[name]['expectation']['lp_status']:
        scorecard.append(1)
    else:
        scorecard.append(0)

print("Correctness: ", sum(scorecard)/len(scenarios))
