# RecommendationEngine
Build Simple Recommendation Engine and Visualization

## Outline

1. For the top 10 users (with more checkins), build
    1.  A basket of recommendation : venues(places), 
    1.  A list of likely venues (places) the user will visit based on their friends,
    1.  Where they will go next (with probability scores).

1. For the top 10 more “social” users (with more friends),
    1.  Draw the path (with map) of a week/month of users checkins,
    2.  List your friends and how close they are in terms of “taste” (based on venues visited
and ranked)

## Datasets
Obtain the sqlite dataset from the following link: https://mltestpublicdata.s3-ap-southeast-1.amazonaws.com/fsdata.db.zip

Place the file in the data folder, or anywhere as its location will be specified in the configuration file

## Programming language

* Python 3.6
* Packages used
    * Please use the ```requirements.txt``` to create the virtual environment.

## Run Program

1. **Configuration File**.   
    Please update the parameters accordingly in the configuration file found in ```data\config\config.json```.
    | Key     | Description |
    | ----------- | ----------- |
    | topUsers     | The number of top users to consider. <br> Type: Int |
    | DB_path   | Full path of the sqlite database.  <br> Type: Str     |
    | numberRecommendation     | The number of items to choose from the recommendation matrix. <br> Type: Int |
    | loc_recom_venues   | Path to save the basket of venues for the top users with most checkins using user-user similarity. <br> Type: Str     |
    | loc_recom_social_venues   | Path to save the basket of venues for the top users with most checkins based on their friends.  <br> Type: Str     |
    | loc_recom_prob   | Path to save the basket of venues for the top users with most checkins using bayesian technique. This will produce probability scores for each recommendations.  <br> Type: Str     |
    | loc_social_checkins   | Path to save the user checkins for the top "social "users. <br> Type: Str     |
    | start_date   | Date in 'YYYY-MM-DD' format. Consider all user checkins from this date onwards for the top "social "users.  <br> Type: Str     |
    

2. **Run Code**.  
    The general syntax is
    ```python
    python src\main.py -config < path to configuration file >
    ```
    For example, in this case, it will be
    ```python
    python src\main.py -config data\config\config.json
    ```

## Output
The following files will be saved.

1. 
