### Battery + DHW OPTIMISER
### RELEASE 2.0
### Functionality: Import, Export for each energy stoage

# Import PuLP (Linear Programming)
import pulp
import math

class DHWOptimizer:
    """ LINEAR OPTIMIZER Rev 3.0
        Uses I, X, H and total import&export OSCE smart meter readings to produce power plan for n-many individually-defined tanks and a battery
        Supports system: I, X, SM-imp, SM-exp, H, heater_power, l_per_kWh, W_init, loss, dilution
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

        # p=total simulated power use by HWT
        # m = sim import
        # e = sim export
        p = {}

        # Battery parameters
        # max battery power [kW] in/out
        bPower = 40
        # max battery in/out kWh/HH
        bMax_kWh = bPower/2
        # min and max battery SOC
        SOCmin = 0.2
        SOCmax = 0.8
        # Total kWh battery capacity
        SOCcapacity = 160
        # How much dSOC/kWh?
        # each kWh results in 1/SOC capacity %
        SOCp = 1/SOCcapacity
        # roundtrip efficiency
        REff = 0.85
        SREff = math.sqrt(REff)
        # midnight desired SoC
        midnightSoC = 0.5

        # UNUSED: Calculating Battery Lifecycle
        # can be simplified
        """
        Batt_kWh_price = 550
        Cycling_degrad_share = 0.77
        Lifetime_FEC = 2050
        Batt_GHG_kWhproduction = 76.07
        Batt_price = Batt_kWh_price * SOCcapacity
        Lifetime_kWh = Lifetime_FEC * SOCcapacity
        # How much does it cost (in [p]) to cycle 1 kWh through the battery
        b_use_cost = 100 * Batt_price * Cycling_degrad_share / Lifetime_kWh
        # How much GHG emissions (in [g CO2eq]) is the 1 kWh cycling through the battery responsible for
        b_use_ghg = 1000 * Batt_GHG_kWhproduction * Cycling_degrad_share / Lifetime_FEC
        print(b_use_ghg)
        """

        # T: adding emissions
        # input emission price in GBP/t
        carbon_price = system['CP']
        # recalculate to fit the units as p/g
        cp = carbon_price * 0.0001


        timeslots = range(len(system['I']))
        # new variable combining i & s as p [kWh]
        for tank in system['tanks']:
            # i[tank] = pulp.LpVariable.dicts("i"+tank, [n for n in timeslots], lowBound=0, cat='Continuous')
            # s[tank] = pulp.LpVariable.dicts("s"+tank, [n for n in timeslots], lowBound=0, cat='Continuous')
            p[tank] = pulp.LpVariable.dicts("p" + tank, [n for n in timeslots], lowBound=0, cat='Continuous')

        # new variables: simulated import and simulated export with the grid [kWh] & battery export(y) = negative & import(z)
        m = pulp.LpVariable.dicts("m", [n for n in timeslots], lowBound=0, upBound=100 , cat='Continuous')
        e = pulp.LpVariable.dicts("e", [n for n in timeslots], lowBound=-100, upBound=0 , cat='Continuous')
        y = pulp.LpVariable.dicts("y", [n for n in timeslots], lowBound=-bMax_kWh, upBound=0 , cat='Continuous')
        z = pulp.LpVariable.dicts("z", [n for n in timeslots], lowBound=0, upBound=bMax_kWh , cat='Continuous')


        # T: total el. usage:
        # Total usage (u) = Import [kWh] + Generation [kWh] - Export [kWh]
        # assuming HH SP
        real_u = [(system['SM']['IMP'][t])+system['G'][t]-system['SM']['EXP'][t] for t in timeslots]

        # real hot water tank mixergy power use, from Mixergy API, in kWh
        real_hwt_p = [
            sum(E_t)
            for E_t in zip(*[system['tanks'][tank].realworldE() for tank in system['tanks']])
        ]

        # T: Other electricity usage (o) = Total usage - Real Mixergy Use
        # Needed for future power balancing
        real_o = [real_u[t] - real_hwt_p[t] for t in timeslots]


        # NEW OF4 JUST DROPPED:
        # vey same OF as in the battonly version

        # T: minimising the sum of all import costs, (negative) export costs and battery throughput costs, including carbon
        # Sim Import(t)*(Grid Emissions(t)*CarbonP+ExpElectricityP(t))+(Export(neg)(t))*(Grid Emissions(t)*CarbonP+ExpElectricityP(t))+Batt_imp*CostThroughput
        # this can be duplicated and changed as needed (eg setting some variables constant, deleting the el. price component -> optim for carbon only...)

        prob += pulp.lpSum([
            m[t] * (system['I'][t]+cp*system['E'][t]) + e[t] * (system['X'][t] +cp*system['E'][t]) for t in timeslots
        ])


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
                    # p now in [kWh], thus doubling to get the average kW power
                    # water at t = (w[t-1] - consumption + (-ve) loss) + (power * heated water per kW within time period)
                    # Sadly, because this is LP, we can't pass the variables in to a function
                    w[tank].append(
                        (w[tank][t-1] - system['tanks'][tank].H(t-1) + system['tanks'][tank].lossInSupplyPeriod(t-1)) + 
                        p[tank][t-1]*2*system['tanks'][tank].heatingFromEnergy(t)
                    )


                # Ensure available SoC at t in each tank >= SoC demand in coming 30min (i.e. demand is met)
                prob  += w[tank][t] >= system['tanks'][tank].H(t)
                # Heater power, regardless of energy source, limited
                prob += p[tank][t]*2 <= system['tanks'][tank].heater_power

                # Each tank cannot contain negative water, and has a capacity limit of 100%
                prob += w[tank][t] >= 0
                prob += w[tank][t] <= 100

            # Can only use generated solar once across all tanks - T: not anymore used
            # prob += pulp.lpSum([s[tank][t] for tank in system['tanks']]) <= system['G'][t]

            # T: Battery operation

            if t == 0:
                # Create battery SoC level (b)
                b = []
                # Given this is the first time slot, set the SoC level to the desired level
                b.append(midnightSoC)

                # forcing flows to 0 at midight

                prob += y[t] == 0
                prob += z[t] == 0

            else:
                # SOC(t) = SOC(t-1) + Imp(t-1)*(SREff)*SOCp + Exp(t-1)*(1/SREff)*SOCp
                # Batt Exp is negative
                b.append ( b[t-1] + z[t] * SREff * SOCp + y[t] * (1/SREff) * SOCp )
                # Battery SOC limited as per operational restrictions
                prob += b[t] >= SOCmin
                prob += b[t] <= SOCmax

            # power balance function
            # _____________________________ - z[t] -y[t]
            # get all power flows to equal to zero, imports = exports
            # 0 = Sim Import + Sim Export(neg) - Generic usage + Generation[kWh] - Batt imp - Batt exp(neg) - Mixergy
            prob += pulp.lpSum([m[t] + e[t] - real_o[t] + system['G'][t] - z[t] -y[t] - [p[tank][t]  for tank in system['tanks']]]) == 0
        # Battery power limited - in veriables settings


        # Ensure each tank has its target set
        # Dual constraint on final time period
        for tank in system['tanks']:
            prob += w[tank][len(timeslots)-1] >= system['tanks'][tank].soc_target

        # same for the Battery
        prob += b[len(timeslots) - 1] >= midnightSoC

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
        print(feedback['lp_status'])
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
            # T: made this much more ugly and less scalable - only assumes 2 specific HW tanks, could easily be changed probably to orig. version
            name_components = variable.name.split('_')
            # Separate the name out to its component parts
            optim_var_type = name_components[0]

            time = int(name_components[1])

            if optim_var_type not in powers:
                powers[optim_var_type] = {time: {}}

            # Take the value of the variable dict
            # Because the order of [variables] is 0, 1, 10, 11, etc. we have to make a dict
            # Turns out I was tired doing v1 of this.
            # Now, we create a dict, per tank, containing i and s. In there is the dict for power@time
            # So the structure is [tank][current_source][time]
            # Then below, once we've collected all the data in our dicts, turn the dicts to lists in place
            q = variable.varValue
            powers[optim_var_type][int(time)] = q

            max_time = max(max_time, time)

        for optim_var_type in powers:
            # Go through in numeric, not dict entry, order to create an ordered list
            powers[optim_var_type] = [powers[optim_var_type][t] for t in range(max_time+1)]

        powers['max_time'] = max_time
        return powers


        

    