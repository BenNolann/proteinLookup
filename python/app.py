#!/usr/bin/env python3

from AWS_login import connect_to_db
import pandas as pd
from shiny import App, render, ui, reactive


#####################
# Import the experiments table into memory
# Populate dropdown boxes etc for it
# Then based on user selection, grab the 
# necessary peaks data using MySQL and 
# AWS
#####################
def samples_experiments():
    conn = connect_to_db()
    # SQL Query for the data
    stmt = f"""
    SELECT *
    FROM bnolan.all_samples_experiments;
    """
    
    df = pd.read_sql(stmt, con=conn)
    return df

# Grab experimental data
experiments = samples_experiments()


# Set up app UI
app_ui = ui.page_fluid(
    ui.h2("ChIP Binding Experiment Webtool"),
    ui.input_select(id="select_antibody", 
                    label="Selected antibody:",
                    choices=list(experiments['antibody'].unique()), 
                    selected="CTCF"),
    ui.hr(),
    ui.input_action_button("load", "Load Peaks!"),
    ui.output_text(id="out_db_details"),
    ui.output_table(id="out_table"), #display table for all selected experiments for antibody
    ui.output_table(id="out_peaks_table") #show all peaks for selected antibody

)

# Set up app Server
def server(input, output, session):
    @reactive.Calc
    def db_info():

        conn = connect_to_db()
        stmt = "SELECT VERSION();"
    
        cursor = conn.cursor()
        cursor.execute(stmt)
        res = cursor.fetchall()
        conn.close()
        string = "MySQL Version: " + str(res[0]) + " | Hosted Using Amazon Web Services"
        return string

    @reactive.Calc
    @reactive.event(input.load) # Take a dependency on the button
    def samples_peaks():
        
        conn = connect_to_db()
        # SQL Query for the data
        sample_antibody = input.select_antibody()
        stmt = f"""
        SELECT chr, start, stop, strength
        FROM bnolan.all_samples_peaks
        JOIN bnolan.all_samples_experiments 
        ON all_samples_experiments.study_id = all_samples_peaks.study_id
        WHERE all_samples_experiments.antibody='{sample_antibody}';
        """

        df = pd.read_sql(stmt, con=conn)
        return df 


    @output
    @render.text
    def out_db_details():
        return f"Current database: {db_info()}"

    @output
    @render.table
    def out_table():
        # Uncomment when utilizaing the data() function
        # to pull peaks data from AWS
        #return data()
        anti = input.select_antibody()
        df = experiments.loc[experiments['antibody'] == f'{anti}']
        return df
    
    @output
    @render.table
    def out_peaks_table():
        # Uncomment when utilizaing the data() function
        # to pull peaks data from AWS
        #return data()
        df = samples_peaks()
        return df


app = App(app_ui, server)