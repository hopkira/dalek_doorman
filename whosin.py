import sys
import scapy.all as scapy
import time
from tqdm import tqdm
import dalek_db as db

def get_ip_list(ip,interface,ip_range):
    '''Returns a list of IP addresses

    Keyword arguments:
    ip -- the base ip address
    interface -- the name of the interface (from ifconfig)
    ip_range -- the nummber of IP addresses to scan from the base
    '''
    ip_addresses = []
    for n in range(1, ip_range+1):
        eval_ip = ".".join( ip.split('.')[:-1] ) + '.' + str(n)
        ip_addresses.append( eval_ip )
    return ip_addresses

def scan_ip_list(ip_addresses):
    '''Uses scapy to issue ARP broadcasts aimed at each IP in turn and return a list of active MAC/IP addresses

    ip_addresses -- a list of ip addresses
    '''
    clients_list=[]
    for ip in tqdm(ip_addresses,desc=' Scanning network ',unit='IP'):
        arp_request = scapy.ARP(pdst=ip)
        broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast/arp_request
        answered_list = scapy.srp(arp_request_broadcast,timeout=1,verbose=False)[0]
        for element in answered_list:
            client_dict = {"ip":element[1].psrc,"mac":element[1].hwsrc}
            clients_list.append(client_dict)
    return clients_list

def device_detected_doc(doc,detected_time):
    '''Records the time the device was detected and that the user is in the house in Cloudant 
    
    doc -- the Cloudant document to be updated (one per device/user)
    detected_time -- the time (in time.time() format) that the device was detected
    '''
    try:
        db.update_doc(doc,"device_detected",detected_time)
        db.update_doc(doc,"in_house",True)
        db.save_doc(doc)
    except:
        print("ERROR: Could not update device_detected and in_house status")

def out_of_house_doc(doc):
    '''Records that the user is out of the house in Cloudant

    doc -- the Cloudant document to be updated
    '''
    try:
        db.update_doc(doc,"in_house",False)
        db.save_doc(doc)
    except:
        print("ERROR: Could not update in_house status")

def who_is_in(active_devices):
    '''Returns a list of people in the house and maintains their status in Cloudant

    active_devices -- a list of active device objects fro the scan
    '''
    whosin = []
    time_now = round(time.time())
    for known_address in known_address_list: # loop through the list of known devices
        match = False # records whether the active device is a known device
        for device in active_devices: # loop through the list of active IP/MAC addresses
            # compares the active device mac address against the known mac addresses
            if str(device['mac']) == str(known_address['mac']):
                match = True
                # retrieve a Cloudant document using the name of the user as the _id
                doc_to_update = db.read_doc(my_db,known_address['_id'])
                # update the document to record that the device has just been seen
                device_detected_doc(doc_to_update,time_now)
                # add the name to the list of people and notify user
                whosin.append(known_address['_id'])
                print(known_address['_id'] + "s phone is detected!")
        # the known device is not in the list of active devices
        if not match:
            # calculate how long it is since the device was last seen and notify user
            time_not_seen = round(time_now - known_address['device_detected'])
            print(known_address['_id'] + "s phone not seen for " + str(time_not_seen) + " seconds.")
            doc_to_update = db.read_doc(my_db,known_address['_id'])
            # if the device has not been detected for roughly 16 minues then tell Cloudant they are out of the house
            if ((time_not_seen > 1000) and (doc_to_update['in_house'] == True)):
                out_of_house_doc(doc_to_update) 
    # return list of known devices that were detected
    return whosin

def main():
    try:
        while True:
            # identify the MAC/IP of all the active devices on the network
            active_devices = scan_ip_list(ip_list)
            # identify the known devices from the list of active devices
            whos_in = who_is_in(active_devices)
    except KeyboardInterrupt:
        print("CTRL+C pressed. Exiting. ")
        sys.exit(0)

# connect to the Cloudant "dalek" database
my_connection = db.get_connection()
my_db = db.db_read(my_connection,"dalek")
# set up the parameters for the scan
ip = "192.168.XXX.XXX" # replace with your network IP
interface = "XXXXX" # replace with your wireless card interface
ip_range = nnn # replaxe with the number of IPs to scan
# retrieve the known device details from Cloudant and store them in the known_address_list
known_address_list = []
doc_list=["person1", "person2", "person3"]
for doc in doc_list:
    known_address_list.append(db.read_doc(my_db,doc))
# generate the ip address list to scan
ip_list = get_ip_list(ip=ip,interface=interface,ip_range=ip_range)

if __name__ == '__main__':
    main()
