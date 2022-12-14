from http.client import SWITCHING_PROTOCOLS
import shutil
from collections import defaultdict
from itertools import permutations
from math import factorial, prod, sqrt
import os
from pathlib import Path
from random import choice, choices
from typing import List, Tuple

import pandas as pd
from geniusweb.profile.utilityspace.LinearAdditiveUtilitySpace import (
    LinearAdditiveUtilitySpace,
)
from geniusweb.profileconnection.ProfileConnectionFactory import (
    ProfileConnectionFactory,
)
from geniusweb.protocol.NegoSettings import NegoSettings
from geniusweb.protocol.session.saop.SAOPState import SAOPState
from geniusweb.simplerunner.ClassPathConnectionFactory import ClassPathConnectionFactory
from geniusweb.simplerunner.NegoRunner import StdOutReporter
from geniusweb.simplerunner.Runner import Runner
from geniusweb.deadline.DeadlineGauss import DeadlineGauss
from pyson.ObjectMapper import ObjectMapper
from uri.uri import URI

from utils.ask_proceed import ask_proceed


def run_session(settings) -> Tuple[dict, dict]:
    agents = settings["agents"]
    profiles = settings["profiles"]
    deadline_time_ms = settings["deadline_time_ms"]
    settings: dict = settings
    means = settings.get("means", [1.0])
    stdevs = settings.get("stdevs", [0.2])
    if "seed" not in settings:
        from numpy.random import default_rng
        seed = int(default_rng().integers(0, 2 ** 63 - 1))
    else:
        seed = settings.get("seed")
    endtime = settings.get("endtime", 100.0)
    durationms = settings.get("durationms", 60000)


    # quick and dirty checks
    assert isinstance(agents, list) and len(agents) == 2
    assert isinstance(profiles, list) and len(profiles) == 2
    assert isinstance(deadline_time_ms, int) and deadline_time_ms > 0
    assert all(["class" in agent for agent in agents])

    for agent in agents:
        if "parameters" in agent:
            if "storage_dir" in agent["parameters"]:
                storage_dir = Path(agent["parameters"]["storage_dir"])
                if not storage_dir.exists():
                    storage_dir.mkdir(parents=True)

    # file path to uri
    profiles_uri = [f"file:{x}" for x in profiles]

    # create full settings dictionary that geniusweb requires
    settings_full = {
        "SAOPSettings": {
            "participants": [
                {
                    "TeamInfo": {
                        "parties": [
                            {
                                "party": {
                                    "partyref": f"pythonpath:{agents[0]['class']}",
                                    "parameters": agents[0]["parameters"]
                                    if "parameters" in agents[0]
                                    else {},
                                },
                                "profile": profiles_uri[0],
                            }
                        ]
                    }
                },
                {
                    "TeamInfo": {
                        "parties": [
                            {
                                "party": {
                                    "partyref": f"pythonpath:{agents[1]['class']}",
                                    "parameters": agents[1]["parameters"]
                                    if "parameters" in agents[1]
                                    else {},
                                },
                                "profile": profiles_uri[1],
                            }
                        ]
                    }
                },
            ],
            #"deadline": {"DeadlineRounds": {"rounds": 200, "durationms": 60000}},
            "deadline": {"DeadlineGauss": {"means": means, "stdevs": stdevs, "seed": seed, "endtime": endtime, "durationms": durationms}},
            # "deadline": {"DeadlineTime": {"durationms": deadline_time_ms}},
        }
    }

    # parse settings dict to settings object
    settings_obj = ObjectMapper().parse(settings_full, NegoSettings)

    # create the negotiation session runner object
    runner = Runner(settings_obj, ClassPathConnectionFactory(), StdOutReporter(), 0)

    # run the negotiation session
    runner.run()

    # get results from the session in class format and dict format
    results_class: SAOPState = runner.getProtocol().getState()
    results_dict: dict = ObjectMapper().toJson(results_class)["SAOPState"]

    # add utilities to the results and create a summary
    results_trace, results_summary = process_results(results_class, results_dict)

    return results_trace, results_summary


