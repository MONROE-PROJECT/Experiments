
import subprocess

def set_dns(interface):
    str = ""
    try:
        with open('/dns') as dnsfile:

            dnsdata = dnsfile.readlines()
            dnslist = [ x.strip() for x in dnsdata ]
            for item in dnslist:
                if interface in item:
                    str += item.split('@')[0].replace("server=",
"nameserver ")
                    str += "\n"
        with open("/etc/resolv.conf", "w") as f:
            f.write(str)
    except:
        print("Could not find DNS file")
    print str
    return str



def set_defaultroute(interface):

    # Find default routes of interfaces
    routes=subprocess.check_output(['ip','route','show','table','all']).splitlines()
    for route in routes:
        if route.startswith("default") and interface in route:
            
            try:
                print (subprocess.check_output(['ip','route','del','default']))
            except:
                # In case no default was set, just let it pass.
                pass

            # Reuse the info from the route output when setting the new default:
            # route="default via 172.18.1.1 dev op0 table 10000"
            # print route.split()[0:5]
            # ['default', 'via', '172.18.1.1', 'dev', 'op0']

            print (subprocess.check_output(['ip','route','add'] + route.split()[0:5]))
            return True

    return False

