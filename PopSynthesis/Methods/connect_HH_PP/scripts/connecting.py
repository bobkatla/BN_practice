import pandas as pd
import os, glob
import pickle

from PopSynthesis.Methods.BN.utils.learn_BN import learn_struct_BN_score, learn_para_BN
from pgmpy.sampling import BayesianModelSampling
from pgmpy.factors.discrete import State
import random
from numpy.random import multinomial


def reject_samp_veh(BN, df_marg, zone_lev):
    inference = BayesianModelSampling(BN)
    ls_total_veh = [
        ("Four or more motor vehicles", "4+"), 
        ("Three motor vehicles", "3"), 
        ("Two motor vehicles", "2"), 
        ("One motor vehicle", "1"),
        ("No motor vehicles", "0"),
        ("None info", None)]
    ls_all = []
    for zone in df_marg[zone_lev]:
        print(f"DOING {zone}")
        ls_re = []
        zone_info = df_marg[df_marg[zone_lev]==zone]
        assert len(zone_info) == 1
        for totveh_label in ls_total_veh:
            n_totvehs = int(zone_info[totveh_label[0]].iat[0])
            evidence = State('totalvehs', totveh_label[1]) if totveh_label[1] is not None else None
            # Weird case of multiple
            syn = None
            if evidence:
                syn = inference.rejection_sample(evidence=[evidence], size=n_totvehs, show_progress=True)
            else:
                syn = inference.forward_sample(size=n_totvehs, show_progress=True)
            ls_re.append(syn)
        if ls_re == []: continue
        final_for_zone = pd.concat(ls_re, axis=0)
        final_for_zone[zone_lev] = zone
        ls_all.append(final_for_zone)
    final_result = pd.concat(ls_all, axis=0)
    return final_result


def process_POA():
    df = pd.read_csv("../data/POA_numveh.csv", skiprows=9, skipfooter=7, engine='python')
    df = df.dropna(axis=1, how='all')
    df = df.dropna(axis=0, thresh=6)
    df = df[:-1]
    df["None info"] = df["Not stated"] + df["Not applicable"]
    df = df.drop(columns=["Not stated", "Not applicable", "Total"])
    df = df.rename({"VEHRD Number of Motor Vehicles (ranges)" : "POA"}, axis=1)
    df["POA"] = df.apply(lambda r: r["POA"].replace(", VIC", ""), axis=1)
    return df


def main():
    #learning to get the HH only with main person
    df_seed = pd.read_csv("../data/connect_hh_main.csv")
    # drop all the ids as they are not needed for in BN learning
    id_cols = [x for x in df_seed.columns if "hhid" in x or "persid" in x]
    df_seed = df_seed.drop(columns=id_cols)

    pp_state_names = None
    with open('../data/dict_pp_states.pickle', 'rb') as handle:
        pp_state_names = pickle.load(handle)
    hh_state_names = None
    with open('../data/dict_hh_states.pickle', 'rb') as handle:
        hh_state_names = pickle.load(handle)
    state_names = hh_state_names | pp_state_names

    print("Learn BN")
    model = learn_struct_BN_score(df_seed, show_struct=False, state_names=state_names)
    model = learn_para_BN(model, df_seed)
    print("Doing the sampling")
    # census_df = pd.read_csv("../data/census_sa1.csv")
    POA_df = process_POA()
    final_syn_pop = reject_samp_veh(BN=model, df_marg=POA_df, zone_lev="POA")
    final_syn_pop.to_csv("SynPop_hh_main_POA.csv", index=False)


if __name__ == "__main__":
    main()