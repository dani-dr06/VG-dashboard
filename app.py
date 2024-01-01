from shiny import App, render, ui
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import geopandas as gpd
import numpy as np

plt.style.use('fivethirtyeight')

connection = sqlite3.connect('videogame.db')
cursor = connection.cursor()

# create list of years for dropdown menu
cursor.execute('''SELECT DISTINCT year_of_release FROM games
               WHERE year_of_release IS NOT null
               ORDER BY year_of_release''')

years = list(cursor.fetchall())
years = [year[0] for year in years]
years.insert(0, 'All')

# create list of publishers for dropdown menu
cursor.execute('''SELECT DISTINCT publisher FROM games
               WHERE publisher IS NOT null
               ORDER BY publisher''')

publishers = list(cursor.fetchall())
publishers = [pub[0] for pub in publishers]
publishers.insert(0, 'All')

# create list of platforms for dropdown menu
cursor.execute('''SELECT DISTINCT platform FROM sales
               WHERE platform IS NOT null
               ORDER BY platform''')

platforms = list(cursor.fetchall())
platforms = [plat[0] for plat in platforms]
platforms.insert(0, 'Any')

world_map = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
regions = world_map[(world_map['continent'].isin(['North America', 'Europe'])) | ( world_map['name'] == 'Japan')].copy()

app_ui =ui.page_fluid(
     ui.panel_title("GameStats"),

    ui.page_navbar(
        # Create sales tab
        ui.nav_panel(
            "Sales",
            ui.row(
                ui.input_selectize('year_sales', 'Select year', years),
                ui.input_selectize('publishers_sales', 'Select Publisher', publishers),
            ),
            ui.panel_main(
                ui.output_plot("map"),
                ui.output_plot("time_series"),
                ui.output_plot("platform_bar_graph"),
                ui.output_plot("genre_bar_graph"),
                

                ui.row(ui.input_text("search", "Search Sales Table")),
                ui.layout_sidebar(
                    ui.panel_sidebar(
                        ui.navset_pill(
                            ui.nav_panel("Ratings",
                                         ui.output_plot("rating_viz")),

                            ui.nav_panel("Publishers",
                                         ui.output_plot("publishers_viz")),

                            ui.nav_panel("Developers",
                                         ui.output_plot("devs_viz")),
                        )
                    ),
                    ui.panel_main(ui.output_data_frame("df"))
                )
                )
        ),

        # Create Reviews tab
        ui.nav_panel(
            "Reviews",
            ui.panel_main(
                ui.output_plot("score_sales_corr"),
                ui.output_plot("pubreviews_plot"),
                ui.input_text("search_rev", "Search Reviews Table"),
                ui.output_data_frame("df_rev")
            )
        ),

    )


)

