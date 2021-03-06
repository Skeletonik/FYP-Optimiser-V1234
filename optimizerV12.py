### Version 2 DHW optimiser with added carbon based on V1: ECC DHW OPTIMISER
### RELEASE 1.0
### Functionality: Import, Export, Generation, etc.

# Import PuLP (Linear Programming)
import pulp

class DHWOptimizer:
    """ LINEAR OPTIMIZER Rev 2.0
        Uses I, X, G and H to produce power plan for n-many individually-defined tanks
        Supports system: I, X, G, H, heater_power, l_per_kWh, W_init, loss, dilution
        T: now also E as the emissions intensity and CP as the carbon price in GBP/t CO2eq
        """
    def __init__(self, system:dict):
        self.system_definition = system
        # VALIDATE
        validation = self._validate(self.system_definition)
        if validation['status'] == 0:    
            # CONSTRUCT
            self._constructProblem(system)
            # SOLVE
            self._solveLp(self.prob)
        # if validation failed, just give the validation status as feedback
        else:
            self.feedback = validation

    def _validate(self, system:dict) -> dict:
        """ SYSTEM VALIDATOR
            Validate the system configuration provided. Ensure all timeseriess are 
            valid lengths, and tank definition is physically valid 
            """
        # Ensure energy availability timeseriess are of consistent length
        if not (len(system['I']) == len(system['X']) == len(system['G']) ==  len(system['E']) ==  len(system['SM']['EXP'])):
            return {'status': 1, 'error': 'mismatched energy availability lengths'}

        # Completely changed to a model-based approach
        # Should just check the type...

        # If we're here, everything's fine
        return {'status': 0}

    def _constructProblem(self, system:dict) -> pulp.LpProblem:
        """ PROBLEM CONSTRUCTOR
            Take the system, and format to an LP problem
            """
        # Name the problem, and define as (cost) minimisation
        prob = pulp.LpProblem("Water_Optimisation", pulp.LpMinimize)

        # VARIABLES
        # There are as many of them as there are tanks*time slots, they must be >=0 and are continuous
        # i = import_power
        # s = self-consumed power
        # x is implicit, and is G[t] - sum(s[t])
        # Calculate self-consumption to stop system trying to re-export imported power when export pricing < import
        i = {}
        s = {}
        timeslots = range(len(system['I']))
        for tank in system['tanks']:
            i[tank] = pulp.LpVariable.dicts("i"+tank, [n for n in timeslots], lowBound=0, cat='Continuous')
            s[tank] = pulp.LpVariable.dicts("s"+tank, [n for n in timeslots], lowBound=0, cat='Continuous')

        ####
        # prob += pulp.lpSum([system['I'][t]*i[tank][t] - system['X'][t]*(system['G'][t]-s[tank][t]) for t in timeslots for tank in system['tanks']])
        # T: adding emissions
        # input emission price in GBP/t
        # emission_price = 1000
        emission_price = system['CP']
        # recalculate to fit the units as p/g
        em_p = emission_price * 0.0001

        # OBJECTIVE FUNCTION V2
        # Sum of ([import costs] + [opportunity cost of export]) across every time period

        prob += pulp.lpSum([
            (system['I'][t]+system['E'][t]*em_p) * sum([i[tank][t] for tank in system['tanks']]) +
            (system['X'][t]+system['E'][t]*em_p) * sum([s[tank][t] for tank in system['tanks']])
            for t in timeslots
        ])

        # OF OG: No emissions Version 1
        """
        prob += pulp.lpSum([
            system['I'][t]*sum([i[tank][t] for tank in system['tanks']]) +
            system['X'][t]*sum([s[tank][t] for tank in system['tanks']])
            for t in timeslots
        ])
        """

        # CONSTRAINTS
        w = {}
        for t in timeslots:
            # For every tank in the system. All EQs in here apply to each tanks
            for tank in system['tanks']:
                # Set up the initial conditions
                if t == 0:
                    # Create a w[ater level] list for each tank
                    w[tank] = []
                    # Given this is the first time slot, set the SoC level to the s_init
                    w[tank].append(system['tanks'][tank].soc_init)
                # Everything in the middle is calculated
                else:
                    # Otherwise, calculate water from the previous 30min and consumption/generation
                    # water at t = (w[t-1] - consumption + (-ve) loss) + (power * heated water per kW within time period)
                    # Sadly, because this is LP, we can't pass the variables in to a function
                    w[tank].append(
                        (w[tank][t-1] - system['tanks'][tank].H(t-1) + system['tanks'][tank].lossInSupplyPeriod(t-1)) + 
                        (i[tank][t-1]+s[tank][t-1])*system['tanks'][tank].heatingFromEnergy(t)
                    )
                    # T: print(system['tanks'][tank].H(t-1))
                # Ensure available SoC at t in each tank >= SoC demand in coming 30min (i.e. demand is met)
                prob  += w[tank][t] >= system['tanks'][tank].H(t)
                # Heater power, regardless of energy source, limited
                prob  += i[tank][t]+s[tank][t] <= system['tanks'][tank].heater_power
                # Each tank cannot contain negative water, and has a capacity limit of 100%
                prob += 0 <= w[tank][t] <= 100
                
            # Can only use generated solar once across all tanks
            prob += pulp.lpSum([s[tank][t] for tank in system['tanks']]) <= system['G'][t]

        # Ensure each tank has its target set
        # Dual constraint on final time period
        for tank in system['tanks']:
            prob += w[tank][len(timeslots)-1] >= system['tanks'][tank].soc_target
            
        self.prob = prob

    def _solveLp (self, prob:pulp.LpProblem) -> dict:
        """ LP SYSTEM SOLVER
            Solve the provided LP Problem, and package feedback to self.result() 
            """
        # LINEAR PROGRAMMING SOLUTION
        # CBC is the default, but needs defining so I can set msg=0
        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        # prob.solve()

        # PACKAGE RETURN DICT
        feedback = {}
        feedback['lp_status']    = pulp.LpStatus[prob.status]
        # Status 0 means things went well. Status 2 means optimization failed
        # Status 1 was covered above
        feedback['status']       = 0 if feedback['lp_status'] == "Optimal" else 2
        feedback['lp_variables'] = prob.variables()
        feedback['cost']         = pulp.value(prob.objective)
        self.feedback = feedback

    def system(self, select:str=None):
        """ QUERY SYSTEM
            Return the system which was/will be LP-ed
            """
        return self.system_definition

    def result(self, select:str=None):
        """ QUERY RESULT
            Return the LP result, or subset thereof, as reqested
            Behaves kinda like an obj of one layer depth (with parens)
            """
        if select == None:
            return self.feedback
        else:
            return self.feedback[select]

    def asDict (self) -> dict:
        """ LP RESULT AS dict v2 (formerly in runOptimizer)
            Parses the PuLP output, prob.variables, to a nice dict with FP numbers
            Much nicer to deal with elsewhere
            """
        variables = self.result('lp_variables')
        powers = {}
        max_time = 0
        for variable in variables:
            # Variables auto-named by PuLP in format: [current_source][tank]_[timeslot]
            # So this makes a list ["[current_source][tank]", "[timeslot]"] for this variable
            name_components = variable.name.split('_')
            # Separate the name out to its component parts
            current_source = name_components[0][0]
            tank = name_components[0][1:]
            time = int(name_components[1])
            
            if tank not in powers:
                powers[tank] = {"i":{}, "s":{}}
            # Take the value of the variable dict
            # Because the order of [variables] is 0, 1, 10, 11, etc. we have to make a dict
            # Turns out I was tired doing v1 of this.
            # Now, we create a dict, per tank, containing i and s. In there is the dict for power@time
            # So the structure is [tank][current_source][time]
            # Then below, once we've collected all the data in our dicts, turn the dicts to lists in place
            powers[tank][current_source][time] = variable.varValue
            max_time = max(max_time, time)

        for tank in powers:
            # Go through in numeric, not dict entry, order to create an ordered list
            powers[tank]['i'] = [powers[tank]['i'][t] for t in range(max_time+1)]
            powers[tank]['s'] = [powers[tank]['s'][t] for t in range(max_time+1)]
        powers['max_time'] = max_time
        return powers


        

    