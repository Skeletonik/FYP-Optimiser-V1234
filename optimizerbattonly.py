### Battery-only optimiser Version 3,4 based on the original ECC DHW OPTIMISER
### RELEASE 2.0
### Functionality: Import, Export, Generation, etc.

# Import PuLP (Linear Programming)
import pulp
import math

class BatteryOptimiser:
    """ LINEAR OPTIMIZER Rev 3.0
        Uses I, X, E to produce power plan for a battery
        Supports system: I, X
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
        if not (len(system['I']) == len(system['X']) ==  len(system['E']) ==  len(system['SM']['EXP'])):
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
        prob = pulp.LpProblem("Battery_Optimisation", pulp.LpMinimize)

        # VARIABLES

        # p=total simulated power use by HWT
        # m = sim import
        # e = sim export
        # p = {}

        ### T: BATTERY PARAMETERS
        # max battery power [kW] in/out
        bPower = 40
        # max battery in/out kWh/HH
        bMax_kWh = bPower/2
        # min and max battery SOC
        SOCmin = 0.1
        SOCmax = 0.9
        # Total kWh battery capacity
        SOCcap = 160
        # How much dSOC/kWh?
        # each kWh results in 1/SOC capacity %
        SOCp = 1/SOCcap
        # roundtrip efficiency - Design spec value = 0.88; Practical value = 0.85
        REff = 0.85
        SREff = math.sqrt(REff)
        # midnight desired SoC
        mSOC = 0.4


        # Adding simple cost of battery throughput
        # in [p/kWh of throughput]
        CoT = 3
        # input emission price in GBP/t
        carbon_price = system['CP']
        # recalculate to fit the units as p/g
        cp = carbon_price * 0.0001
        
        timeslots = range(len(system['I']))

        # new variables: simulated import and simulated export with the grid [kWh] & battery export(y) = negative & import(z)
        m = pulp.LpVariable.dicts("m", [n for n in timeslots], lowBound=0, upBound=100 , cat='Continuous')
        e = pulp.LpVariable.dicts("e", [n for n in timeslots], lowBound=-100, upBound=0 , cat='Continuous')
        y = pulp.LpVariable.dicts("y", [n for n in timeslots], lowBound=-bMax_kWh, upBound=0 , cat='Continuous')
        z = pulp.LpVariable.dicts("z", [n for n in timeslots], lowBound=0, upBound=bMax_kWh , cat='Continuous')


        # T: total el. usage:
        # Total usage (u) = Import [kWh] + Generation [kWh] - Export [kWh]
        # Real_u now without PV gen - it is not needed
        real_u = [(system['SM']['IMP'][t])-system['SM']['EXP'][t] for t in timeslots]

        # OBJECTIVE FUNCTION

        ####
        # T: adding emissions & battery


        # NEW OF4 JUST DROPPED:

        # LCA OF V2 Redemption
        # ... + Batt Import(t) * ( CoT ) ) )
        # + z[t] * CoT

        # T: minimising the sum of all import costs, (negative) export costs and battery throughput costs, including carbon
        # Sim Import(t)*(Grid Emissions(t)*CarbonP+ExpElectricityP(t))+(Export(neg)(t))*(Grid Emissions(t)*CarbonP+ExpElectricityP(t))+Batt_imp*CostThroughput
        # this can be duplicated and changed as needed (eg setting some variables constant, deleting the el. price component -> optim for carbon only...)

        prob += pulp.lpSum([
            m[t] * (system['I'][t] + cp * system['E'][t]) + e[t] * (system['X'][t] + cp * system['E'][t] ) + z[t] * CoT for t in
            timeslots
        ])


        # CONSTRAINTS
        w = {}
        for t in timeslots:

            # Battery operation

            if t == 0:
                # Create battery SoC level (b)
                b = []
                # Given this is the first time slot, set the SoC level to the desired level
                b.append(mSOC)
                # forcing flows to 0

                prob += y[t] == 0
                prob += z[t] == 0

            else:
                # SOC(t) = SOC(t-1) + Imp(t-1)*(SREff)*SOCp + Exp(t-1)*(1/SREff)*SOCp
                # Batt Exp is negative
                b.append ( b[t-1] + z[t] * SREff * SOCp + y[t] * (1/SREff) * SOCp )
                # Battery SOC limited as per operational restrictions
                prob += b[t] >= SOCmin
                prob += b[t] <= SOCmax

            # Power balance equation
            # _____________________________ - z[t] -y[t]
            # get all power flows to equal to zero, imports = exports
            # 0 = Sim Import + Sim Export(neg) - Generic usage + Generation[kWh] - Batt imp - Batt exp(neg)
            prob += pulp.lpSum([m[t] + e[t] - real_u[t] - z[t] -y[t]]) == 0
            # print(b[t])

        # Battery power limited - set in the variables' initialiastion


        # Ensure battery has its midnight target set

        prob += b[len(timeslots) - 1] >= mSOC

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
            # Variables auto-named by PuLP in format: [current_source][tank]_[timeslot]
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

        # powers['real_u'] = [real_u for t in timeslots]

        # powers['real_o']

        powers['max_time'] = max_time
        return powers


        

    