def server(input, output, session):

    @output
    @render.data_frame
    def df():
        cursor.execute('''SELECT g.game_id, name, year_of_release, platform, genre, developer, publisher, rating, global_sales,
                       na_sales, eu_sales, jp_sales
                       FROM games AS g
                       INNER JOIN sales AS s ON g.game_id = s.game_id
                       WHERE g.game_id LIKE ? OR name LIKE ?
                       OR year_of_release LIKE ? OR platform LIKE ?
                       OR genre LIKE ? OR developer LIKE ?
                       OR publisher LIKE ? OR rating LIKE ?
                       ''', (f'%{input.search()}%', f'%{input.search()}%', f'%{input.search()}%', f'%{input.search()}%',
                            f'%{input.search()}%', f'%{input.search()}%', f'%{input.search()}%', f'%{input.search()}%'))
        colnames = cursor.description
        colnames_list = []

        for row in colnames:
            colnames_list.append(row[0])

        result_df = pd.DataFrame(cursor.fetchall(), columns=colnames_list)
        return result_df
    
    @output
    @render.plot
    def map():
        cursor.execute('''
                       SELECT SUM(na_sales) AS na_sales, SUM(eu_sales) AS eu_sales, SUM(jp_sales) AS jp_sales
                       FROM games AS g
                       INNER JOIN sales AS s ON g.game_id = s.game_id
                       WHERE (year_of_release = ? OR ? = 'All')
                       AND (publisher = ? OR ? = 'All')
                        ''', (input.year_sales(), input.year_sales(), input.publishers_sales(), input.publishers_sales()))
        colnames = cursor.description
        colnames_list = []

        for row in colnames:
            colnames_list.append(row[0])

        result_df = pd.DataFrame(cursor.fetchall(), columns=colnames_list)

        regions.loc[regions['continent'] == 'North America', 'sales'] = result_df['na_sales'].values[0]
        regions.loc[regions['continent'] == 'Europe', 'sales'] = result_df['eu_sales'].values[0]
        regions.loc[regions['name'] == 'Japan', 'sales'] = result_df['jp_sales'].values[0]

        fig, ax = plt.subplots(figsize=(20,8))
        regions.plot(ax=ax, column='sales', cmap='viridis', legend=True, legend_kwds={'label':'Sales (in millions)'})
        ax.set_xticks([])
        ax.set_yticks([])
        fig.suptitle('Video Game Sales by Region - NA, EU, Japan')

        return fig

    @output
    @render.plot
    def time_series():
        cursor.execute('''
                       SELECT year_of_release AS year, SUM(na_sales) AS na_sales, SUM(eu_sales) AS eu_sales, SUM(jp_sales) AS jp_sales,
                       SUM(global_sales) as global_sales
                       FROM games AS g
                       INNER JOIN sales AS s ON g.game_id = s.game_id
                       WHERE (publisher = ? OR ? = 'All') AND year_of_release IS NOT NULL
                       GROUP BY year_of_release
                        ''', (input.publishers_sales(), input.publishers_sales()))
        colnames = cursor.description
        colnames_list = []

        for row in colnames:
            colnames_list.append(row[0])

        result_df = pd.DataFrame(cursor.fetchall(), columns=colnames_list)

        fig= plt.figure(figsize=(15,8))
        year_ticks = np.arange(1980, 2025, 5)
        for sale in ['global_sales','na_sales', 'eu_sales', 'jp_sales']:
             plt.plot(result_df['year'], result_df[sale], label=sale, marker='o')

        fig.suptitle(f'Sales Time-Series - Publisher: {input.publishers_sales()}')
        plt.xlabel('Year')
        plt.ylabel('Sales (in millions)')
        plt.legend()
        plt.xticks(year_ticks)
        plt.tight_layout()
        return fig
    
    @output
    @render.plot
    def platform_bar_graph():
        cursor.execute('''
                       SELECT platform, SUM(na_sales) AS na_sales, SUM(eu_sales) AS eu_sales, SUM(jp_sales) AS jp_sales,
                       SUM(global_sales) AS global_sales
                       FROM games AS g
                       INNER JOIN sales AS s ON g.game_id = s.game_id
                       WHERE (year_of_release = ? OR ? = 'All')
                       AND (publisher = ? OR ? = 'All')
                       GROUP BY platform
                       ''', (input.year_sales(), input.year_sales(), input.publishers_sales(), input.publishers_sales()))
        colnames = cursor.description
        colnames_list = []

        for row in colnames:
            colnames_list.append(row[0])

        result_df = pd.DataFrame(cursor.fetchall(), columns=colnames_list)

        fig = plt.figure()
        plt.bar(result_df['platform'], result_df['global_sales'])
        fig.suptitle(f'Platform Sales by Year and Platform\n Publisher(s): {input.publishers_sales()}, Year(s): {input.year_sales()}')
        plt.ylabel('Sales (in millions)')
        plt.xticks(fontsize=8)

        return fig

    @output
    @render.plot
    def genre_bar_graph():
        cursor.execute('''
                       SELECT genre, SUM(na_sales) AS na_sales, SUM(eu_sales) AS eu_sales, SUM(jp_sales) AS jp_sales
                       FROM games AS g
                       INNER JOIN sales AS s ON g.game_id = s.game_id
                       WHERE (year_of_release = ? OR ? = 'All')
                       GROUP BY genre
                        ''', (input.year_sales(), input.year_sales()))
        colnames = cursor.description
        colnames_list = []

        for row in colnames:
            colnames_list.append(row[0])

        result_df = pd.DataFrame(cursor.fetchall(), columns=colnames_list)

        fig= plt.figure(figsize=(15,8))
        
        bar_width = 0.25
        bar_positions_na = np.arange(result_df.genre.nunique())
        bar_positions_eu = bar_positions_na + bar_width
        bar_positions_asia = bar_positions_na + 2 * bar_width

        plt.barh(bar_positions_na, result_df['na_sales'], height=bar_width, label='NA')
        plt.barh(bar_positions_eu, result_df['eu_sales'], height=bar_width, label='EU')
        plt.barh(bar_positions_asia, result_df['jp_sales'], height=bar_width, label='Japan')
        plt.yticks(bar_positions_na + bar_width, result_df.genre)

        fig.suptitle(f'Sales by Genre - {input.year_sales()}')
        plt.ylabel('Genre')
        plt.xlabel('Sales (in millions)')
        plt.legend()
        plt.tight_layout()

        return fig

    @output
    @render.plot
    def rating_viz():
        cursor.execute('''
                       SELECT rating, COUNT(rating) AS number_of_games
                       FROM games AS g
                       WHERE rating IS NOT NULL
                       GROUP BY rating
                       ORDER BY number_of_games DESC
                       LIMIT 3
                        ''')
        colnames = cursor.description
        colnames_list = []

        for row in colnames:
            colnames_list.append(row[0])

        result_df = pd.DataFrame(cursor.fetchall(), columns=colnames_list)

        fig = plt.figure()
        plt.pie(result_df['number_of_games'], labels=result_df['rating'], autopct='%1.1f%%')
        plt.suptitle('Top 3 ESRB Ratings')

        return fig
    
    @output
    @render.plot
    def publishers_viz():
        cursor.execute('''
                       SELECT publisher, SUM(global_sales) AS sales
                       FROM games AS g
                       INNER JOIN sales AS s ON g.game_id = s.game_id
                       WHERE publisher IS NOT NULL
                       GROUP BY publisher
                       ORDER BY sales DESC
                       LIMIT 10
                        ''')
        colnames = cursor.description
        colnames_list = []

        for row in colnames:
            colnames_list.append(row[0])

        result_df = pd.DataFrame(cursor.fetchall(), columns=colnames_list)

        fig = plt.figure(figsize=(15,8))
        plt.barh(result_df['publisher'], result_df['sales'])
        plt.suptitle('Top 10 Publishers by Sales')
        plt.yticks(fontsize=8)
        plt.xticks(np.arange(0, 2500, 500), fontsize=8)
        plt.xlabel('Sales (millions)', fontsize=12)

        return fig
    
    @output
    @render.plot
    def devs_viz():
        cursor.execute('''
                       SELECT developer, SUM(global_sales) AS sales
                       FROM games AS g
                       INNER JOIN sales AS s ON g.game_id = s.game_id
                       WHERE developer IS NOT NULL
                       GROUP BY developer
                       ORDER BY sales DESC
                       LIMIT 10
                        ''')
        colnames = cursor.description
        colnames_list = []

        for row in colnames:
            colnames_list.append(row[0])

        result_df = pd.DataFrame(cursor.fetchall(), columns=colnames_list)

        fig = plt.figure(figsize=(15,8))
        plt.barh(result_df['developer'], result_df['sales'])
        plt.suptitle('Top 10 Developers')
        plt.yticks(fontsize=8)
        plt.xticks(np.arange(0, 2000, 500), fontsize=8)
        plt.xlabel('Sales (millions)', fontsize=12)

        return fig
    
    @output
    @render.plot
    def score_sales_corr():
        cursor.execute('''
                       SELECT g.game_id, name, year_of_release, genre, developer, publisher, critic_score,
                       SUM(global_sales) AS global_sales
                       FROM games AS g
                       INNER JOIN reviews AS r ON g.game_id = r.game_id
                       INNER JOIN sales AS s ON g.game_id = s.game_id
                       GROUP BY g.game_id
                        ''')
        colnames = cursor.description
        colnames_list = []

        for row in colnames:
            colnames_list.append(row[0])

        result_df = pd.DataFrame(cursor.fetchall(), columns=colnames_list)

        fig = plt.figure()
        colors = np.random.rand(result_df.shape[0])
        plt.scatter(result_df['critic_score'], result_df['global_sales'], c=colors, edgecolors='black')
        plt.xlabel('Critic Review Scores')
        plt.ylabel('Global Sales (in millions)')
        plt.suptitle('Critic Scores and Sales Correlation')
        

        return fig
    
    @output
    @render.plot
    def pubreviews_plot():
        cursor.execute('''
                       SELECT publisher, AVG(critic_score) AS avg_critic_score
                       FROM games AS g
                       INNER JOIN reviews AS r ON g.game_id = r.game_id
                       WHERE publisher IS NOT NULL
                       GROUP BY publisher
                       ORDER BY avg_critic_score DESC
                       LIMIT 20
                        ''')
        colnames = cursor.description
        colnames_list = []

        for row in colnames:
            colnames_list.append(row[0])

        result_df = pd.DataFrame(cursor.fetchall(), columns=colnames_list)

        fig = plt.figure(figsize=(15,8))
        plt.barh(result_df['publisher'], result_df['avg_critic_score'], color='green')
        plt.suptitle('Publishers with Highest Avg Scores')
        plt.yticks(fontsize=8)
        plt.xlabel('Critic Score', fontsize=12)

        return fig
    
    @output
    @render.data_frame
    def df_rev():
        cursor.execute('''SELECT g.game_id, name, year_of_release, genre, developer, publisher, rating, critic_score
                       FROM games AS g
                       INNER JOIN reviews AS r ON g.game_id = r.game_id
                       WHERE g.game_id LIKE ? OR name LIKE ?
                       OR year_of_release LIKE ?
                       OR genre LIKE ? OR developer LIKE ?
                       OR publisher LIKE ? OR rating LIKE ?
                       ''', (f'%{input.search_rev()}%', f'%{input.search_rev()}%', f'%{input.search_rev()}%', f'%{input.search_rev()}%',
                            f'%{input.search_rev()}%', f'%{input.search_rev()}%', f'%{input.search_rev()}%', ))
        colnames = cursor.description
        colnames_list = []

        for row in colnames:
            colnames_list.append(row[0])

        result_df = pd.DataFrame(cursor.fetchall(), columns=colnames_list)
        return result_df

app = App(app_ui, server)

#cursor.close()
#connection.close()