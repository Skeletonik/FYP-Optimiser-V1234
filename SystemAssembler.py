from datetime import date
class SystemAssembler:
    """ SYSTEM ASSEMBLER v1
        Take a systemconfig object with instructions on assembly. Either autoassemble 
        it, or provide the tools to do so manually
    """
    def __init__ (self, system_config:object):
        # Honestly, not 100% I want to take that by default
        self.config = system_config

    def system (self):
        """ Returns the current system config """
        return self.simulation_system

    def included (self, source:str) -> object:
        # Return an object with one key
        # var_name: [values]
        return source['data']

    def fromJson (self, var_name:str, filename:str) -> list:
        from utilities import loadFromJSON
        # Return an object with one key
        # var_name: [values]
        # But make sure it's only the right one, for now
        return loadFromJSON(filename)[var_name]

    def ljFromRest (self, date_from:date, date_to:date) -> object:
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

    def ljFromCsv (self, filename:str, date_from:date, date_to:date) -> object: # list:
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

# Yes, I realise I have two confusingly named "source"s here

    def autoSelectSource (self, source:object, field:str):
        # Python docs officially reccommend using many ifs rather than a case statement...
        if   source['source'] == "included":
            return self.included(source)
        elif source['source'] == "JSON":
            return self.fromJson(field, source['filename'])
        elif source['source'] == "LJ_REST":
            return self.ljFromRest(source['date_from'], source['date_to'])
        elif source['source'] == "LJ_CSV":
            return self.ljFromCsv(source['filename'], source['date_from'], source['date_to'])
        elif source['source'] == "PV_CSV":
            return self.pvFromCSV(source['filename'], source['date_from'], source['date_to'])
        # Now we're out of ideas
        else:
            Exception("Unhandled data source: " + source['source'])

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
        # De-mingle cosourced data. I is always the one sourced
        if ix_cosourced:
            system['X'] = system['I']['X']
            system['I'] = system['I']['I']
            
        # Now we need to go through the tanks and source their data
        for tank in system['tanks']:
            # H is a placeholder of similar format to above, but in situ
            # So we need to replace it
            system['tanks'][tank]['H'] = self.autoSelectSource(system['tanks'][tank]['H'], 'H')

        self.simulation_system = system