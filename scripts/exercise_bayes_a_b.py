#%%
# Import libraries
import pandas as pd
import numpy as np

# Number of random draws from the prior
n_draws = 10000
observed_data=6
# Here you sample n_draws draws from the prior into a pandas Series (to have convenient
# methods available for histograms and descriptive statistics, e.g. median)
prior = pd.Series(np.random.uniform(0, 1, n_draws))  

prior.hist() # It's always good to eyeball the prior to make sure it looks ok.

# Here you define the generative model
def generative_model(prob:float) -> pd.Series:
    np.random.binomial(16,prob)
    return np.random.binomial(16,prob)

# Here you simulate data using the parameters from the prior and the 
# generative model
sim_data = [generative_model(p) for p in prior]
# Here you filter off all draws that do not match the data.
posterior = prior[list(map(lambda x: x == observed_data, sim_data))]

posterior.hist() # Eyeball the posterior


# See that we got enought draws left after the filtering. 
# There are no rules here, but you probably want to aim for >1000 draws.

# Now you can summarize the posterior, where a common summary is to take the mean or the median posterior, 
# and perhaps a 95% quantile interval.


print('Number of draws left: %d, Posterior median: %.3f, Posterior quantile interval: %.3f-%.3f' % 
      (len(posterior), posterior.median(), posterior.quantile(.025), posterior.quantile(.975)))
# %%
np.mean(posterior > 0.2)
# %%
signups= pd.Series([np.random.binomial(n=100, p=p) for p in posterior])
signups.hist()
print('Sign-up 95%% quantile interval %d-%d' % tuple(signups.quantile([.025, .975]).values))
# %%
