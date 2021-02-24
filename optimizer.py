### ECC DHW OPTIMISER
### RELEASE 0.0a
### Functionality: Import

def main(params, config):
    """ LINEAR OPTIMIZER Rev 0.0a
    Uses I and H to produce power plan for a single tank
    Supports params: I, H, heater_power, l_per_kWh, W_init, loss, dilution
    """
    
    # VALIDATION
    # Validate config
    if not (config['heater_power'] > 0 and config['litres_per_kWh'] > 0 and config['dilution'] >= 1 and
            0 <= config['loss'] <= 1 and config['w_init'] >= 0):
        return {'status': 1, 'error':"Invalid configuration"}
    # Validate params
    if len(params['I']) == len(params['X']) == len(params['G']) == len(params['H']):
        timeslots = range(len(params['I']))
    else:
        return {'status': 1, 'error':"Mismatched param lengths"}

    # LINEAR PROGRAMMING SETUP
    # Import PuLP (Linear Programming)
    import pulp

    # Define the problem as (cost) minimisation
    prob = pulp.LpProblem("Water Optimisation", pulp.LpMinimize)

    # VARIABLES
    # There are as many of them as there are time slots, they must be >=0 and are continuous
    # i = import_power
    i = pulp.LpVariable.dicts("i", [n for n in timeslots], lowBound=0, cat='Continuous')

    # OBJECTIVE
    # Sum of [import costs minus export costs]
    prob += pulp.lpSum([params['I'][t]*i[t] for t in timeslots])

    # CONSTRAINTS
    w = []
    for t in timeslots:
        if t == 0:
            # water at t=0 is w_init, by definition
            w.append(config['w_init'])
        else:
            # water at t is (w[t-1] - consumption)*(1-loss) + heated volume
            w.append((w[t-1]- params['H'][t-1]*config['dilution'])*(1-config['loss']) + (i[t-1])*config['litres_per_kWh'])
        # Available DHW at t >= DHW demand (after dilution) in coming 30min
        prob  += w[t] >= params['H'][t]*config['dilution']
        # Heater power limited
        prob  += i[t] <= config['heater_power']

    # LINEAR PROGRAMMING SOLUTION
    # CBC is the default, but needs defining so I can set msg=0
    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    # PACKAGE RETURN OBJECT
    feedback = {}
    feedback['status']       = 0
    feedback['lp_status']    = pulp.LpStatus[prob.status]
    feedback['lp_variables'] = prob.variables()
    feedback['cost']         = pulp.value(prob.objective)
    return feedback
