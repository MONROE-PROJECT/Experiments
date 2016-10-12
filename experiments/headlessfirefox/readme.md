
# Experiment template
A template to show of some of the capabilities of the Monroe platform.

The experiment will download a url (file) over http/https/http2 using firefox(headless) over different operator.
If the operator is not available in the node the experiment will fail. 
The default values are (can be overridden by providing /monroe/config):
```
{
        # The following value are specific to the monroe platform
        "guid": "no.guid.in.config.file",  # Overridden by scheduler
        "nodeid": "no.nodeid.in.config.file",  # Overridden by scheduler
        "storage": 104857600,  # Overridden by scheduler
        "traffic": 104857600,  # Overridden by scheduler
        "script": "jonakarl/experiment-template",  # Overridden by scheduler
        "zmqport": "tcp://172.17.0.1:5556",
        "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
        "meta_grace": 120,  # Grace period to wait for interface metadata
        "exp_grace": 120,  # Grace period before killing experiment
        "meta_interval_check": 5,  # Interval to check if interface is up
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        # These values are specic for this experiment
        "operator": "Telenor SE",
}
```
The download will abort when either size OR time OR actual size of the "url" is
 downloaded.

All debug/error information will be printed on stdout
 depending on the "verbosity" variable.

## Overview of code structure
The experiment consists of one main process and two sub processes.
 1. One process listen to modem information
 3. One process executes the experiment
 4. The main process are managing the two processes above

### Information sharing between processes
The information are shared between the processes by two thread safe
datastructures (a python "Manager" object).
For modem information the latest metadata update (for the specified operator)
are stored in a dictionary.

### The Metadata (sub)process
The responsibility for this process is to:
 1. Listen to gps and modem messages sent on the ZeroMQ bus
 2. Update the shared datastructures

### The experiment (sub)process
The responsibility for this process is to:
 1. Get information from (read) the shared datastructures
 2. run the experiment
 3. save the result when finished


## Requirements

These directories and files must exist and be read/writable by the user/process
running the container:
 * /monroe/config (added by the scheduler in the nodes)
 * "resultdir" (from /monroe/config see defaults above)    



## Docker misc usage
 * List running containers
     * ```docker ps```
 * Debug shell
     * ```docker run -i -t --entrypoint bash --net=host template```
 * Normal execution with output to stdout
     * ```docker run -i -t --net=host template```
 * Attach running container (with shell)
    * ```docker exec -i -t [container runtime name] bash```
 * Get container logs (stderr and stdout)
    * ```docker logs [container runtime name]```

