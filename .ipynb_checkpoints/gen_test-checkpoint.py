import pandas as pd
import sklearn.datasets
import pickle

#generate data
data = sklearn.datasets.make_classification(n_samples=4000000, 
	n_classes=2,
	n_clusters_per_class=1, 
	n_features=5,
	n_informative=2, 
	n_redundant=0, 
	n_repeated=0)


#create dataframe
x = data[0]
y = data[1]
df = pd.DataFrame(data[0])
df['label'] = data[1]
df.head()


#pickle to data folder
with open('./data_lfs/test_data1.pickle', 'wb') as f:
    pickle.dump(df, f)