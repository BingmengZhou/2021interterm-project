result = {
    "message":None,
    "success":False,
    "details":None
}

def removeEmpty(data):
    data2 = {}
    for o in data:
        if not data[o]== '':
            data2[o] = data[o]
    return data2