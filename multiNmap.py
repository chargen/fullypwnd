#!/usr/bin/python
import subprocess
import multiprocessing
import Queue
import sys
import os
import re
import getopt
import csv
import migrate_exploits
from data_alchemy import *
from sqlalchemy import *
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError
from debug import Debug
from xml.etree.ElementTree import ElementTree

__author__ = 'Daniel Taualii'
__version__ = 0.1

# Global variables
#

usageMessage = '''
[*] Usage: %s <ip address/range> [-c THREADS] [--debug=LEVEL]" % sys.argv[0]
  This script is used to simultaneously execute nmap.
    -c NUM Defines the max number of concurrent instances
           of nmap
    --debug=NUM Defines the debug level of this program 
'''

validIPMessage = '''
Addresses must be 
  an addresses (ie 255.255.255.255)
  or
  address ranges (ie 255.255.255.201-254 or 123-124.125.125.95-125)
'''

rootMessage = '''
You must be root!
'''

base_files = {'xml_file': "results-nmap-A.xml",
            'results_file': "results.csv",
            'host_file': "host_info.csv"}
debug = Debug()
debug.level = 0

# Acceptable commandline arguments
#

options = ('c:d')
longOptions = ['debug-level=', 'no-cache', 'no-scan', 'update-exploits']

# if there isn't an argument fail gracefully
if len(sys.argv) < 2:
    print usageMessage
    sys.exit(1)

# Auxiliary functions
#

# store ip address/range
def validateRange(subnet):
    if debug.level > 0:
        debug.msg(subnet)

    validRange = False
    ipRange = subnet.split("-")
    lowRange = 0
    highRange = 0
    if len(ipRange) == 2:
        lowRange = ipRange[0]
        highRange = ipRange[1]

    if int(lowRange) < 255 and int(highRange) < 255 and int(lowRange) < int(highRange):
        validRange = True
    return validRange

def validateIP(ip):
    if debug.level > 0:
        debug.msg(ip)

    ipFound = False
    if (validateRange(ip[0]) or int(ip[0]) < 255) and (validateRange(ip[1]) or int(ip[1]) < 255) and (validateRange(ip[2]) or int(ip[2]) < 255) and (validateRange(ip[3]) or int(ip[3]) < 255):
        ipFound = True
    return ipFound

def enumerateIPs(ip):
    if debug.level > 0:
        debug.msg(ip)

    classARange = []
    classBRange = []
    classCRange = []
    classDRange = []       

    if len(ip[0].split("-")) == 2:
        classA = ip[0].split("-")
        classALow = classA[0]
        classAHigh = classA[1]
        classARange = range(int(classALow), int(classAHigh) + 1)
    else:
        classARange.append(int(ip[0]))

    if len(ip[1].split("-")) == 2:
        classB = ip[1].split("-")
        classBLow = classB[0]
        classBHigh = classB[1]
        classBRange = range(int(classBLow), int(classBHigh) + 1)
    else:
        classBRange.append(int(ip[1]))

    if len(ip[2].split("-")) == 2:
        classC = ip[2].split("-")
        classCLow = classC[0]
        classCHigh = classC[1]
        classCRange = range(int(classCLow), int(classCHigh) + 1)
    else:
        classCRange.append(int(ip[2]))

    if len(ip[3].split("-")) == 2:
        classD = ip[3].split("-")
        classDLow = classD[0]
        classDHigh = classD[1]
        classDRange = range(int(classDLow), int(classDHigh) + 1)
    else:
        classDRange.append(int(ip[3]))

    ips = []       

    for ipA in classARange:
        for ipB in classBRange:
            for ipC in classCRange:
                for ipD in classDRange:
                    ips.append(str(ipA) + "." + str(ipB) + "." + str(ipC) + "." + str(ipD))        

    return ips

def setup_files(ip):
    if debug.level > 0:
        debug.msg(ip)

    xml_path = "./" + ip + "/" + base_files['xml_file']
    results_path = "./" + ip + "/" + base_files['results_file']
    host_path = "./" + ip + "/" + base_files['host_file']
    created_files = {'xml_file': xml_path,
                    'results_file': results_path,
                    'host_file': host_path}
    
    return created_files

