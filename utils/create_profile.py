import json
from math import sqrt
import os
from itertools import product
from random import randint
from shutil import rmtree
from string import ascii_uppercase

import numpy as np
import plotly.graph_objects as go
from numpy.random import dirichlet
from numpy.random import uniform
from numpy.random import beta
from numpy.random import shuffle

def main():
    np.random.seed(100)
    gen_domains("domains/basic/", n=50)

    np.random.seed(101)
    gen_domains("domains/i8v5/", n=50, issue_count=8, value_count=5, extra=False)
    
    np.random.seed(102)
    gen_domains("domains/i2v5/", n=50, issue_count=2, value_count=5)
    
    np.random.seed(103)
    gen_domains("domains/i5v2/", n=50, issue_count=5, value_count=2)
    
    np.random.seed(104)
    gen_domains("domains/i5v10/", n=50, issue_count=5, value_count=10, extra=False)
    
    np.random.seed(105)
    gen_domains("domains/o-5/", n=50, opposition=-0.5)
    
    np.random.seed(106)
    gen_domains("domains/o+5/", n=50, opposition=0.5)
    
    np.random.seed(107)
    gen_domains("domains/l+5/", n=50, lopsided=0.5)
    
    np.random.seed(108)
    gen_domains("domains/o-8/", n=50, opposition=-0.8)
    
    np.random.seed(109)
    gen_domains("domains/o+8/", n=50, opposition=0.8)
    
    np.random.seed(110)
    gen_domains("domains/o2-8/", n=50, opposition_2=-0.8)
    
    np.random.seed(111)
    gen_domains("domains/o2+8/", n=50, opposition_2=0.8)
    
    np.random.seed(110)
    gen_domains("domains/test_2/", n=4, opposition_2=0.6)


def gen_domains(folder, n=1, issue_count=None, value_count=None, opposition=None, lopsided=None, extra=True, opposition_2=None):
    os.makedirs(folder, exist_ok=True)
    big_n = n
    if opposition_2 is not None and opposition_2 != 0.0:
        if not extra:
            raise Exception("extra must be True to use opposition_2")
        big_n = int(n / (1.0 - abs(opposition_2)))
    domains = []
    for i in range(big_n):
        domain = Domain.create_random_new(f"domain{i:02d}", issue_count, value_count, opposition, lopsided)
        if extra:
            domain.calculate_specials()
            domain.generate_visualisation()
        domains.append(domain)
    if opposition_2 is not None and opposition_2 != 0.0:
        domain_sorted = sorted(domains, key=lambda d: d.opposition)
        if opposition_2 < 0.0:
            domains = domain_sorted[0:n]
        else:
            domains = domain_sorted[-n:]
    for domain in domains:
        domain.to_file(f"{folder}")

    def gen_original():
        for i in range(50):
            domain = Domain.create_random(f"domain{i:02d}")
            domain.calculate_specials()
            domain.generate_visualisation()
            domain.to_file("domains/")

