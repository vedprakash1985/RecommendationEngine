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
    | loc_social_closeness   | Path to save the friends of the top "social "users, together with how close they are. <br> Type: Str     |
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

1. `data\output\recom_venues.csv`
    1. For the top users with most checkins, this is the basket of venues based on user-user similarity
    2. Columns are `user_id`, and `venue_id` of the places recommended.
    
1. `data/output/recom_social_venues.csv`
    1. For the top users with most checkins, this is the basket of venues based on their friends (Similarity matrix form the social network)
    2. Columns are `user_id`, and `venue_id` of the places recommended.

1. `data/output/recom_prob_venues.csv`
    1. For the top users with most checkins, this is the basket of venues using Bayesian technique. This will produce probability scores for each recommendations (using Bayes Theorem).
    2. Columns are `user_id`, `venue_id` of the places recommended together with the corresponding `probability`.

1. `data/output/social_checkins.csv`
    1. For the top "social "users, this contains all the user checkins based on the timeperiod.
    2. Use this file and update the Tableau dashboard provided in `data/output/social_users_checkins.twbx`.
    3. The map of the user checkins obtained from the Tableau dashboard is shown here for reference.
    ![alt text](https://github.com/vedprakash1985/RecommendationEngine/blob/master/data/image/checkin_map.png?raw=true)
    
 1. `data/output/social_taste.csv`
     1. For the top "social "users, this contains all their friends and how close they are.
     2. We use the jaccard similarity score between the venues visited by their friends to compute the closeness between them.
     3. This score is between 0 and 1, the higher the score, the more close they are.
     4. Columns of the file are `user_id`, `friend_id` and the closeness between the user and the friend. The higher the distance, the closer they are.