## Sample output
```
{"Web load time": 6475, "DataId": "MONROE.EXP.FIREFOX.HEADLESS.BROWSING", "SequenceNumber": 1, "PageSize": 434225, "DataVersion": 1, "url": "www.google.com", "Timestamp": 1476202962.729973, "NodeId": "fake.nodeid", "NumObjects": 14, "Objects": [{"url": "http://www.google.se/?gfe_rd=cr&ei=iGL7V66QCu_k8Aeo6KDwDg", "ObjectSize": 68899, "timings": {"receive": 0, "send": 0, "connect": 64, "dns": 0, "blocked": 0, "wait": 45}, "time": 109}, {"url": "https://www.google.se/?gfe_rd=cr&ei=iGL7V66QCu_k8Aeo6KDwDg&gws_rd=ssl", "ObjectSize": 68840, "timings": {"receive": 64, "send": 460, "connect": 29, "dns": 0, "blocked": 0, "wait": 126}, "time": 679}, {"url": "https://www.google.se/images/hpp/ic_wahlberg_product_core_48.png8.png", "ObjectSize": 2456, "timings": {"receive": 2, "send": 0, "connect": 1, "dns": 0, "blocked": 0, "wait": 61}, "time": 64}, {"url": "https://www.google.se/images/nav_logo242.png", "ObjectSize": 22275, "timings": {"receive": 35, "send": 0, "connect": 0, "dns": 0, "blocked": 0, "wait": 51}, "time": 86}, {"url": "https://consent.google.com/status?continue=https://www.google.se&pc=s&timestamp=1476092553", "ObjectSize": 929, "timings": {"receive": 0, "send": 1151, "connect": 31, "dns": 24, "blocked": 0, "wait": 59}, "time": 1265}, {"url": "https://www.google.se/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png", "ObjectSize": 6334, "timings": {"receive": 2, "send": 0, "connect": 1, "dns": 0, "blocked": 0, "wait": 51}, "time": 54}, {"url": "https://ssl.gstatic.com/gb/images/i1_1967ca6a.png", "ObjectSize": 8447, "timings": {"receive": 1, "send": 729, "connect": 31, "dns": 9, "blocked": 0, "wait": 96}, "time": 866}, {"url": "https://www.google.se/xjs/_/js/k=xjs.s.sv.njD84qgLUV4.O/m=sx,c,sb,cdos,cr,elog,hsm,jsa,r,qsm,j,p,d,csi/am=AIGSJEAB4v8hINxCsCAVYGAQ/rt=j/d=1/t=zcms/rs=ACT90oHyStYO7MDv_YQWfAAeLs12Fcq1cg", "ObjectSize": 136106, "timings": {"receive": 50, "send": 0, "connect": 1, "dns": 0, "blocked": 0, "wait": 28}, "time": 79}, {"url": "https://www.gstatic.com/og/_/js/k=og.og2.en_US.FmFN8wh_cXY.O/rt=j/m=def/exm=in,fot/d=1/ed=1/rs=AA2YrTu_EYZlbvQhiIp7k2ginJ2Q5mlCCw", "ObjectSize": 47705, "timings": {"receive": 27, "send": 118, "connect": 34, "dns": 3, "blocked": 0, "wait": 106}, "time": 288}, {"url": "https://apis.google.com/_/scs/abc-static/_/js/k=gapi.gapi.en.I_ZVJb_pzks.O/m=gapi_iframes,googleapis_client,plusone/rt=j/sv=1/d=1/ed=1/rs=AHpOoo8NNXa6ND5OamMO-moF9Aq-DewphA/cb=gapi.loaded_0", "ObjectSize": 48620, "timings": {"receive": 68, "send": 0, "connect": 139, "dns": 0, "blocked": 0, "wait": 28}, "time": 235}, {"url": "https://www.gstatic.com/inputtools/images/tia.png", "ObjectSize": 541, "timings": {"receive": 0, "send": 0, "connect": 0, "dns": 0, "blocked": 0, "wait": 35}, "time": 35}, {"url": "https://www.google.se/xjs/_/js/k=xjs.s.sv.njD84qgLUV4.O/m=sy39,sy49,em2,em1,sy51,em0,sy306,aa,abd,sy75,sy74,sy73,sy76,em14,async,erh,sy78,foot,fpe,idck,ipv6,sy120,sy166,lu,m,sf,vm,sy40,sy128,sy41,sy43,sy47,sy146,sy42,sy44,sy145,em7,em8,sy38,sy48,sy142,sy147,sy148,cbin,sy378,dgm,sy143,sy144,cbhb/am=AIGSJEAB4v8hINxCsCAVYGAQ/rt=j/d=0/t=zcms/rs=ACT90oHyStYO7MDv_YQWfAAeLs12Fcq1cg", "ObjectSize": 22571, "timings": {"receive": 13, "send": 0, "connect": 1, "dns": 0, "blocked": 0, "wait": 52}, "time": 66}, {"url": "https://www.google.se/gen_204?atyp=i&ct=&cad=&vet=10ahUKEwi-psGi-c_PAhXE_iwKHeIzAIgQsmQIDQ..s&ei=iWL7V_69JcT9swHi54DACA&zx=1476092558902", "ObjectSize": 251, "timings": {"receive": 0, "send": 0, "connect": 1, "dns": 0, "blocked": 0, "wait": 64}, "time": 65}, {"url": "https://www.google.se/gen_204?v=3&s=webhp&atyp=csi&ei=iWL7V_69JcT9swHi54DACA&imc=3&imn=3&imp=3&adh=&xjs=init.275.20.sb.212.p.25.foot.16.m.6.jsa.4&ima=0&rt=xjsls.236,prt.504,iml.1805,dcl.1001,xjses.3077,jraids.3412,jraide.3473,xjsee.3859,xjs.3860,ol.4638,aft.504,wsrt.2323,cst.29,dnst.43,rqst.190,rspt.64,rqstt.1508,unt.992,cstt.1019,dit.2827", "ObjectSize": 251, "timings": {"receive": 0, "send": 0, "connect": 1, "dns": 0, "blocked": 0, "wait": 61}, "time": 62}], "Operator": "3 SE", "Iccid": "8946071512360089472", "Guid": "no.guid.in.config.file"}
```
