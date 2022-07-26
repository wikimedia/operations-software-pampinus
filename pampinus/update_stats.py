import datetime
import requests
import sys

PROM_ENDPOINT = 'https://thanos-query.discovery.wmnet' + '/api/v1/query'


def get_instance(result):
    prometheus_instance = result.get('metric', {}).get('instance', '').split(':')
    instance_host = '-'.join(prometheus_instance[:-1])
    prometheus_port = int(prometheus_instance[-1])
    instance_port = 3306 if prometheus_port == 9104 else prometheus_port - 10000
    instance = (str(instance_host)
                if instance_port == 3306
                else ':'.join([instance_host, str(instance_port)]))
    return instance


def get_host(result):
    return result.get('metric', {}).get('instance', '').split(':')[0]


def query(metric):
    response = requests.get(PROM_ENDPOINT, params={'query': metric})
    results = response.json()
    if results.get('status', 'error') != 'success':
        print('ERROR: Query failed')
        sys.exit(-1)
    return results


results = query('mysql_version_info')
data = dict()
for result in results.get('data', {}).get('result', []):
    instance = get_instance(result)
    version = result.get('metric', {}).get('version', '').split('-')[0]
    data[instance] = {'version': version}

results = query('timestamp(mysql_global_status_uptime) - mysql_global_status_uptime')
for result in results.get('data', {}).get('result', []):
    instance = get_instance(result)
    last_start = datetime.datetime.fromtimestamp(float(result.get('value')[1]))
    if instance not in data:
        data[instance] = {}
    data[instance]['last_start'] = last_start

results = query('mysql_up')
for result in results.get('data', {}).get('result', []):
    instance = get_instance(result)
    up = result.get('value')[1] == "1"
    if instance not in data:
        data[instance] = {}
    data[instance]['up'] = up

for key, instance in data.items():
    if instance.get('version'):
        print(f"UPDATE instances SET version='{instance['version']}' WHERE name='{key}';")

# results = query('timestamp(node_time_seconds{cluster="mysql"}) -
#                  node_time_seconds{cluster="mysql"}')
# for result in results.get('data', {}).get('result', []):
#     host = get_host(result)
#     last_boot = datetime.datetime.fromtimestamp(float(result.get('value')[1] ))