def store_nmap_host(host):
    if debug.level > 0:
        debug.msg(host)

    if 'addr' in host:
        addr = host['addr']
    else:
        addr = ""
    if 'state' in host:
        state = host['state']
    else:
        state = ""
    if 'reason' in host:
        reason = host['reason']
    else:
        reason = ""
    if 'hostname' in host:
        hostname = host['hostname']
    else:
        hostname = ""
    if 'type' in host:
        os_type = host['type']
    else:
        os_type = ""
    if 'vendor' in host:
        os_vendor = host['vendor']
    else:
        os_vendor = ""
    if 'os_family' in host:
        os_family = host['os_family']
    else:
        os_family = ""
    if 'os_gen' in host:
        os_gen = host['os_gen']
    else:
        os_gen = ""
    if 'osclass_accuracy' in host:
        osclass_accuracy = int(host['osclass_accuracy'])
    else:
        osclass_accuracy = int(0)
    if 'osmatch_name' in host:
        osmatch_name = host['osmatch_name']
    else:
        osmatch_name = ""
    if 'osmatch_accuracy' in host:
        osmatch_accuracy = int(host['osmatch_accuracy'])
    else:
        osmatch_accuracy = int(0)
    if 'uptime' in host:
        uptime = int(host['uptime'])
    else:
        uptime = int(0)
    if 'lastboot' in host:
        lastboot = host['lastboot']
    else:
        lastboot = ""
    if 'finished' in host:
        finished = host['finished']
    else:
        finished = "" 
    if 'elapsed' in host:
        elapsed = host['elapsed']
    else:
        elapsed = ""
    if 'fingerprint' in host:
        fingerprint = host['fingerprint']
    else:
        fingerprint = ""

    if (addr != None):
        try:
            host_record = Host(ip = addr, state = state, reason = reason, hostname = hostname, os_type = os_type, os_vendor = os_vendor, os_family = os_family, os_gen = os_gen, osclass_accuracy = osclass_accuracy, osmatch_name = osmatch_name, osmatch_accuracy = osmatch_accuracy, uptime = uptime, lastboot = lastboot, finished = finished, elapsed = elapsed, fingerprint = fingerprint)
            session.add(host_record)
            session.commit()
        except:
            debug.msg(host_record)
    else:
        print "Address:", addr, "or osclass:", osclass, "is blank. "

    return host_record

def store_nmap_host_services(services, host_record):
    if debug.level > 0:
        debug.msg(services)
        debug.msg(host_record)
    
    host_service = []

    if len(services) > 0:
        for service in services:
            if 'addr' in service:
                addr = service['addr']
            else:
                addr = ""
            if 'portid' in service:
                port_id = service['portid']
            else:
                port_id = 0
            if 'protocol' in service:
                protocol = service['protocol']
            else:
                protocol = ""
            if 'state' in service:
                state = service['state']
            else:
                state = ""
            if 'reason' in service:
                reason = service['reason']
            else:
                reason = ""
            if 'reason_ttl' in service:
                reason_ttl = service['reason_ttl']
            else:
                reason_ttl = 0
            if 'service_name' in service:
                service_name = service['service_name']
            else:
                service_name = ""
            if 'product' in service:
                product = service['product']
            else:
                product = ""
            if 'version' in service:
                version = service['version']
            else:
                version = ""
            if 'extrainfo' in service:
                extrainfo = service['extrainfo']
            else:
                extrainfo = ""
            if 'ostype' in service:
                ostype = service['ostype']
            else:
                ostype = ""
            if 'method' in service:
                method = service['method']
            else:
                method = ""
            if 'conf' in service:
                conf = service['conf']
            else:
                conf = 0

            if port_id != None and port_id != "" and addr != None:
                port_id = int(port_id)
                reason_ttl = int(reason_ttl)
                conf = int(conf)
                try:
                    session.query(Host_service).filter(Host_service.ip == addr).filter(Host_service.port_id == port_id).delete()
                    host_service = Host_service(ip = addr, port_id = port_id, protocol = protocol, state = state, reason = reason, reason_ttl = reason_ttl, service_name = service_name, product = product, version = version, extrainfo = extrainfo, ostype = ostype, method = method, conf = conf)
                    host_record.host_service.append(host_service)
                    session.add(host_record)
                    session.commit()
                except Exception as e:
                    debug.msg(e)
                    debug.msg("[*] Error adding host service. ")
                    session.rollback()
            else:
                debug.msg("port and/or addr missing.")
            
    return host_service

