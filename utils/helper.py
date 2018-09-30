import datetime

def hippid_date_parse(string):
    return datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%S.%f')

def timestr():
    dt = datetime.datetime.utcnow()
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')
