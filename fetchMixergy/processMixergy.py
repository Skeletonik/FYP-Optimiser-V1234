# I've just come back round to this, and it doesn't make sense
# Surely the idle tank losses are the same as the %SoC loss hidden by heating
# Because that's exactly what's happening?
# Possibly this issue is caused by the lack of flange. TBD

# %SoC gain hidden by heating process
HIDDEN_TANK_LOSSES = [-0.000364187823, -0.000809828852]
# SoC gained per kWh, for loop off/on
HEATING_TANK_GAIN  = [5.73558601, 5.988531764]
# Tank %SoC gains in idle tank (after compensating for heating) per second 
IDLE_TANK_LOSSES   = [-0.044015567/60, -0.111688958/60]

def tankLosses (delta_t, pumped_loop=True):
    """ Find effect of losses on idle tank
    delta_t: time passed within the period loss value is needed
    pumped_loop: state of the pumped loop at this time """
    # Model should be improved, this is just linearised in Excel
    # It's a function so it can be improved
    
    return IDLE_TANK_LOSSES[pumped_loop]*delta_t

def heatingGain (delta_t, energy, pumped_loop=True):
    """ Find effect of heating on delta_SoC, to allow compensation
    power: kWh input over minute
    pumped_loop: bool, is the pump on? """
    # Model should be improved, this is just linearised in Excel

    # Total losses hidden by heating are:
    #   ([+ve gain effect of heating (%/min)] -  [-ve real losses (%/min)])
    return HEATING_TANK_GAIN[pumped_loop]*energy - HIDDEN_TANK_LOSSES[pumped_loop]*delta_t

def parseUnixTime (time):
    """ Parse Unixtime to *time* object
    Should already be in seconds by this point 
    Just gives time within the day """
    from datetime import datetime
    unix_datetime = datetime.utcfromtimestamp(int(time))
    return datetime.time(unix_datetime)

def ifPumpedLoop (record_time):
    """ Determine whether the pumped loop is on
    Accepts a datetime object as input """
    from datetime import time
    # Convert the record_time from Unix int to datetime object
    record_time = parseUnixTime(record_time)
    # Pump operates 5am-6pm
    pump_on  = time(5, 0, 0)
    pump_off = time(18, 0, 0)
    # So work out if the pump is on
    if (pump_on <= record_time < pump_off):
        return True
    else: 
        return False


def findDeltas (mixergy_data):
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
        heating_adjusted = delta_charge - heatingGain(delta_t, energy, ifPumpedLoop(t['recordedTime']))
        effect_adjusted  = heating_adjusted - tankLosses(delta_t, ifPumpedLoop(t['recordedTime']))
        # effect_adjusted = effect_adjusted if effect_adjusted < 0 else 0

        # Pack it all up in a nice dict and append to system record
        processed_data.append({'delta_t': delta_t, 'delta_charge': delta_charge, 'energy':energy, 'heating_adjusted': heating_adjusted, 'effect_adjusted': effect_adjusted})
        # Update the previous record to this one
        prev = t
    
    return processed_data

def nMinuteBlocks (delta_data, n_minutes):
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

    return block_data

def processMixergy (mixergy_data):
    """ Take Mixergy API _content_ data, and return the heating- and loss-adjusted
    delta SoC (i.e. demand in terms of SoC) in 30min blocks, starting from the first point put in.
    Won't return incomplete 30min blocks"""

    # Make 30min blocks of delta SoC data
    returned = nMinuteBlocks(findDeltas(mixergy_data), 30)
    return returned


if __name__ == "__main__":
    # sledgehammer, walnut, we meet again
    import os, sys
    sys.path.append(os.path.relpath('.'))
    # pylint: disable=import-error
    
    from utilities import loadFromJSON
    mixergy_data = loadFromJSON('input_data/Mixergy-28Feb.json')['content']
    returned = processMixergy(mixergy_data)
    print(returned)

