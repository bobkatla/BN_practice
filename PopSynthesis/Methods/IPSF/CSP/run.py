"""Run the CSP from a given syn HH (also SAA to adjust again)"""


import pickle
import pandas as pd
from PopSynthesis.Methods.IPSF.const import (
    processed_dir,
    output_dir,
    PP_ATTS,
    NOT_INCLUDED_IN_BN_LEARN,
    zone_field,
)
from PopSynthesis.Methods.IPSF.CSP.operations.extra_filters import filter_mismatch_hhsz
from PopSynthesis.Methods.IPSF.CSP.operations.sample_from_pairs import (
    sample_matching_from_pairs,
    create_count_col,
)


def main():
    # TODO: is there anyway to use pp marg
    # get the data
    HHID = "hhid"
    main_rela = "Main"
    hh_name = "HH"

    syn_hh = pd.read_csv(
        output_dir / "SAA_output_HH_again.csv", index_col=0
    ).reset_index(drop=True)
    syn_hh["hhid"] = syn_hh.index
    with open(processed_dir / "dict_pool_pairs.pickle", "rb") as handle:
        pools_ref = pickle.load(handle)
    
    # get attributes
    pp_atts = list(set(PP_ATTS) - set(NOT_INCLUDED_IN_BN_LEARN))
    hh_atts = [x for x in syn_hh.columns if x not in [zone_field, HHID]]
    all_rela = [x.split("-")[-1] for x in pools_ref.keys()]

    # rename the HH-Main so the so Main match the rest
    rename_main = {x: f"{x}_{main_rela}" for x in pp_atts}
    pools_ref[f"{hh_name}-{main_rela}"] = pools_ref[f"{hh_name}-{main_rela}"].rename(columns=rename_main)
    pools_ref[f"{hh_name}-{main_rela}"] = filter_mismatch_hhsz(
        pools_ref[f"{hh_name}-{main_rela}"], "hhsize", all_rela
    )

    # NOTE: the syn main people will be updated with the new values, it is the first val in the array
    assert all_rela[0] == main_rela
    main_pp = None
    rm_hh = []
    kept_hh = []
    rm_main_pp = []
    pp_results = {}
    main_atts = list(rename_main.values())
    for rela in all_rela:
        print(f"Processing {rela}")
        to_process_syn = syn_hh
        pool_name = f"{hh_name}-{main_rela}"
        evidence_cols = hh_atts
        sample_cols = main_atts + all_rela
    
        if rela != main_rela:
            # override
            main_pp[rela] = main_pp[rela].astype(int)
            to_process_syn = main_pp[main_pp[rela] > 0]
            to_process_syn = create_count_col(to_process_syn, rela)
            pool_name = f"{main_rela}-{rela}"
            evidence_cols = main_atts
            sample_cols = [f"{x}_{rela}" for x in pp_atts]
        
        rela_pp, removed_syn, kept_syn = sample_matching_from_pairs(
            given_syn=to_process_syn,
            syn_id=HHID,
            paired_pool=pools_ref[pool_name],
            evidence_cols=evidence_cols,
            sample_cols=sample_cols,
        )
        rela_pp["relationship"] = rela
        pp_results[rela] = rela_pp

        if rela == main_rela:
            rm_hh.append(removed_syn)
            kept_hh.append(kept_syn)
            main_pp = rela_pp
        else:
            rm_main_pp.append(removed_syn)
            main_pp = kept_syn
            pp_results[main_rela] = kept_syn

    print(rm_hh)
    print(rm_main_pp)
    print(pp_results)

if __name__ == "__main__":
    main()