def run_tournament(tournament_settings: dict) -> Tuple[list, list]:
    # create agent permutations, ensures that every agent plays against every other agent on both sides of a profile set.
    agents = tournament_settings["agents"]
    profile_sets = tournament_settings["profile_sets"]
    deadline_time_ms = tournament_settings["deadline_time_ms"]

    num_sessions = (factorial(len(agents)) // factorial(len(agents) - 2)) * len(
        profile_sets
    )
    if num_sessions > 100:
        message = (
            f"WARNING: this would run {num_sessions} negotiation sessions. Proceed?"
        )
        if not ask_proceed(message):
            print("Exiting script")
            exit()

    tournament_results = []
    tournament_steps = []
    for profiles in profile_sets:
        # quick an dirty check
        assert isinstance(profiles, list) and len(profiles) == 2
        for agent_duo in permutations(agents, 2):
            # create session settings dict
            settings = {
                "agents": list(agent_duo),
                "profiles": profiles,
                "deadline_time_ms": deadline_time_ms,
            }

            # run a single negotiation session
            _, session_results_summary = run_session(settings)

            # assemble results
            tournament_steps.append(settings)
            tournament_results.append(session_results_summary)

    tournament_results_summary = process_tournament_results(tournament_results)

    return tournament_steps, tournament_results, tournament_results_summary

def run_marketplace(marketplace_settings: dict) -> Tuple[list, list]:
    # create agent permutations, ensures that every agent plays against every other agent on both sides of a profile set.
    agent_distribution = marketplace_settings["agent_distribution"]
    profile_set = marketplace_settings["profile_set"]
    deadline_time_ms = marketplace_settings["deadline_time_ms"]
    endtime = marketplace_settings["endtime"]

    marketplace_results = []
    marketplace_steps = []
    count = marketplace_settings["count"]
    for _ in range(count):
        # create session settings dict
        settings = {
            "agents": sample_agents(agent_distribution),
            "profiles": sample_profiles(profile_set),
            "deadline_time_ms": deadline_time_ms,
            "endtime": endtime,
        }

        # run a single negotiation session
        _, session_results_summary = run_session(settings)

        # assemble results
        marketplace_steps.append(settings)
        marketplace_results.append(session_results_summary)

    marketplace_results_summary = process_marketplace_results(marketplace_steps, marketplace_results)

    return marketplace_steps, marketplace_results, marketplace_results_summary

def sample_agents(agent_distribution, n = 2):
    c = [
        {"class": "agents.conceder_agent.conceder_agent.ConcederAgent"},
        {"class": "agents.boulware_agent.boulware_agent.BoulwareAgent"},
        {"class": "agents.hardliner_agent.hardliner_agent.HardlinerAgent"},
        {"class": "agents.micro_agent.micro_agent.MiCROAgent"}
    ]
    agents = choices(c, agent_distribution, k = n)
    return agents

def sample_profiles(profile_set):
    d = get_immediate_subdirectories(profile_set)
    domain = choice(d)
    return [profile_set + "/" + domain + "/profileA.json", profile_set+ "/" + domain + "/profileB.json"]

def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir) if os.path.isdir(os.path.join(a_dir, name))]

def process_results(results_class: SAOPState, results_dict: dict):
    # dict to translate geniusweb agent reference to Python class name
    agent_translate = {
        k: v["party"]["partyref"].split(".")[-1]
        for k, v in results_dict["partyprofiles"].items()
    }

    results_summary = {"num_offers": 0}
    bid_final = {}

    # check if there are any actions (could have crashed)
    if results_dict["actions"]:
        # obtain utility functions
        utility_funcs = {
            k: get_utility_function(v["profile"])
            for k, v in results_dict["partyprofiles"].items()
        }

        # iterate both action classes and dict entries
        actions_iter = zip(results_class.getActions(), results_dict["actions"])

        for action_class, action_dict in actions_iter:
            if "Offer" in action_dict:
                offer = action_dict["Offer"]
            elif "Accept" in action_dict:
                offer = action_dict["Accept"]
            else:
                continue

            # add bid utility of both agents if bid is not None
            bid = action_class.getBid()
            if bid is None:
                raise ValueError(
                    f"Found `None` value in sequence of actions: {action_class}"
                )
            else:
                offer["utilities"] = {
                    k: float(v.getUtility(bid)) for k, v in utility_funcs.items()
                }

            results_summary["num_offers"] += 1

        # gather a summary of results
        if "Accept" in action_dict:
            utilities_final = list(offer["utilities"].values())
            bid_final = action_dict["Accept"]["bid"]
            result = "agreement"
        else:
            utilities_final = [0, 0]
            bid_final = {}
            result = "failed"
    else:
        utilities_final = [0, 0]
        result = "ERROR"

    for i, actor in enumerate(results_dict["connections"]):
        position = actor.split("_")[-1]
        results_summary[f"agent_{position}"] = agent_translate[actor]
        results_summary[f"utility_{position}"] = utilities_final[i]
    results_summary["nash_product"] = prod(utilities_final)
    results_summary["social_welfare"] = sum(utilities_final)
    results_summary["result"] = result
    results_summary["final_bid"] = bid_final

    return results_dict, results_summary


