"""
To learn simple BN
"""
import pandas as pd
import numpy as np
from PopSynthesis.Benchmark.CompareFullPop.utils import wrapper_get_all, sampling_from_full_pop, realise_full_pop_based_on_weight, condense_pop
from PopSynthesis.Benchmark.CompareFullPop.compare import full_pop_SRMSE
from PopSynthesis.Methods.BN.utils.learn_BN import learn_struct_BN_score, learn_para_BN
from pgmpy.sampling import BayesianModelSampling


def loop_learn_full_pop(loc_data, range_sample=np.linspace(0.01, 0.1, 10)):
    seed_df_hh = pd.read_csv(loc_data + "H_sample.csv")
    seed_df_pp = pd.read_csv(loc_data + "P_sample.csv")
    
    # fake_HH_seed_data, fake_PP_seed_data = wrapper_get_all(seed_df_hh, seed_df_pp, sample_rate=0.01, name_weights_in_hh="wdhhwgt_sa3", new_name_weights_in_hh='_weight', shared_ids_name='hhid')
    
    # NOTE: for now, only HH data
    to_drop_cols = ["hh_num", "hhid", "SA1", "SA2", "SA3", "SA4"]
    seed_df_hh = seed_df_hh.drop(columns=to_drop_cols)
    full_df_hh = realise_full_pop_based_on_weight(seed_df_hh, weight_col="wdhhwgt_sa3")
    n = len(full_df_hh)
    print(n)
    results = []
    for rate in range_sample:
        print(f"PROCESSING rate {rate}")
        seed_df = sampling_from_full_pop(full_df_hh, rate=rate)
        new_seed_df = condense_pop(seed_df, "_weight")
        print("Learn BN")
        model = learn_struct_BN_score(new_seed_df, show_struct=False)
        model = learn_para_BN(model, new_seed_df)
        print("Doing the sampling")
        inference = BayesianModelSampling(model)
        syn_pop = inference.forward_sample(size=n)
        print("Calculate SRMSE now")
        SRMSE = full_pop_SRMSE(full_df_hh, syn_pop)
        results.append(SRMSE)
        print(f"Done rate {rate}, got score of {SRMSE}")
    return results


def main():
    loc_data = "./data/"
    min_rate, max_rate, tot = 0.01, 0.1, 10
    results = loop_learn_full_pop(loc_data=loc_data, range_sample=np.linspace(min_rate, max_rate, tot))
    data = np.asarray(results)
    np.save(f'./output/results_simpleBN_{min_rate}_{max_rate}.npy', data)
    print(results)

if __name__ == "__main__":
    main()