class Profile:
    def __init__(self, profile, issue_weights, value_weights):
        self.profile = profile
        self.issue_weights = issue_weights
        self.value_weights = value_weights

    @classmethod
    def from_file(cls, utility_file):
        utility_file = utility_file.split(":")[-1]

        with open(utility_file, "r") as f:
            profile = json.load(f)

        raw = profile["LinearAdditiveUtilitySpace"]
        issue_weights = {i: w for i, w in raw["issueWeights"].items()}
        value_weights = {}

        for issue, values in raw["issueUtilities"].items():
            issue_value_weights = {
                v: w for v, w in values["DiscreteValueSetUtilities"]["valueUtilities"].items()
            }
            value_weights[issue] = issue_value_weights

        return cls(profile, issue_weights, value_weights)

    @classmethod
    def create_2_random_new(cls, domain, name_a, name_b, opposition=None, lopsided=None):
        def dirichlet_dist(names, mode, alpha, lopsided=None):
            distribution = (dirichlet(alpha) * 100000).astype(int)
            if mode == "issues":
                distribution[0] += 100000 - np.sum(distribution)
            if mode == "values":
                # distribution = [100000] + [100000 * random() for _ in range(len(names) - 1)]
                # shuffle(distribution)
                # distribution = np.array(distribution).astype(int)
                # distribution = (dirichlet(np.array(range(len(names))) * 0.3 + 1.0) * 100000).astype(int)
                # shuffle(distribution)
                distribution = distribution - np.min(distribution)
                distribution = (distribution * 100000.0 / np.max(distribution)).astype(int)
                # distribution = distribution.astype(int)
                if lopsided is not None and lopsided > 0:
                    reward = lopsided * np.max(distribution)
                    distribution[distribution > 0] = ((1 - lopsided) * distribution[distribution > 0] + reward)
                distribution = distribution.astype(int)
            distribution = distribution / 100000
            return {i: w for i, w in zip(names, distribution)}
        issues = list(domain["issuesValues"].keys())
        alpha_seed = np.linspace(-1.0, 1.0, len(issues), endpoint=True)
        alpha_base = np.repeat(1.0, len(issues))
        shuffle(alpha_seed)
        alpha_a = np.abs(opposition) * alpha_seed + alpha_base
        alpha_b = -opposition * alpha_seed + alpha_base
        issue_weights_a = dirichlet_dist(issues, "issues", alpha_a)
        issue_weights_b = dirichlet_dist(issues, "issues", alpha_b)
        value_weights_a = {}
        value_weights_b = {}
        if lopsided is None:
            lopsided = 0
        for issue in issues:
            values = domain["issuesValues"][issue]["values"]
            value_weights_a[issue] = dirichlet_dist(values, "values", alpha=np.repeat(1.0, len(values)), lopsided=lopsided)
            value_weights_b[issue] = dirichlet_dist(values, "values", alpha=np.repeat(1.0, len(values)), lopsided=-lopsided)
        issue_utilities_a = {
            i: {"DiscreteValueSetUtilities": {"valueUtilities": value_weights_a[i]}} for i in issues
        }
        issue_utilities_b = {
            i: {"DiscreteValueSetUtilities": {"valueUtilities": value_weights_b[i]}} for i in issues
        }
        profile_a = {
            "LinearAdditiveUtilitySpace": {
                "issueUtilities": issue_utilities_a,
                "issueWeights": issue_weights_a,
                "domain": domain,
                "name": name_a,
            }
        }
        profile_b = {
            "LinearAdditiveUtilitySpace": {
                "issueUtilities": issue_utilities_b,
                "issueWeights": issue_weights_b,
                "domain": domain,
                "name": name_b,
            }
        }
        return cls(profile_a, issue_weights_a, value_weights_a), cls(profile_b, issue_weights_b, value_weights_b)

    @classmethod
    def create_random(cls, domain, name):
        def dirichlet_dist(names, mode, alpha=1):
            distribution = (dirichlet([alpha] * len(names)) * 100000).astype(int)
            if mode == "issues":
                distribution[0] += 100000 - np.sum(distribution)
            if mode == "values":
                # distribution = [100000] + [100000 * random() for _ in range(len(names) - 1)]
                # shuffle(distribution)
                # distribution = np.array(distribution).astype(int)
                # distribution = (dirichlet(np.array(range(len(names))) * 0.3 + 1.0) * 100000).astype(int)
                # shuffle(distribution)
                distribution = distribution - np.min(distribution)
                distribution = (distribution * 100000 / np.max(distribution)).astype(
                    int
                )
            distribution = distribution / 100000
            return {i: w for i, w in zip(names, distribution)}

        issues = list(domain["issuesValues"].keys())
        issue_weights = dirichlet_dist(issues, "issues")
        value_weights = {}
        for issue in issues:
            values = domain["issuesValues"][issue]["values"]
            value_weights[issue] = dirichlet_dist(values, "values", alpha=1)

        issue_utilities = {
            i: {"DiscreteValueSetUtilities": {"valueUtilities": value_weights[i]}} for i in issues
        }
        profile = {
            "LinearAdditiveUtilitySpace": {
                "issueUtilities": issue_utilities,
                "issueWeights": issue_weights,
                "domain": domain,
                "name": name,
            }
        }
        return cls(profile, issue_weights, value_weights)

    def to_file(self, parent_path):
        domain_name = self.profile["LinearAdditiveUtilitySpace"]["domain"]["name"]
        profile_name = self.profile["LinearAdditiveUtilitySpace"]["name"]
        path = os.path.join(parent_path, domain_name)
        with open(os.path.join(path, f"{profile_name}.json"), "w") as f:
            f.write(json.dumps(self.profile, indent=2))

    def get_issues_values(self):
        return self.profile["LinearAdditiveUtilitySpace"]["domain"]["issuesValues"]

    def get_utility(self, bid):
        return sum(
            self.issue_weights[i] * self.value_weights[i][v] for i, v in bid.items()
        )


