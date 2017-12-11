
set_defaultroute('op0')
print (subprocess.check_output(['curl','ifconfig.co']))
print (subprocess.check_output(['host','cdn.netflix.com']))
print (subprocess.check_output(['traceroute','cdn.netflix.com']))
set_defaultroute('op1')
print (subprocess.check_output(['curl','ifconfig.co']))
print (subprocess.check_output(['host','cdn.netflix.com']))
print (subprocess.check_output(['traceroute','cdn.netflix.com']))


