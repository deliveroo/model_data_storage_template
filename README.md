# Test Data Storage Guidance

This repo suggests guideline frameworks for effectively storing training / test / validation sets for our forecasting projects.



## Option A: S3 Bucket:

![Alt Text](https://github.com/dstarkey1/model_data_storage_template/blob/main/img/s3_img.png)


#### 1: Create a `data_s3` directory in your project repo: `mkdir ./data_s3`.

#### 2: Add this directory to your `.gitignore` file to prevent accidental commiting large datasets to github repo.
* `nano .gitignore`
* Add the following lines
-  `data_s3/*`
-  `/data_s3`

#### 3: Setup AWS S3 credentials

#### 4: Create pickle dataset with model name - date - version nameing convention

e.g. in python script:
```python
with open('./data_s3/OVForecast_20220606_1.pickle', 'wb') as f:
    pickle.dump(df, f)
```

#### 5: Pull/Push from forecast-model-datasets to './data_s3' local directory
* `aws s3 cp s3://forecast-model-datasets/[*ModelName_DateStamp_Version*.pickle]` ./`

* `aws s3 cp s3://forecast-model-datasets/[*ModelName_DateStamp_Version*.pickle]` ./`



## Option B: GitHub Large File Storage (git-lfs): https://git-lfs.github.com/


![Alt Text](https://github.com/dstarkey1/model_data_storage_template/blob/main/img/lfs_img.png)

Integrates large file storage conveniently within github repo (no need for faffing around with s3 connections). 1GB of storage and bandwith provided for free with individual accounts. _Does Deliveroo have special access?_

#### Setup:

* Install git-lfs: `brew install git-lfs `

* Verify Installation: `git lfs install`

* Navigate to repo: `cd ./projects/gitlfs_test`

* Add the location and file types you want to track with git-lfs: `git lfs track "./data_lfs/*.pickle"`

* Add and commit files in the standard way:
- `git add ./data_lfs/*.pickle`
- `git commit 'test lfs storage'`
-  `git push`




# Variable-level Monitoring

Please see the example [model_monitoring.py](https://github.com/dstarkey1/model_data_storage_template/blob/main/model_monitoring.py) script for suggested guidance on input feature (or variable-level) monitoring of general machine learning model.

In general, the expeceted output of an ML model change typically due one or both of the following:

* Changes in the input features themselves (due to data ingestion issues) leading to bad (e.g. 0 or nan) values for a sustained period.
* Changes in population behaviour (causing trend changes to the input features).
* Changes in the realtionship between the features and the target.

The top two of these issues can be quickly identified with strong variable-level-monitoring (VLM). This can act as an early warning system to alert the user to changes in trend, volatility or quality of the model input data.

## Ruptures
The [model_monitoring.py](https://github.com/dstarkey1/model_data_storage_template/blob/main/model_monitoring.py) explores the use of the [ruptures](https://github.com/deepcharles/ruptures) python package to identify changes in timeseries data. This is able to detect data drops and trend changes as shown below. With a few modifications it is also able to detect changes in timeseries volatility.

### Trend / Level Changes

The ruptures package uses a technique known as Pruned Exact Linear Time ([PELT](https://article.sciencepublishinggroup.com/html/10.11648.j.ajtas.20150406.30.html)) to iteratively split a time series into small chunks whose summed rms is minimised. The algorithm requires tuning with a hyper parameter that penalises excess splitting. The figures below highlight its use for level and trend stationarity changes in the timeseries behaviour.

![Alt Text](https://github.com/dstarkey1/model_data_storage_template/blob/main/img/trend_example.png)

### Data Drops

![Alt Text](https://github.com/dstarkey1/model_data_storage_template/blob/main/img/dropoff.png)



### UPGRADE: Volatility Changes

The PELT technique in practice appears to fail here due to the absence of a level change. We can however clearly see large volatility changes to the underlying population behaviour. We can modify the ruptures technique to instead analyse the rolling standard deviation. While this requires an additional hyper parameter (the window size and additional split penalty), we see the algorithm now has the ability to identify volaitility changes.

![Alt Text](https://github.com/dstarkey1/model_data_storage_template/blob/main/img/volatility_example.png)





## VLM Result Summaries

Ideally, we sugget results of any VLM should be reported concisely in a single document, pdf, pptx format with example format ![here](https://github.com/dstarkey1/model_data_storage_template/blob/main/img/variable_level_monitoring.pdf)
. The corresponding code to generate these results is available in [model_monitoring.py](https://github.com/dstarkey1/model_data_storage_template/blob/main/model_monitoring.py).



# Pre-commit Hooks:

As an asside, [pre-commit](https://pre-commit.com/) hooks are a great way to automate many of the standard tasks required to maintain code in a git repo. These include things such as auto-formatting code to a specific spacing requirements (i.e. using `python -m black ./*`). It can also cover things like running of unit tests. These standard maintenance and continuous integration tasks of a project.


## Installation Guide


##### 1. Install pre-commit

`pip install pre-commit`

This should also be added to the `requirents.txt` file of the git project currently in use.


##### 2. create a file named .pre-commit-config.yaml

`touch .pre-commit-config.yaml`

This should be created in the project root directory. Edit this file to include the following:

```
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v2.3.0
    hooks:
    -   id: check-yaml
    -   id: end-of-file-fixer
    -   id: trailing-whitespace
-   repo: https://github.com/psf/black
    rev: 21.12b0
    hooks:
    -   id: black
```

Any number of auto pre commit processes can be defined in this .yaml file and tailored to the specific needs of the project.


##### 3. Install the git hook scripts

`pre-commit install`



##### 4. Commit to your project as normal

All the pre commit processes defined in the yaml file will now run automatically every commit! An example commit push sequence will look like the following.

![Alt Text](https://github.com/dstarkey1/model_data_storage_template/blob/main/img/example_precommit.png)


We can see that the auto-formatting defined in the .yaml file now runs without prompt from the user.