class Domain:
    def __init__(
        self,
        domain,
        profile_A: Profile,
        profile_B: Profile,
        nash_bid=None,
        kalai_bid=None,
        pareto_front=None,
        opposition=None,
        visualisation=None,
    ):
        self.domain = domain
        self.profile_A = profile_A
        self.profile_B = profile_B
        self.nash_bid = nash_bid
        self.kalai_bid = kalai_bid
        self.pareto_front = pareto_front
        self.opposition = opposition
        self.visualisation = visualisation

    @classmethod
    def create_random_new(cls, name, issue_count=None, value_count=None, opposition=None, lopsided=None):
        
        # def random_values(num_values):
        #     values = [f"value_{x}" for x in ascii_uppercase[:num_values]]
        #     return {"values": values}
        if issue_count is None and value_count is None:
            domain_size = randint(200, 10000)
            print(name)
            # print(domain_size)
            while True:
                num_issues = randint(4, 10)
                spread = dirichlet([1] * num_issues)
                multiplier = (domain_size / np.prod(spread)) ** (1.0 / randint(3, 7))
                values_per_issue = np.round(multiplier * spread).astype(np.int32)
                values_per_issue = np.clip(values_per_issue, 2, None)
                if abs(domain_size - np.prod(values_per_issue)) < (0.1 * domain_size):
                    # print(np.prod(values_per_issue))
                    break
            issues = list(ascii_uppercase[:num_issues])
        else:
            num_issues = issue_count
            values_per_issue = np.repeat(value_count, issue_count)
            issues = list(ascii_uppercase[:num_issues])

        issuesValues = {}
        for issue, num_values in zip(issues, values_per_issue):
            values = {"values": [f"value{x}" for x in ascii_uppercase[:num_values]]}
            issuesValues[f"issue{issue}"] = values

        domain = {"name": name, "issuesValues": issuesValues}
        if opposition is None:
            opposition = 0.0
        if lopsided is None:
            lopsided = 0.0
        profile_A, profile_B = Profile.create_2_random_new(domain, "profileA", "profileB", opposition, lopsided)
        return cls(domain, profile_A, profile_B)


    @classmethod
    def create_random(cls, name):
        # def random_values(num_values):
        #     values = [f"value_{x}" for x in ascii_uppercase[:num_values]]
        #     return {"values": values}

        domain_size = randint(200, 10000)
        print(name)
        # print(domain_size)
        while True:
            num_issues = randint(4, 10)
            spread = dirichlet([1] * num_issues)
            multiplier = (domain_size / np.prod(spread)) ** (1.0 / randint(3, 7))
            values_per_issue = np.round(multiplier * spread).astype(np.int32)
            values_per_issue = np.clip(values_per_issue, 2, None)
            if abs(domain_size - np.prod(values_per_issue)) < (0.1 * domain_size):
                # print(np.prod(values_per_issue))
                break
        issues = list(ascii_uppercase[:num_issues])

        issuesValues = {}
        for issue, num_values in zip(issues, values_per_issue):
            values = {"values": [f"value{x}" for x in ascii_uppercase[:num_values]]}
            issuesValues[f"issue{issue}"] = values

        domain = {"name": name, "issuesValues": issuesValues}
        profile_A = Profile.create_random(domain, "profileA")
        profile_B = Profile.create_random(domain, "profileB")
        return cls(domain, profile_A, profile_B)

    @classmethod
    def from_directory(cls, directory):
        name = os.path.basename(directory)
        profile_B = Profile.from_file(f"{directory}/profileB.json")
        profile_A = Profile.from_file(f"{directory}/profileA.json")
        domain = {"name": name, "issuesValues": profile_A.get_issues_values()}

        specials_path = f"{directory}/specials.json"
        if os.path.exists(specials_path):
            with open(specials_path, "r") as f:
                specials = json.load(f)
            return cls(
                domain,
                profile_A,
                profile_B,
                specials["nash"],
                specials["kalai"],
                specials["pareto_front"],
            )
        else:
            domain = cls(domain, profile_A, profile_B)
            return domain

    def calculate_specials(self):
        if self.nash_bid:
            return False
        self.pareto_front = self.get_pareto(list(self.iter_bids()))

        nash_utility = 0
        kalai_diff = 10

        for pareto_bid in self.pareto_front:
            utility_A, utility_B = pareto_bid["utility"][0], pareto_bid["utility"][1]

            utility_diff = abs(utility_A - utility_B)
            utility_prod = utility_A * utility_B

            if utility_diff < kalai_diff:
                self.kalai_bid = pareto_bid
                kalai_diff = utility_diff
                self.opposition = sqrt((utility_A - 1.0) ** 2 + (utility_B - 1.0) ** 2)
            if utility_prod > nash_utility:
                self.nash_bid = pareto_bid
                nash_utility = utility_prod

        return True

    def generate_visualisation(self):
        bid_utils = [self.get_utilities(bid) for bid in self.iter_bids()]
        bid_utils = list(zip(*bid_utils))

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=bid_utils[0],
                y=bid_utils[1],
                mode="markers",
                name="bids",
                marker=dict(size=3),
            )
        )

        if self.pareto_front:
            pareto_utils = [bid["utility"] for bid in self.pareto_front]
            pareto_utils = list(zip(*pareto_utils))
            fig.add_trace(
                go.Scatter(
                    x=pareto_utils[0],
                    y=pareto_utils[1],
                    mode="lines+markers",
                    name="Pareto",
                    marker=dict(size=3),
                    line=dict(width=1.5),
                )
            )

        if self.nash_bid:
            x, y = self.nash_bid["utility"]
            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers",
                    name="Nash",
                    marker=dict(size=8, line_width=2, symbol="x-thin"),
                )
            )

        if self.kalai_bid:
            x, y = self.kalai_bid["utility"]
            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers",
                    name="Kalai-Smorodinsky",
                    marker=dict(size=8, line_width=2, symbol="cross-thin"),
                )
            )

        fig.update_xaxes(range=[0, 1], title_text="Utility A")
        fig.update_yaxes(range=[0, 1], title_text="Utility B")

        fig.update_layout(
            title=dict(
                text=f"{self.get_name()}<br><sub>(size: {len(list(self.iter_bids()))}, opposition: {self.opposition:.4f})</sub>",
                x=0.5,
                xanchor="center",
            )
        )

        self.visualisation = fig

    def to_file(self, parent_path):
        path = os.path.join(parent_path, self.domain["name"])
        if os.path.exists(path):
            rmtree(path)
        os.makedirs(path)

        with open(os.path.join(path, f"{self.domain['name']}.json"), "w") as f:
            f.write(json.dumps(self.domain, indent=2))
        self.profile_A.to_file(parent_path)
        self.profile_B.to_file(parent_path)

        if self.nash_bid:
            with open(os.path.join(path, "specials.json"), "w") as f:
                f.write(
                    json.dumps(
                        {
                            "size": len(list(self.iter_bids())),
                            "opposition": self.opposition,
                            "nash": self.nash_bid,
                            "kalai": self.kalai_bid,
                            "pareto_front": self.pareto_front,
                        },
                        indent=2,
                    )
                )

        if self.visualisation:
            self.visualisation.write_image(
                file=os.path.join(path, "visualisation.png"), scale=5
            )

    def iter_bids(self):
        return iter(self)

    def get_utilities(self, bid):
        return self.profile_A.get_utility(bid), self.profile_B.get_utility(bid)

    def get_pareto(self, all_bids: list):
        pareto_front = []
        # dominated_bids = set()
        while True:
            candidate_bid = all_bids.pop(0)
            bid_nr = 0
            dominated = False
            while len(all_bids) != 0 and bid_nr < len(all_bids):
                bid = all_bids[bid_nr]
                if self._dominates(candidate_bid, bid):
                    # If it is dominated remove the bid from all bids
                    all_bids.pop(bid_nr)
                    # dominated_bids.add(frozenset(bid.items()))
                elif self._dominates(bid, candidate_bid):
                    dominated = True
                    # dominated_bids.add(frozenset(candidate_bid.items()))
                    bid_nr += 1
                else:
                    bid_nr += 1

            if not dominated:
                # add the non-dominated bid to the Pareto frontier
                pareto_front.append(
                    {
                        "bid": candidate_bid,
                        "utility": [
                            self.profile_A.get_utility(candidate_bid),
                            self.profile_B.get_utility(candidate_bid),
                        ],
                    }
                )

            if len(all_bids) == 0:
                break

        pareto_front = sorted(pareto_front, key=lambda d: d["utility"][0])

        return pareto_front

    def _dominates(self, bid, candidate_bid):
        if self.profile_A.get_utility(bid) < self.profile_A.get_utility(candidate_bid):
            return False
        elif self.profile_B.get_utility(bid) < self.profile_B.get_utility(
            candidate_bid
        ):
            return False
        else:
            return True

    def get_name(self):
        return self.domain["name"]

    def __iter__(self) -> dict:
        issuesValues = [
            [i, v["values"]] for i, v in self.domain["issuesValues"].items()
        ]
        issues, values = zip(*issuesValues)

        bids_values = product(*values)
        for bid_values in bids_values:
            yield {i: v for i, v in zip(issues, bid_values)}

    def __str__(self) -> str:
        return str(self.domain)


if __name__ == "__main__":
    main()
