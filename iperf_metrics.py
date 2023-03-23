# Script to run iperf3 test to measure bandwidth to remote site.
# Runs in reverse mode to measure both ingress and egress bandwidth
# Sends avg bandwidth metric to ELK stack 
import time
from datadog import initialize, statsd
import time
import iperf3
import os
from elasticsearch import Elasticsearch
from  datetime import datetime
import pytz


local_tz = pytz.timezone('Europe/Paris')
device_name = "device8"

es = Elasticsearch("http://192.168.122.1:9200")
try :
 print(es.info().body)
except : 
	print("enable to connect to elasticsearch")
	print("Please Re-check elasticsearch IP addr")
# Set vars
# Remote iperf server IP
remote_site = '10.2.3.4'

# How long to run iperf3 test in seconds
test_duration = 20


# Set Iperf Client Options
# Run 10 parallel streams on port 5201 for duration w/ reverse
client = iperf3.Client()
client.server_hostname = remote_site
client.zerocopy = True
client.verbose = False
client.reverse = True
client.port = 5201
client.num_streams = 10
client.interval = 5
client.duration = int(test_duration)
client.bandwidth = 1000000000


mappings = {
                "properties": {
                "timestamp": {"type": 'date'},
                "bandwidth": {"type": 'float', 'format' : "yyyy-MM-dd HH:mm:ss"}
                        }
                }

try : 
        print("Creating new index" + str(device_name))
        es.indices.create(index= device_name, mappings=mappings)
except : print("index already exist")

#result = client.run()
#iperf_data = result.json
total_bandwidth_usage = []
timestamps = []

c = 0
while True:
	result = client.run()
	iperf_data = result.json	
#	print(result.json) 
	if c == client.duration * 2 :
                
		break
	else:
                c = c + client.duration
	# Extract the relevant information from the intervals section
	try :
		intervals_data = iperf_data['intervals']
	except :  print(iperf_data)
	id =30
	for interval in intervals_data:
#		print(interval)
		sent_bps = interval['sum']['bits_per_second']
		sent_kbps = sent_bps / 1000
		sent_Mbps = sent_kbps / 1000
		total_bandwidth_usage.append(sent_Mbps)
		timestamps.append(interval['sum']['start'])
		doc = {
        	'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        	'bandwidth': sent_Mbps}

		print(es.index(index= device_name , document=doc))
		id = id + 1


#    if result:
#        for interval_result in result.intervals:
#            time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(interval_result.start))
#            bandwidth = round(interval_result.bps / 1000000, 2)  # in Mbps
#            print(f'{time_stamp}\t{bandwidth} Mbps')
#    if result and result.error:
#        print(result.error)
#        break

	time.sleep(client.duration+5)
	


print("Bandwidth Usage: ", total_bandwidth_usage)
print("Timestamps: ", timestamps)