def store_nmap_service_script(scripts, host_service_record):
    if debug.level > 0:
        debug.msg(scripts)
        debug.msg(host_service_record)

    if len(scripts) > 0:
        service_scripts = []
        for script in scripts:
            if 'addr' in script:
                addr = script['addr']
            else:
                addr = ""
            if 'portid' in script:
                port_id = int(script['portid'])
            else:
                port_id = int(0)
            if 'protocol' in script:
                protocol = script['protocol']
            else:
                protocol = ""
            if 'service_name' in script:
                service_name = script['service_name']
            else:
                service_name = ""
            if 'script_id' in script:
                script_id = script['script_id']
            else:
                script_id = ""
            if 'script_output' in script:
                script_output = script['script_output']
            else:
                script_output = ""
            
            if addr != None and port_id != None and protocol != None and script_id != None and script_output != None:
                try:
                    session.query(Service_script).filter(and_(Service_script.ip == addr, Service_script.port_id == port_id)).delete()

                    service_script = Service_script(ip = addr, port_id = port_id, protocol = protocol, service_name = service_name, script_id = script_id, script_output = script_output)
                    host_service_record.service_script.append(service_script)
                    session.add(host_service_record)
                    session.commit()

                except Exception as e:
                    print "[*] Error adding service script. "
                    debug.msg(e)
            else:
                print "Required parameters for store_nmap_service_script not found. "

    return

def parse_nmap_xml(nmap_xml):
    if debug.level > 0:
        debug.msg(nmap_xml)
        for node in nmap_xml:
            for subnode in node:
                print node
                print "  ", subnode


    nmap_host = {}
    host_services = []
    hostscript_tmp = {}
    hostscripts = []
    port_script = []
    host = nmap_xml.find('host')
    if host != None:
        host_status = host.find('status')
        if host_status != None:
            nmap_host['state'] = host_status.get('state')
            nmap_host['reason'] = host_status.get('reason')
            
        host_address = host.find('address')
        if host_address != None:
            nmap_host['addr'] = host_address.get('addr')
        
        hostnames = host.find('hostnames')
        if hostnames != None:
            for hostname in hostnames:
                nmap_host['hostname'] = hostname.get('name')
        
        osclass = host.find('os/osclass')
        if osclass != None:
            nmap_host['type'] = osclass.get('type')
            nmap_host['vendor'] = osclass.get('vendor')
            nmap_host['os_family'] = osclass.get('osfamily')
            nmap_host['os_gen'] = osclass.get('osgen')
            nmap_host['osclass_accuracy'] = osclass.get('accuracy')

        osmatch = host.find('os/osmatch')
        if osmatch != None:
            nmap_host['osmatch_name'] = osmatch.get('name')
            nmap_host['osmatch_accuracy'] = osmatch.get('accuracy')
        else:
            nmap_host['osmatch_name'] = ""
            nmap_host['osmatch_accuracy'] = 0

        osfingerprint = host.find('os/osfingerprint')
        if osfingerprint != None:
            nmap_host['osfingerprint'] = osfingerprint.get('fingerprint')
        else:
            nmap_host['osfingerprint'] = ""

        uptime = host.find('uptime')
        if uptime != None:
            nmap_host['uptime'] = uptime.get('seconds')
            nmap_host['lastboot'] = uptime.get('lastboot')
        
        finished = nmap_xml.find('runstats/finished')
        if finished != None:
            nmap_host['finished'] = finished.get('timestr')
            nmap_host['elapsed'] = finished.get('elapsed')
        
        hostscripts = host.find('hostscript')
        if hostscripts != None:
            for hostscript in hostscripts:
                hostscript_tmp['hostscript_id'] = hostscript.get('id')
        
        port_nodes = host.findall('ports/port')
        if port_nodes != None:
            for port in port_nodes:
                port_tmp = {}
                
                # port information
                port_tmp['addr'] = nmap_host['addr']
                port_tmp['portid'] = port.get('portid')
                port_tmp['protocol'] = port.get('protocol')
    
                # state information
                port_tmp['state'] = port.find('state').get('state')
                port_tmp['reason'] = port.find('state').get('reason')
                port_tmp['reason_ttl'] = port.find('state').get('reason_ttl')
                
                # service information
                service = port.find('service')
                if service != None:
                    port_tmp['service_name'] = service.get('name')
                    port_tmp['product'] = service.get('product')
                    port_tmp['version'] = service.get('version')
                    port_tmp['extrainfo'] = service.get('extrainfo')
                    port_tmp['ostype'] = service.get('ostype')
                    port_tmp['method'] = service.get('method')
                    port_tmp['conf'] = service.get('conf')
                
                # script information
                script_nodes = port.findall('script')

                for script in script_nodes:
                    script_tmp = {}
                    if script != None:
                        script_tmp['addr'] = nmap_host['addr']
                        script_tmp['portid'] = port_tmp['portid']
                        script_tmp['protocol'] = port_tmp['protocol']
                        script_tmp['service_name'] = port_tmp['service_name']
                        script_tmp['script_id'] = script.get('id')
                        script_tmp['script_output'] = script.get('output')
                        port_script.append(script_tmp)
            
                
                port_tmp['scripts'] = port_script
                host_services.append(port_tmp)
                     
        return nmap_host, host_services, port_script

