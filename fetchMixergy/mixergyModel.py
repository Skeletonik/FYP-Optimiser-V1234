import datetime

class MixergyModel:
    def __init__(self, tank_config:dict):
        # Validate the config
        self.validate(tank_config)
        # Given it's valid, process the config to a nice format
        self.unpack(tank_config)

    def validate(self, tank_config:dict) -> bool:
        # Check all the keys exist
        if not all([
            "HIDDEN_TANK_LOSSES" in tank_config['params'],
            "HEATING_TANK_GAIN" in tank_config['params'],
            "IDLE_TANK_LOSSES" in tank_config['params']
        ]):
            Exception("Invalid tank configuration: Missing keys")
        # Check they're all the same length (avoiding a keyerror)
        if not ( 
            len(tank_config['params']["HIDDEN_TANK_LOSSES"]) == 
            len(tank_config['params']["HEATING_TANK_GAIN"]) == 
            len(tank_config['params']["IDLE_TANK_LOSSES"])
        ):
            raise Exception("Mismatched tank parameter lengths")
        # If we've got a special tank, check it's correctly defined
        if len(tank_config['params']["HIDDEN_TANK_LOSSES"]) > 1:
            if len(tank_config['unusual_periods']) + 1 == len(tank_config['params']["HIDDEN_TANK_LOSSES"]):
                return True
            else:
                raise Exception("Not enough special period definitions for special periods")

    def unpack(self, tank_config:dict):
        self.tank_id = tank_config['tank_id']
        for param in tank_config['params']:
            setattr(self, param, tank_config['params'][param])
        # We've already checked these attrs exist
        # self.HIDDEN_TANK_LOSSES = tank_config['params']["HIDDEN_TANK_LOSSES"]
        # self.HEATING_TANK_GAIN  = tank_config['params']["HEATING_TANK_GAIN"]
        # self.IDLE_TANK_LOSSES   = tank_config['params']["IDLE_TANK_LOSSES"]

        special_periods = {}
        dateify = datetime.datetime.strptime
        for period in tank_config["unusual_periods"]:
            special_periods[period] = {}
            special_periods[period]['time_from'] = dateify(tank_config["unusual_periods"][period]['time_from'], "%H:%M").time()
            special_periods[period]['time_to'] = dateify(tank_config["unusual_periods"][period]['time_to'], "%H:%M").time()
        self.special_periods = special_periods

    def _isSpecialPeriod (self, ts:int) -> int:
        # Check every period to see if our time falls in the window
        # If it does, return the period
        # TBD: Overlapping periods (and/or rejecting them)
        time = datetime.datetime.fromtimestamp(ts/1000).time()
        for period in self.special_periods:
            if self.special_periods[period]['time_from'] <= time < self.special_periods[period]['time_to']:
                return int(period)
        # If nothing matches, it's not in one
        return 0

    def _tankLosses (self, delta_t:int, special_period:int=0) -> float:
        """ Find effect of losses on idle tank
        delta_t: time passed within the period loss value is needed
        pumped_loop: state of the pumped loop at this time """
        # Model should be improved, this is just linearised in Excel
        # It's a function so it can be improved
        return self.IDLE_TANK_LOSSES[special_period]*delta_t

    def _heatingGain (self, delta_t:int, energy:float, special_period:int=0) -> float:
        """ Find effect of heating on delta_SoC, to allow compensation
        power: kWh input over minute
        pumped_loop: bool, is the pump on? """
        # Model should be improved, this is just linearised in Excel

        # Total losses hidden by heating are:
        #   ([+ve gain effect of heating (%/min)] -  [-ve real losses (%/min)])
        return self.HEATING_TANK_GAIN[special_period]*energy - self.HIDDEN_TANK_LOSSES[special_period]*delta_t

    def _findDeltas (self, mixergy_data:dict) -> list:
        processed_data = []
        # Define the "previous" values for the first calculation
        prev = mixergy_data[0]

        for t in mixergy_data:
            # Consider recordedTime an int, for maths later
            # It's Unix format seconds
            # Because of python being weird (the fact that t and prev are both mix_data[0] in the first run), it appears
            #   I don't need to deal with prev separately. Dividing one does both
            t['recordedTime'] = int(t['recordedTime']/1000)
            delta_t       = t['recordedTime'] - prev['recordedTime']
            delta_charge  = t['charge'] - prev['charge']
            # Find energy put in the tank (Watt Seconds) -> kWh
            energy = (t['voltage'] * t['current'] * delta_t)/3600000
            # Adjust for heating effects hiding demand 
            # Then adjust for losses
            # What's left is pure demand
            heating_adjusted = delta_charge - self._heatingGain(delta_t, energy, self._isSpecialPeriod(t['recordedTime']))
            effect_adjusted  = heating_adjusted - self._tankLosses(delta_t, self._isSpecialPeriod(t['recordedTime']))
            # effect_adjusted = effect_adjusted if effect_adjusted < 0 else 0

            # Pack it all up in a nice dict and append to system record
            processed_data.append({'delta_t': delta_t, 'delta_charge': delta_charge, 'energy':energy, 'heating_adjusted': heating_adjusted, 'effect_adjusted': effect_adjusted})
            # Update the previous record to this one
            prev = t
        
        return processed_data

    def _nMinuteBlocks (self, delta_data:list, n_minutes:int) -> list:
        block_data = []
        sum_t = 0
        consumption = 0
        energy = 0

        for t in delta_data:
            sum_t += t['delta_t']
            consumption += t['effect_adjusted']
            energy += t['energy']
            # Once n_min have been summed, append and reset
            if sum_t >= n_minutes*60:
                block_data.append({
                    'delta_t': sum_t,
                    'consumption': consumption,
                    'energy': energy
                })
                sum_t = 0
                consumption = 0
                energy = 0
        # Put the remaining data in the last block
        # Needed to line up lengths
        block_data.append({
                    'delta_t': sum_t,
                    'consumption': consumption,
                    'energy': energy
                })

        return block_data

    def _accessRest (self, time_from:datetime.date, time_to:datetime.date) -> dict:
        # sledgehammer, walnut, we meet again
        import os, sys
        sys.path.append(os.path.relpath('./mixergyio_main'))
        # pylint: disable=import-error
        from user_rest import UserREST

        username = "damon@owensquare.coop"
        # username = "damon@a5gard.net"
        password = "SyM818^M5h"
        host = "www.mixergy.io"

        ts_from = int(time_from.timestamp())*1000
        ts_to   = int(time_to.timestamp())*1000

        with UserREST(host, username, password) as ur:
        # tanks = ur.get_tanks()
        # for sn, tank in tanks.items():
            tank = ur.get_tank(self.tank_id)
            measurements = ur.get_tank_measurements(tank, ts_from, ts_to)

        return measurements['content']

    def populate (self, time_from:datetime.date, time_to:datetime.date, supply_period_duration:int):
        # Fetch from the mixergy API
        retrieved          = self._accessRest(time_from, time_to)
        # Find deltaSoC in every time period
        deltas             = self._findDeltas(retrieved)
        # Sum the time periods to get demand in supply_period_duration-long blocks
        self.demand_blocks = self._nMinuteBlocks(deltas, supply_period_duration)

    def H (self):
        # Negative consumption (from MixergyModel context) is demand
        # H takes demand to be positive, so invert consumption
        # Removing the negative component of demand errs toward making more DHW (good)
        # We'll find out if that's excessive
        return [max(-slot['consumption'], 0) for slot in self.demand_blocks]

class DummyModel:
    def __init__ (self, tank_config):
        for param in tank_config['params']:
            setattr(self, param, tank_config['params'][param])

if __name__ == '__main__':
    # sledgehammer, walnut, we meet again
    import os, sys
    sys.path.append(os.path.relpath('.'))
    # pylint: disable=import-error
    from utilities import loadFromJSON
    tank_config = loadFromJSON('input_data/tank_parameters.json')
    import datetime
    ts_from = datetime.datetime(2021, 2, 28)
    ts_to   = datetime.datetime(2021, 3, 1)
    supply_period_duration = 30
    MX001224 = MixergyModel(tank_config['ECC'])
    MX001224.populate(ts_from, ts_to, supply_period_duration)
    print (MX001224.H())