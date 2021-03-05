from getData import loadFromJSON
from optimizer import main 

# Load the default config
system = loadFromJSON('systemconfig.json')
system = {**system, **loadFromJSON('rates.json')}

system['tanks']['ECC'] = {**system['tanks']['ECC'], **loadFromJSON('dhw_ECC.json')}
system['tanks']['Nursery'] = {**system['tanks']['ECC'], **loadFromJSON('dhw_nursery.json')}

response = main(system)
print(response)