def get_utility_function(profile_uri) -> LinearAdditiveUtilitySpace:
    profile_connection = ProfileConnectionFactory.create(
        URI(profile_uri), StdOutReporter()
    )
    profile = profile_connection.getProfile()
    assert isinstance(profile, LinearAdditiveUtilitySpace)

    return profile


def process_tournament_results(tournament_results):
    agent_result_raw = defaultdict(lambda: defaultdict(list))
    tournament_results_summary = defaultdict(lambda: defaultdict(int))
    for session_results in tournament_results:
        agents = {k: v for k, v in session_results.items() if k.startswith("agent")}
        for agent_id, agent_class in agents.items():
            agent_result_raw[agent_class]["utility"].append(
                session_results[f"utility_{agent_id.split('_')[1]}"]
            )
            agent_result_raw[agent_class]["nash_product"].append(
                session_results["nash_product"]
            )
            agent_result_raw[agent_class]["social_welfare"].append(
                session_results["social_welfare"]
            )
            if "num_offers" in session_results:
                agent_result_raw[agent_class]["num_offers"].append(
                    session_results["num_offers"]
                )
            tournament_results_summary[agent_class][session_results["result"]] += 1

    for agent, stats in agent_result_raw.items():
        num_session = len(stats["utility"])
        for desc, stat in stats.items():
            stat_average = sum(stat) / num_session
            tournament_results_summary[agent][f"avg_{desc}"] = stat_average
        tournament_results_summary[agent]["count"] = num_session

    column_order = [
        "avg_utility",
        "avg_nash_product",
        "avg_social_welfare",
        "avg_num_offers",
        "count",
        "agreement",
        "failed",
        "ERROR",
    ]
    column_type = {
        "count": int,
        "agreement": int,
        "failed": int,
        "ERROR": int,
    }

    # results dictionary to dataframe
    tournament_results_summary = pd.DataFrame(tournament_results_summary).T

    # clean data and types
    tournament_results_summary = tournament_results_summary.fillna(0)
    for column in column_order:
        if column not in tournament_results_summary:
            tournament_results_summary[column] = 0
    tournament_results_summary = tournament_results_summary.astype(column_type)

    # structure dataframe
    tournament_results_summary.sort_values("avg_utility", ascending=False, inplace=True)
    tournament_results_summary = tournament_results_summary[column_order]

    return tournament_results_summary

def process_marketplace_results(marketplace_steps, marketplace_results):
    agent_result_raw = defaultdict(lambda: defaultdict(list))
    marketplace_results_summary = defaultdict(lambda: defaultdict(int))
    for session_results in marketplace_results:
        agents = {k: v for k, v in session_results.items() if k.startswith("agent")}
        for agent_id, agent_class in agents.items():
            agent_result_raw[agent_class]["utility"].append(
                session_results[f"utility_{agent_id.split('_')[1]}"]
            )
            agent_result_raw[agent_class]["nash_product"].append(
                session_results["nash_product"]
            )
            agent_result_raw[agent_class]["social_welfare"].append(
                session_results["social_welfare"]
            )
            if "num_offers" in session_results:
                agent_result_raw[agent_class]["num_offers"].append(
                    session_results["num_offers"]
                )
            marketplace_results_summary[agent_class][session_results["result"]] += 1

    for agent, stats in agent_result_raw.items():
        num_session = len(stats["utility"])
        for desc, stat in stats.items():
            stat_average = sum(stat) / num_session
            stat_std = sqrt(sum([(s - stat_average)**2 for s in stat]) / (num_session - 1))
            marketplace_results_summary[agent][f"avg_{desc}"] = stat_average
            marketplace_results_summary[agent][f"std_{desc}"] = stat_std
        marketplace_results_summary[agent]["count"] = num_session

    column_order = [
        "avg_utility",
        "std_utility",
        "avg_nash_product",
        "std_nash_product",
        "avg_social_welfare",
        "std_social_welfare",
        "avg_num_offers",
        "std_num_offers",
        "count",
        "agreement",
        "failed",
        "ERROR",
    ]
    column_type = {
        "count": int,
        "agreement": int,
        "failed": int,
        "ERROR": int,
    }

    # results dictionary to dataframe
    marketplace_results_summary = pd.DataFrame(marketplace_results_summary).T

    # clean data and types
    marketplace_results_summary = marketplace_results_summary.fillna(0)
    for column in column_order:
        if column not in marketplace_results_summary:
            marketplace_results_summary[column] = 0
    marketplace_results_summary = marketplace_results_summary.astype(column_type)

    # structure dataframe
    marketplace_results_summary.sort_values("avg_utility", ascending=False, inplace=True)
    marketplace_results_summary = marketplace_results_summary[column_order]

    return marketplace_results_summary

