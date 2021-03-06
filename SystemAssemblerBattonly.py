from datetime import date
class SystemAssembler:
    """ SYSTEM ASSEMBLER v1
        Take a systemconfig dict with instructions on assembly. Either autoassemble
        it, or provide the tools to do so manually
    """
    def __init__ (self, system_config:dict):
        self.config = system_config

    def system (self):
        """ Returns the current system config """
        return self.simulation_system

    def included (self, source:str) -> dict:
        # Return a dict with one key
        # var_name: [values]
        return source['data']

    def fromJson (self, var_name:str, filename:str) -> list:
        from utilities import loadFromJSON
        # Return a dict with one key
        # var_name: [values]
        # But make sure it's only the right one, for now
        return loadFromJSON(filename)[var_name]

    def ljFromRest (self, date_from:date, date_to:date) -> list:
        """ Currently redundant """
        from fetchLJ import lj_rest
        # grab the APX data, divide by 10 for p/kWh
        # getAPX provides {date, price (£/MWh)}
        # £/MWh -> p/kWh = 1/10
        return [ x[1]/10 for x in
                    lj_rest.getAPX(
                        date_from,
                        date_to
                    ) if (date_from <= x[0] < date_to)
                ]

    def ljFromCsv (self, filename:str, date_from:date, date_to:date) -> dict:
        # This function is unique, it's the only one which returns I and X in an obj
        # Thus an obj...
        # However, that is in no small part because I haven't finished REST
        # Realistically, I and X will always come together
        # Maybe I should be more Agile and just do that...
        from fetchLJ import LJfromCSV
        return LJfromCSV.main(
            filename,
            date_from,
            date_to
        )

    def ciFromRest (self, date_from:date, date_to:date, postcode) -> list:
        from fetchCI import CI_rest
        import datetime
        # T: get carbon intensity
        # x = CI_rest.getCI('2022-03-20T12:00Z', '2022-03-21T12:00Z', 'BS5')
        # Changing date_to to load the same number of data points as all other sources
        date_to_48 = date_to - datetime.timedelta(minutes=1)
        # Run the main CI rest function - changing the dates to the right format - maybe not working idk?
        response = CI_rest.getCI(date_from.strftime("%Y-%m-%dT%H:%MZ"), date_to_48.strftime("%Y-%m-%dT%H:%MZ"), postcode)

        return response

    def pvFromCSV (self, filename:str, date_from:date, date_to:date) -> list:
        from fetchPV import PVfromCSV
        return PVfromCSV.main(
            filename,
            date_from,
            date_to
        )

    def smFromCsv (self, filename:str, date_from:date, date_to:date) -> list:
        from fetchSM import SMfromCSV
        return SMfromCSV.main(
            filename,
            date_from,
            date_to
        )

    def MixModel (self, filename:str, tank_name:str, date_from:date, date_to:date) -> list:
        from utilities import loadFromJSON
        import mixergyModel
        from utilities import datetimeify
        tank_config = loadFromJSON(filename)[tank_name]
        tank = mixergyModel.MixergyModel(tank_config)
        tank.populate(date_from, date_to, 30)
        return tank

    def DummyModel (self, tank_config):
        import mixergyModel
        tank = mixergyModel.MixergyModel(tank_config)
        return tank

# Yes, I realise I have two confusingly named "source"s here

    def autoSelectSource (self, variable:dict, field:str):
        # Python docs officially recommend using many ifs rather than a case statement...
        if   variable['source'] == "included":
            return self.included(variable)
        # JSON loading of H is currently broken. 
        # Isn't a tank object
        elif variable['source'] == "JSON":
            return self.fromJson(field, variable['filename'])
        elif variable['source'] == "LJ_REST":
            return self.ljFromRest(variable['date_from'], variable['date_to'])
        elif variable['source'] == "LJ_CSV":
            return self.ljFromCsv(variable['filename'], variable['date_from'], variable['date_to'])
        elif variable['source'] == "PV_CSV":
            return self.pvFromCSV(variable['filename'], variable['date_from'], variable['date_to'])
        elif variable['source'] == "CI_REST":
            return self.ciFromRest(variable['date_from'], variable['date_to'], variable['postcode'])
        elif variable['source'] == "SM_CSV":
            return self.smFromCsv(variable['filename'], variable['date_from'], variable['date_to'])
        # Now we're out of ideas
        else:
            Exception("Unhandled data source: " + variable['source'])

    def autoFill (self):
        """ SYSTEM AUTO-ASSEMBLER v1
            Run all the functions necessary to assemble the system 
            """
        from utilities import datetimeify
        from datetime import timedelta
        # We know exactly the variables we're looking for: I, X, G, H*tank
        # So let's tackle the fixed ones first
        # Why bother having the 'dataSources'? Just make included stuff self-replacing like H....
        config = self.config
        need_to_fetch = ['I', 'X', 'G', 'E', 'SM']
        ix_cosourced     = True if config['I'] == config['X'] else False
        if ix_cosourced: need_to_fetch.remove('X')

        # We're going to fetch everything to a staging area, where we know what we fetched it for
        # This lets us handle the ix shared case more nicely
        system = {}
        for field in need_to_fetch:
            # Find dates and make them datetime objects
            # Makes life much prettier later
            if 'date_from' in config[field]:
                config[field]['date_from'] = datetimeify(config[field]['date_from'])
                config[field]['date_to']   = config[field]['date_from'] + timedelta(hours = config['optimization_duration'])
            # for key in config[field]:
            #     if 'date' in key:
            #         config[field][key] = datetimeify(config[field][key])
            system[field] = self.autoSelectSource(config[field], field)

        # What happens if ix_cosourced=false but I is an object? - TBD
        if ix_cosourced:
            if type(system['I']) == dict:
                system['X'] = system['I']['X']
                system['paidX'] = system['I']['paidX']
                system['paidI'] = system['I']['paidI']
                system['I'] = system['I']['I']
            elif type(system['I']) == list:
                # This is a case where import/export match. Not realistic; possible
                system['X'] = system['I']
            else:
                Exception("Unknown 'I' format")

        # Now we need to go through the tanks and source their data
        """
        for tank in system['tanks']:
            system['tanks'][tank]['date_from'] = datetimeify(system['tanks'][tank]['date_from'])
            system['tanks'][tank]['date_to']   = system['tanks'][tank]['date_from'] + timedelta(hours = config['optimization_duration'])
            this_tank = system['tanks'][tank]
            # Create a tank object for every tank
            if this_tank['source'] == "MixergyModel":
                system['tanks'][tank] = self.MixModel(this_tank['filename'], this_tank['tankname'], this_tank['date_from'], this_tank['date_to'])
            elif this_tank['source'] == "included":
                system['tanks'][tank] = self.DummyModel(this_tank['data'])
            else:
                pass
                """
        # T: print(system['E']) works...
        # T: simply load Carbon Price ( CP )
        system['CP'] = config['carbon_price']
            # Currently, can only be sourced direct from mixergy
            # system['tanks'][tank] = self.autoSelectSource(system['tanks'][tank]['H'], 'H')

        self.simulation_system = system
        # print(system)
if __name__ == '__main__':
    pass