# TODO This could pass command line arguments to nmap
def callNmap(ip):
    if debug.level > 0:
        debug.msg(ip)

    if not os.path.isdir("./" + ip):
        os.mkdir("./" + ip)

    output_files = setup_files(ip)
    #subprocess.call(["nmap", "-PN", "-v", "-oX", output_files['xml_file'], "-A", ip])
    #subprocess.call(["nmap", "-p22", "-oX", output_files['xml_file'], "-sV", ip])
    subprocess.call(["nmap", "-p1-65535", "-v", "-oX", output_files['xml_file'], "-A", ip])
    elementtree = ElementTree()
    nmap_xml = elementtree.parse(open(output_files['xml_file']))
    nmap_host, host_services, port_script = parse_nmap_xml(nmap_xml)
    
     
    host_record = store_nmap_host(nmap_host)
    host_service_record = store_nmap_host_services(host_services, host_record)
    store_nmap_service_script(port_script, host_service_record)

def exploit_service(service_exploit):
    if debug.level > 0:
        debug.msg(service_exploit)

    session = Session(bind = engine)
    session.add(service_exploit)
    exploit_path = service_exploit.exploit_path.encode('ascii', 'ignore')
    exploit_parameters = [] 
    try:
        if os.path.exists(exploit_path):
            filename, extension = os.path.basename(exploit_path).split(".")
            if extension == "py":
                exploit_parameters.append(sys.executable)
            exploit_parameters.append(exploit_path)
            exploit_parameters.append(ip)
            exploit_log = str(exploit_parameters)
            exploit_output = subprocess.Popen(exploit_parameters, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            exploit_log = exploit_log + exploit_output.communicate()[0]
            if debug.level > 0:
                debug.msg(exploit_log)
            service_exploit.exploit_log = exploit_log

    except Exception as e:
        debug.msg(e)

    return exploit_log


def query_exploits(host_service_extended):
    if debug.level > 0:
        debug.msg(host_service_extended)
    
    service_exploits_all = []
    service_aliases = []
    exploit_parameters = []
    session = Session(bind = engine)
    session.add(host_service_extended)
    os_family = host_service_extended.os_family
    service_name = host_service_extended.service_name
    #os_family = "Windows"
    #service_name = "smb"
    ip = host_service_extended.ip
    port_id = host_service_extended.port_id

    try:
        #print "os_family: " + os_family + "\n service_name: " + service_name
        """ This next few lines will find the service used by nmap, map it to a service,
            then use the nmap name as the service.  This is to allow for aliases.  There
            is a more efficient way, but I don't have the time to work on that right now.
        """
        nmap_aliases = session.query(Nmap_service_alias.service_alias).filter(Nmap_service_alias.nmap_service == service_name)
        #print nmap_aliases.all()
        service_names = session.query(Service_exploit.service_name).filter(Service_exploit.service_name == service_name)
        nmap_set = set(nmap_aliases)
        service_set = set(service_names)
        #services = OrderedSet(nmap_aliases.union(service_names))
        services = nmap_set | service_set 
        #print services
        """ This loops through the services and finds the associated exploits. """
        for service in services:
            if service[0] is not None:
                exploit_paths = session.query(Service_exploit.exploit_path).join(Exploit).filter(and_(Service_exploit.os_family == os_family, Service_exploit.service_name == str(service[0]))).all()
                for exploit_paths in exploit_paths:
                    service_exploits_all.append(str(exploit_paths[0]))
            #if len(service_exploits_all) > 0:
            #    exploit_parameters = session.query(Exploit_parameter).filter(Exploit_parameter.exploit_sha1.match(service_exploits[0].exploit_sha1)).all()
            #    print exploit_parameters
    except Exception as e:
        debug.msg(e)

    #print set(service_exploits_all)
    return service_exploits_all

def update_exploits():
    if debug.level > 0:
        debug.msg()
    migrate_exploits.main()

def remove_cache(ipList):
    if debug.level > 0:
        debug.msg(ipList)

    print "[*] Removing files for previously scanned IPs."
    
    for ip in ipList:
        host = session.query(Host).filter(Host.ip == ip).delete()

def run_once_ip_list(ipList):
    if debug.level > 0:
        debug.msg(ipList)

    returnValue = False

    for ip in ipList:
        try:
            host = session.query(Host).filter(Host.ip == ip).all()
            if len(host) > 0:
                print "This ip", ip, "has already been scanned."
                print "  If you want to perform a fresh scan use --no-cache"
                ipList.remove(ip)
        except Exception as e:
            debug.msg(e)
            
    return returnValue

def get_osmatch(host_file):
    if debug.level > 0:
        debug.msg(host_file)

    os_match = None
    csv_reader = csv.DictReader(open(host_file, "r"))
    for line in csv_reader:
        if line['osmatch'] == "":
            os_match = find_osmatch(line)
        else:
            os_match = line['osmatch']

    return os_match

def main():	
    if debug.level > 0:
        debug.msg()

    processCount = multiprocessing.cpu_count()
    print sys.argv[1:]
    flags, other = getopt.getopt(sys.argv[1:], options, longOptions)
    run_scan = True
    find_exploits = True
    parse_ip = True
    use_cache = True

    for flag, value in flags:
        if flag in ('-c'):
            if int(value) < processCount * 1000:
                processCount = int(value)
        elif flag in ('--no-cache'):
            use_cache = False
        elif flag in ('--no-scan'):
            run_scan = False
        elif flag in ('--debug-level'):
            debug.level = value
        elif flag in ('--update-exploits'):
            update_exploits()
            run_scan = False
            find_exploits = False
            parse_ip = False
	else:
            print usageMessage
            sys.exit(1)
    
    if parse_ip:
        # TODO This could use an elif checking for valid domain name as well
        if len(other[0].split(".")) == 4:
            ip = other[0].split(".")	
            if validateIP(ip): 
                ipList = enumerateIPs(ip)
            else:
                print validIPMessage
        else:
            print validIPMessage
        if use_cache == False:
            remove_cache(ipList)

    if run_scan:
        #remove_cache(ipList)
        run_once_ip_list(ipList)

        if len(ipList) > 0:

            if len(ipList) < processCount:
                processCount = len(ipList)

            try:
                pool = multiprocessing.Pool(processes=processCount)
                nmap_results = pool.map_async(callNmap, ipList).get(99999999)

                print "Finished calling nmap."

            except KeyboardInterrupt:
                print "Quitting!"
                sys.exit(1)
    
    if find_exploits:
        session_exploits = Session(bind = engine)
        try:
            if len(ipList) > 0:
                host_services_extended = session_exploits.query(Host_service_extended).filter(Host_service_extended.ip.in_(ipList)).all()
                if debug.level > 0:
                    debug.msg(host_services_extended)

                found_exploits = []
                if len(host_services_extended) > 0:
                    pool = multiprocessing.Pool(processes = processCount)
                    service_exploits = pool.map_async(query_exploits, host_services_extended).get(99999999999)
                    
                    """ This is used to clean up the data.  I need a unique list of data without blank sets """
                    service_exploits_set = set()
                    for service_exploit_list in service_exploits:
                        service_exploits_set = service_exploits_set | set(service_exploit_list)
                    
                    if len(service_exploits_set) > 0:
                        
                        print "[*] %d exploits found:" % len(service_exploits_set)
                        for service_exploit in service_exploits_set:
                            found_exploits.append(service_exploit)
                            print service_exploit
                    
                    else:
                        print "Sorry, no exploits found.  :("

        except ProgrammingError as e:
            debug.msg(e)

if __name__ == "__main__":
    if os.getuid() == 0:
        main()
    else:
        print rootMessage
        sys.exit(1)
