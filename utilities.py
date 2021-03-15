def loadFromJSON (filename):
    import json
    with open(filename, 'r') as infile:
        return json.load(infile)

def saveAsJSON (filename, data):
    import json
    with open(filename, 'w') as outfile:
        json.dump(data, outfile)

def floatify (row:object, fields:list) -> object:
    """ make the fields specified in to floats"""
    for field in fields:
        row[field] = float(row[field])
    return row


if __name__ == "__main__":
    
    response = loadFromJSON('systemconfig.json')
    print(response)