from cmath import sqrt
from tabnanny import verbose
import pandas as pd
import bnlearn as bn
from math import sqrt
from pgmpy.sampling import GibbsSampling, BayesianModelSampling
import itertools

ATTRIBUTES = ['AGEGROUP', 'PERSINC', 'SEX', 'CARLICENCE']

# This assume that both df have the same collumns/attributes
def SRMSE(actual, pred, attributes):
    total_att = 1
    full_list = {}

    # Get the possible values for each att
    for att in attributes:
        possible_values = actual[att].unique()
        total_att *= len(possible_values)
        full_list[att] = possible_values

    # Generate all the possible combinations
    keys, values = zip(*full_list.items())
    combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
    
    #calculate
    hold = 0
    for instance in combinations:
        # the 2 would be None or not None at the same time
        check_actual = None
        check_pred = None
        for att in attributes:
            if check_actual is not None:
                check_actual = check_actual & (actual[att] == instance[att])
                check_pred = check_pred & (pred[att] == instance[att])
            else:
                check_actual = (actual[att] == instance[att])
                check_pred = (pred[att] == instance[att])
        # This assumes that there will always be False result
        freq_actual = 1 - ((check_actual.value_counts()[False]) / len(check_actual))
        freq_pred = 1 - ((check_pred.value_counts()[False]) / len(check_pred))
        hold += (freq_actual - freq_pred)**2
    
    result = sqrt(hold * total_att)

    return result

if __name__ == "__main__":
    # import data
    original_df = pd.read_csv("./data/VISTA_2012_16_v1_SA1_CSV/P_VISTA12_16_SA1_V1.csv")
    df = original_df[ATTRIBUTES].dropna()
    # It is noted that with small samples, cannot ebtablish the edges
    seed_df = df.sample(n = 20000).copy()
    print(df.shape)
    
    # Learn the DAG in data using Bayesian structure learning:
    DAG = bn.structure_learning.fit(seed_df, methodtype='hc', scoretype='bic', verbose=0)
    # Remove insignificant edges
    DAG = bn.independence_test(DAG, seed_df, alpha=0.05, prune=True)

    # Adjacency matrix
    # print(DAG['adjmat'])

    # Plot the DAG
    # G = bn.plot(DAG)

    # Parameter learning on the user-defined DAG and input data using Bayes to estimate the CPTs
    model = bn.parameter_learning.fit(DAG, seed_df, methodtype='bayes', verbose=0)
    # bn.print_CPD(model)

    # Using other sampling methods
    infer_model = BayesianModelSampling(model['model'])
    # sampling_df = infer_model.forward_sample(size=100)
    # sampling_df = infer_model.likelihood_weighted_sample(size=100)
    # sampling_df = infer_model.rejection_sample(size=10)

    # Using GibbsSampling, noted here it initial/seed is randon
    gibbs_chain = GibbsSampling(model['model'])
    # sampling_df = gibbs_chain.sample(size=10, start_state=None)

    # print(sampling_df)

    # print(SRMSE(df, sampling_df, ATTRIBUTES))
