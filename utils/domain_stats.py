from os import listdir
from os.path import join
from os.path import isfile
from os.path import isdir
import json
import numpy as np

def get_domains(folder):
    domains = []
    for dname in [f for f in listdir(folder) if isdir(join(folder, f))]:
        domain = {}
        domain["name"] = dname
        with open(join(folder, dname, "profileA.json"), 'r') as file:
            domain["profileA"] = json.load(file)
        with open(join(folder, dname, "profileB.json"), 'r') as file:
            domain["profileB"] = json.load(file)
        with open(join(folder, dname, f"{dname}.json"), 'r') as file:
            domain["domain"] = json.load(file)
        if isfile(join(folder, dname, "specials.json")):
            with open(join(folder, dname, "specials.json"), 'r') as file:
                domain["specials"] = json.load(file)
        domains.append(domain)
    return domains

def opposition(domains):
    opps = []
    for domain in domains:
        if "specials" in domain:
            opps.append(domain["specials"]["opposition"])
    return np.array(opps)

def main():
    categories = {
        "basic": get_domains("domains/basic/"),
        "default_domains": get_domains("domains/default_domains/"),
        "i2v5": get_domains("domains/i2v5/"),
        "i5v2": get_domains("domains/i5v2/"),
        "i5v10": get_domains("domains/i5v10/"),
        "i8v5": get_domains("domains/i8v5/"),
        "lp5": get_domains("domains/l+5/"),
        "o_5": get_domains("domains/o-5/"),
        "op5": get_domains("domains/o+5/"),
        "o_8": get_domains("domains/o-8/"),
        "op8": get_domains("domains/o+8/"),
        "o2_8": get_domains("domains/o2-8/"),
        "o2p8": get_domains("domains/o2+8/"),
    }

    for catname, domains in categories.items():
        opp = opposition(domains)
        opp_mean = np.mean(opp) if len(opp) > 0 else float('nan')
        opp_stdev = np.std(opp) if len(opp) > 0 else float('nan')
        print(catname, opp_mean, opp_stdev)

if __name__ == "__main__":
    main()