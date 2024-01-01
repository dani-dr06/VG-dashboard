# GameStats: Video Game Sales and Reviews Dashboard

The objective of this project was to design a web application driven by a SQLite database where the user could interact with the data through visualizations and tables, and, therefore, create a visually-appealing way for the user to understand the dataset and obtain insights from the data.

The following Python libraries were used to make this dashboard:

1. Sqlite3
2. PyShiny
3. Pandas
4. Numpy
5. Geopandas
6. Matplotlib

## [Dataset](https://www.kaggle.com/datasets/thedevastator/video-game-sales-and-ratings)
The data, which was obtained through Kaggle, contains a few decades worth of information about video game sales and reviews. The raw data contains the following columns:

- Name: Name of the video game
- Platform: Platform for the game
- Year_of_Release: Year in which the game was released
- Genre: Genre of the game
- Publisher: Company that published the game
- NA_Sales: Sales of the game in North America, in millions
- EU_Sales: Sales of the game in Europe, in millions
- JP_Sales: Sales of the game in Japan, in millions
- Other_Sales: Sales of the game in other regions, in millions
- Global_Sales: Global sales of the game, in millions
- Critic_Score: Average score given by critics
- Critic_Count: Critics who reviewed the game
- User_Score: Average score given by users
- User_Count: Users who reviewed the game
- Developer: Company that developed the game
- Rating: ESRB rating of the game


The dataset does contain some columns with missing values (which are identified in the Create-db notebook), so I imputed/handled some columns for which I thought it made sense to handle said missing values. For example, there were a couple of records which had null values for the game name column and almost all other columns, making it difficult to get any useful information out of those two records, so they were dropped. For games with missing values with the developer, I decided it was worth it to use the publisher as the developer as well, since many games have the same publisher and developer. However, there were other columns for which I decided it made no sense to impute missing values (e.g., year of release).

## Creating the database
The first step towards completing this project was to transform the raw data into the sqlite database that would be used by the webapp.

### Database Schema
1. Video Games table

    - Fields: Game_ID, Name, Year_of_Release, Genre, Rating, Developer, Publisher
    - PK Game_ID
    - Unique Constraint: Game_ID, Title, Year (since a game can be remastered or released again at a later date) 

2. Sales table

    - Fields: Game_ID, Platform, NA_Sales, EU_Sales, JP_Sales, Other_Sales, Global_Sales
    - PK Game_ID, Platform, Year_of_Release
    - FK Game_ID references Game_ID from Games Table

3. Reviews table

    - Fields: Review_ID , Game_ID, Critic_Score
    - PK Review_ID
    - FK Game_ID references Game_ID from Games Table
  
## Webapp Design

The webapp contains two tabs, one for sales and one for reviews. The idea behind the reviews tab was to create a way for the user to understand the correlation between critic reviews and game sales. However, since the critic reviews had a very large amount of missing values that were filled in with the average score, the result is hard to interpret, which is one of the aspects to improve upon in this project. On the other hand, the sales tab includes sales data about the main regions included in the dataset: North America, Europe, and Japan. In addition, the dashboard user can see other information such as a time series of sales, information about sales according to platform, and sales according to genre. These visualizations contain interactive components, where the visualizations can change according to the year and/or publisher filters selected, as I thought that it would be an interesting idea to understand sales over time by publisher if desired.
