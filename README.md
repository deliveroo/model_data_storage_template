# Test Data Storage Guidance

This repo suggests guideline frameworks for effectively storing training / test / validation sets for our forecasting projects. 



## Option A: S3 Bucket:

![Alt Text](https://github.com/dstarkey1/model_data_storage_tutorial/blob/main/img/s3_img.png)


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


![Alt Text](https://github.com/dstarkey1/model_data_storage_tutorial/blob/main/img/lfs_img.png)

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



