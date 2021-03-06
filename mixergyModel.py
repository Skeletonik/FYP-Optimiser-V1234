import datetime

class MixergyModel:
    def __init__(self, tank_config:dict):
        """ Initialise a MixergyModel. Can create a dummy if H is provided in params """
        # Validate the config
        self._validate(tank_config)
        # Given it's valid, process the config to a nice format
        self._unpack(tank_config)

    def _validate(self, tank_config:dict) -> bool:
        """ Validate the tank config being provided. Most important, check TANK_LOSSES and HEATING_TANK_GAIN exist """
        # Check all the keys exist
        if not all([
            "TANK_LOSSES" in tank_config['params'],
            "HEATING_TANK_GAIN" in tank_config['params']
        ]):
            raise Exception("Invalid tank configuration: Missing keys")
        # Check they're all the same length (avoiding a keyerror)
        if not ( 
            len(tank_config['params']["TANK_LOSSES"]) == 
            len(tank_config['params']["HEATING_TANK_GAIN"])
        ):
            raise Exception("Mismatched tank parameter lengths")
        # If we've got a special tank, check it's correctly defined
        # Special tanks are defined by a variable list len()>1
        if len(tank_config['params']["TANK_LOSSES"]) > 1:
            if len(tank_config['unusual_periods']) + 1 == len(tank_config['params']["TANK_LOSSES"]):
                return True
            else:
                raise Exception("Not enough special period definitions for special periods")

    def _unpack(self, tank_config:dict):
        """ Unpack the settings dict to the tank object. Process any dates/times from JSON, etc """
        self.tank_id = tank_config['tank_id']
        # This may or may not agree with the dummy, untested
        if 'user_pass' in tank_config:
            self.user_pass = tank_config['user_pass']

        # If there's an H, it's intended to be used as demand_blocks
        # H in class MixergyModel is a function we don't want overwritten
        # Repack H to meet the expected format
        if "H" in tank_config["params"]:
            self.demand_blocks = [{"consumption": this_H} for this_H in tank_config["params"]["H"]]
            tank_config["params"].pop("H")

        # Set a default SoC target
        self.soc_target = 0

        # Unpack all the params
        # We've already checked the key ones exist
        for param in tank_config['params']:
            setattr(self, param, tank_config['params'][param])

        # If there are unusual periods, process their dates and add them to the object
        if "unusual_periods" in tank_config:
            special_periods = {}
            dateify = datetime.datetime.strptime
            for period in tank_config["unusual_periods"]:
                special_periods[period] = {}
                special_periods[period]['time_from'] = dateify(tank_config["unusual_periods"][period]['time_from'], "%H:%M").time()
                special_periods[period]['time_to'] = dateify(tank_config["unusual_periods"][period]['time_to'], "%H:%M").time()
            self.special_periods = special_periods


    def _isSpecialPeriod (self, date_time:[datetime.datetime, int]) -> int:
        """ Check if the current time is special, and if it is, what kind """
        # Check every period to see if our time falls in the window
        # If it does, return the period
        # TBD: Overlapping periods (and/or rejecting them)
        if type(date_time) is int:
            date_time = datetime.datetime.fromtimestamp(date_time)
        if hasattr(self, 'special_periods'):
            for period in self.special_periods:
                if self.special_periods[period]['time_from'] <= date_time.time() < self.special_periods[period]['time_to']:
                    return int(period)
        # If we're here, nothing matches; it's not in one
        return 0

    def _tankLosses (self, delta_t:int, special_period:int=0) -> float:
        """ Find effect of losses on idle tank
        delta_t: time passed within the period loss value is needed
        special_period: which special period applies at this time """
        # Model should be improved, this is just linearised in Excel
        # It's a function so it can be improved
        return self.TANK_LOSSES[special_period]*delta_t

    def _heatingGain (self, delta_t:int, energy:float, special_period:int=0) -> float:
        """ Find effect of heating on delta_SoC, to allow compensation
        delta_t: duration of the heating period
        energy: kWh provided
        special_period: which special period applies (none = 0) """
        # Model should be improved, this is just linearised in Excel

        # Total losses hidden by heating are:
        #   ([+ve gain effect of heating (%/min)] -  [-ve real losses (%/min)])
        ########### So why does the comment say minus and the code say plus? - evening Seb ###########
        # return self.HEATING_TANK_GAIN[special_period]*energy + self.TANK_LOSSES[special_period]*delta_t

        heating_gains = self.HEATING_TANK_GAIN[special_period]*energy
        return heating_gains + self._tankLosses(delta_t, special_period)

    def _findDeltas (self, mixergy_data:dict) -> list:
        """ Find the change in SoC due to demand. Removes heating and loss effects 
        using _heatingGain() and _tankLosses() """
        processed_data = []
        # Define the "previous" values for the first calculation
        prev = mixergy_data[0]

        for t in mixergy_data:
            # Consider recordedTime an int, for maths later
            # It's Unix format seconds
            # Because of python being weird (the fact that t and prev are both mix_data[0] in the first run), it appears
            #   I don't need to deal with prev separately. Dividing one does both
            t['recordedTime'] = datetime.datetime.fromtimestamp(t['recordedTime']/1000)
            delta_t       = t['recordedTime'] - prev['recordedTime']
            delta_charge  = t['charge'] - prev['charge']
            # Find energy put in the tank (Watt Seconds) -> kWh
            energy = (t['voltage'] * t['current'] * delta_t.seconds)/3600000
            # Adjust to remove heating effect (deltaSoC is just losses) and 
            #   remove losses (deltaSoC should be zero)
            heating_adjusted = delta_charge - self._heatingGain(delta_t.seconds, energy, self._isSpecialPeriod(t['recordedTime']))
            # Legacy hangover. Probably trivially removable, but not egregious enough to bother. 
            effect_adjusted = heating_adjusted

            # Pack it all up in a nice dict and append to system record
            processed_data.append({
                'recorded_time': t['recordedTime'], 
                'delta_t': delta_t, 
                'delta_charge': delta_charge, 
                'energy':energy, 
                'heating_adjusted': heating_adjusted, 
                'effect_adjusted': effect_adjusted
            })
            # Update the previous record to this one
            prev = t
        
        return processed_data

    def _nMinuteBlocks (self, delta_data:list, n_minutes:int) -> list:
        """ Collect up minute-by-minute data to n_minute-long blocks. Spare minutes 
        are added to the last block """
        blocks_data = []
        block_starttime = delta_data[0]['recorded_time']
        block_duration  = datetime.timedelta(minutes = n_minutes)
        consumption = 0
        energy = 0

        for t in delta_data:
            # Whilst we're not up to the half hour mark, keep adding
            if t['recorded_time'] <= block_starttime + block_duration:
                consumption += t['effect_adjusted']
                energy += t['energy']
            else:
                # Once we've reached it, write out the timeslot
                # time - time = deltatime object. deltatime.seconds
                blocks_data.append({
                    'delta_t': (t['recorded_time'] - block_starttime).seconds,
                    'consumption': consumption,
                    'energy': energy
                })
                # Then, set the next threshold to block_starttime += **block_duration**
                # Adding to the last recorded time causes 1min/2blocks drift, so breaks >24hrs
                # This way we'll be a consistent small amount out, and hopefully all data is used
                block_starttime += block_duration
                # Use the values for this minute which tipped us over
                consumption = t['effect_adjusted']
                energy = t['energy']

        # Write out the last of the data to a block.
        # You're borderline guaranteed to come up ~1min short
        # Without this, that makes you a whole block short
        blocks_data.append({
                'delta_t': (t['recorded_time'] - block_starttime).seconds,
                'consumption': consumption,
                'energy': energy
            })

        return blocks_data

    def _accessRest (self, time_from:datetime.date, time_to:datetime.date) -> dict:
        """ Access the Mixergy REST API to retrieve tank data. 
        **** Credit to CEPro ****
        Uses CEPro user_rest 
        """
        import datetime
        # sledgehammer, walnut, we meet again
        import os, sys
        sys.path.append(os.path.relpath('./mixergyio_main'))
        # pylint: disable=import-error
        from user_rest import UserREST

        [username, password] = self.user_pass

        host = "www.mixergy.io"

        # Find how many results we're expecting (one per minute)
        delta_t        = time_to - time_from
        expected_count = delta_t.days*24*60 + delta_t.seconds/60

        # Can only request 1.38days from UserREST, so need to divide up
        # Set to 1.38 on the off chance someone wants 1.2 days or something
        content = []
        with UserREST(host, username, password) as ur:
            tank = ur.get_tank(self.tank_id)
            # While the time being requested is too long, chop it to smaller windows
            while time_to - time_from > datetime.timedelta(days=1.38):
                # Find the day 1 day ahead
                time_plusdelta = time_from + datetime.timedelta(days=1)
                # Make the timestamps for our partial window
                ts_from = int(time_from.timestamp())*1000
                ts_plusdelta = int(time_plusdelta.timestamp())*1000
                # Add the content from that request to the end of the content list
                content += ur.get_tank_measurements(tank, ts_from, ts_plusdelta)['content']
                # Move the from date forwards
                time_from = time_plusdelta
            # With less than 1.38 days deltatime, make a straightforward request
            # Also append to the list, so it's compatible either way
            ts_from = int(time_from.timestamp())*1000
            ts_to   = int(time_to.timestamp())*1000
            content += ur.get_tank_measurements(tank, ts_from, ts_to)['content']

        # Raise a warning if we don't have enough data (close enough anyway)
        # This error is annoying to find
        # TBD - improve resilience by using real record time, not deltas, to group
        # This will warn when we're missing >200min of data

        if expected_count - len(content) > 200:
            raise Warning("There's lots of missing data (too little) for tank ", self.tank_id, ". Check the Mixergy portal for offline time in configured window. Got", len(content), "data items, expected ", expected_count)

        return content

    def populate (self, time_from:datetime.date, time_to:datetime.date, supply_period_duration:int):
        """ Populate this MixergyModel from the Mixergy API. Fetches data between dates, and brackets
        demand in to supply periods of n minutes """
        self.supply_period_duration = supply_period_duration
        # Fetch from the mixergy API
        retrieved          = self._accessRest(time_from, time_to)
        # Use the first charge value as soc_init, and last as soc_target
        # This gives us a fair grounds for comparison of energy consumption
        self.soc_init      = retrieved[0]["charge"]
        self.soc_target    = retrieved[-1]["charge"]
        # Find deltaSoC in every time period
        deltas             = self._findDeltas(retrieved)
        # Sum the time periods to get demand in supply_period_duration-long blocks
        self.demand_blocks = self._nMinuteBlocks(deltas, supply_period_duration)

    def H (self, timeslot:int=None) -> float:
        """ Calculate H, returning either the full list or only a single timeslot. 
        Sets a floor on H of zero. """
        # Negative consumption (from MixergyModel context) is demand
        # H takes demand to be positive, so invert consumption
        # Removing the negative component of demand errs toward making more DHW (good)
        # We'll find out if that's excessive
        # Also kinda not happy with it, feels like a fudge
        if timeslot == None:
            # return [max(-slot['consumption'], 0) for slot in self.demand_blocks]
            return [-slot['consumption'] for slot in self.demand_blocks]
        elif timeslot <= len(self.demand_blocks):
            # return max(-self.demand_blocks[timeslot]['consumption'], 0)
            return -self.demand_blocks[timeslot]['consumption']
        else:
            raise Exception("You're accessing a timeslot which doesn't exist. Also, I don't know how you even got here.")

    def realworldE (self, timeslot:int=None) -> float:
        """ Retrieve the real E (import Energy) for the Mixergy tank. Only runs on real-world data (obv) """
        if timeslot == None:
            return [slot['energy'] for slot in self.demand_blocks]
        elif timeslot <= len(self.demand_blocks):
            return self.demand_blocks[timeslot]['energy']
        else:
            raise Exception("You're accessing a timeslot which doesn't exist.")

    def lossInSupplyPeriod (self, timeslot:int) -> float:
        """ find the tank SoC loss in a given supply_period_duration. Also checks for special times. For external use """
        # Convert the time to seconds since midnight Unix time
        # _isSpecialPeriod() throws away the date, so that's fine
        time = timeslot*self.supply_period_duration*60
        # DeltaT is a number of seconds
        # supply_period_duration is a number of minutes
        return self._tankLosses(self.supply_period_duration*60, self._isSpecialPeriod(time))

    def heatingFromEnergy (self, timeslot:int) -> float:
        """ find the tank SoC/kW in a supply_period_duration. Also checks for special times. For external use """
        ts = timeslot*self.supply_period_duration*60
        special_period = self._isSpecialPeriod(ts)
        # This estimate is a simplified version of the reverse-engineering one above
        # This value will *all* be multiplied by power
        # Can't make this a function which accepts power because LP
        # tank gain = %SoC/kWh. 
        # result will be *kW, so compensate for the "h" here
        return self.HEATING_TANK_GAIN[special_period]*(self.supply_period_duration/60)

if __name__ == '__main__':
    # sledgehammer, walnut, we meet again
    import os, sys
    sys.path.append(os.path.relpath('.'))
    # pylint: disable=import-error
    from utilities import loadFromJSON
    tank_config = loadFromJSON('input_data/tank_parameters.json')
    import datetime
    ts_from = datetime.datetime(2022, 2, 25)
    ts_to   = datetime.datetime(2022, 4, 18)
    supply_period_duration = 30
    MX001224 = MixergyModel(tank_config['ECC'])
    MX001224.populate(ts_from, ts_to, supply_period_duration)
    print(MX001224.H())
    print(MX001224.realworldE())
    # MX001389 = MixergyModel(tank_config['Nursery'])
    # MX001389.populate(ts_from, ts_to, supply_period_duration)
    # print(MX001389.H())
    # print(MX001389.realworldE())
    # print(MX001389.lossInSupplyPeriod(4))
