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

    def pvFromCSV (self, filename:str, date_from:date, date_to:date) -> list:
        from fetchPV import PVfromCSV
        return PVfromCSV.main(
            filename,
            date_from,
            date_to
        )

    def MixModel (self, filename:str, tank_name:str, date_from:date, date_to:date) -> list:
        from utilities import loadFromJSON
        from fetchMixergy import mixergyModel
        from utilities import datetimeify
        tank_config = loadFromJSON(filename)[tank_name]
        date_from = datetimeify(date_from)
        date_to = datetimeify(date_to)
        tank = mixergyModel.MixergyModel(tank_config)
        tank.populate(date_from, date_to, 30)
        return tank

    def DummyModel (self, tank_config):
        from fetchMixergy import mixergyModel
        tank = mixergyModel.DummyModel(tank_config)
        return tank

# Yes, I realise I have two confusingly named "source"s here

    def autoSelectSource (self, variable:dict, field:str):
        # Python docs officially reccommend using many ifs rather than a case statement...
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
        # Now we're out of ideas
        else:
            Exception("Unhandled data source: " + variable['source'])

    def autoFill (self):
        """ SYSTEM AUTO-ASSEMBLER v1
            Run all the functions necessary to assemble the system 
            """ 
        from utilities import datetimeify
        # We know exactly the variables we're looking for: I, X, G, H*tank
        # So let's tackle the fixed ones first
        # Why bother having the 'dataSources'? Just make included stuff self-replacing like H....
        config = self.config
        need_to_fetch = ['I', 'X', 'G', 'tanks'] 
        ix_cosourced     = True if config['I'] == config['X'] else False
        if ix_cosourced: need_to_fetch.remove('X')

        # We're going to fetch everything to a staging area, where we know what we fetched it for
        # This lets us handle the ix shared case more nicely
        system = {}
        for field in need_to_fetch:
            # Find dates and make them datetime objects
            # Makes life much prettier later
            for key in config[field]:
                if 'date' in key:
                    config[field][key] = datetimeify(config[field][key])
            system[field] = self.autoSelectSource(config[field], field)

        if ix_cosourced:
            if type(system['I']) == dict:
                system['X'] = system['I']['X']
                system['I'] = system['I']['I']
            elif type(system['I']) == list:
                # This is a case where import/export match. Not realistic; possible
                system['X'] = system['I']
            else:
                Exception("Unknown 'I' format")
            
        # Now we need to go through the tanks and source their data
        for tank in system['tanks']:
            this_tank = system['tanks'][tank]
            # Create a tank object for every tank
            if this_tank['source'] == "MixergyModel":
                system['tanks'][tank] = self.MixModel(this_tank['filename'], this_tank['tankname'], this_tank['date_from'], this_tank['date_to'])
            elif this_tank['source'] == "included":
                system['tanks'][tank] = self.DummyModel(this_tank['data'])
            else: 
                pass

            # Currently, can only be sourced direct from mixergy
            # system['tanks'][tank] = self.autoSelectSource(system['tanks'][tank]['H'], 'H')

        self.simulation_system = system

if __name__ == '__main__':
    pass
