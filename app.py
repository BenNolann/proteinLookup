#!/usr/bin/env python3

from AWS_login import connect_to_db
import pandas as pd
from shiny import App, render, ui, reactive
from htmltools import *
from pathlib import Path
import json


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
    # JavaScript for IGV browser
    head_content(
        tags.script(src = "https://igv.org/web/release/2.8.6/dist/igv.min.js"),
    ),

    ui.h2("ChIP Binding Experiment Webtool"),
    ui.div(id = "igv-div"),
    tags.script((Path(__file__).parent / "igv.js").read_text()),
    ui.output_ui("IGV_tracks"),

    # in body
    ui.input_select(id="select_antibody", 
                    label="Selected antibody:",
                    choices=list(experiments['antibody'].unique()), 
                    selected="CTCF"),
    ui.hr(),
    ui.input_action_button("load", "Load Peaks!"),
    ui.output_text(id="out_db_details"),
    ui.output_table(id="out_table"), #display table for all selected experiments for antibody
    #ui.output_table(id="out_peaks_table") #show all peaks for selected antibody
)

# Set up app Server
def server(input, output, session):

    # Load track containing all bedgraph coordinates for 
    # selected antibody
    @output
    @render.ui
    @reactive.event(input.load) # Take a dependency on the button
    async def IGV_tracks():
        # - Read in bedgraph of all peaks for selected antibody
        peaks = samples_peaks()
        # - Rename columns for IGV
        peaks.rename(columns = { 'stop' : 'end', 
                                'strength' : 'value', 
                                'study_id' : 'name' }, 
                                inplace=True)
        # - Convert to JSON format for IGV
        jsonfile = peaks.to_json(orient='records')
        json2 = json.loads(jsonfile)

        sample_antibody = input.select_antibody()

        # - Create JavaScript call to loadTrack function
        # using JSON bedgraph 
        tracks = tags.script(HTML(
            f"""

            var bedFeatures = {json2}

            var config = \u007b
                        format: "bed",
                        name: "{sample_antibody}",
                        type: "annotation",
                        features: bedFeatures,
                        indexed: false,
                        displayMode: "SQUISHED",
                        sourceType: "file",
                        // color: "black",
                        height: 50
                        \u007d;

            IGVBROWSER.loadTrack(config)
            """

               )                
        )
        # Return the <script/> javascript call
        # and place in the HTML body
        return tracks


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
        SELECT chr, start, stop, strength, bnolan.all_samples_peaks.study_id
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
    
    # @output
    # @render.table
    # def out_peaks_table():
    #     # Uncomment when utilizaing the data() function
    #     # to pull peaks data from AWS
    #     #return data()
    #     df = samples_peaks()
    #     return df

app = App(app_ui, server)