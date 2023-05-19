#!/usr/bin/env python3

# Import AWS login connection from
# local file AWS_login.py
from AWS_login import connect_to_db

# Import the shiny module for
# creation of Python for
# Shiny application
from shiny import App, render, ui, reactive

# Import multiple packages for
# data and string handling
import pandas as pd
from htmltools import *
from pathlib import Path
import json


#####################
# Connect to AWS database using connect_to_db()
# and pull all_samples_experiments table
# Read into pandas dataframe [1000 rows]
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


# Store experiments data as global variable
experiments = samples_experiments()

# Set up app UI
app_ui = ui.page_fluid(
    # JavaScript for IGV browser
    # Necessary to be placed in HEAD
    head_content(
        tags.script(src="https://igv.org/web/release/2.8.6/dist/igv.min.js"),
    ),
    ui.h2("ChIP Binding Experiment Webtool"),
    # DIV naming is used by igv.js
    ui.div(id="igv-div"),
    # Places igv.js JavaScript script in the body of HTML
    tags.script((Path(__file__).parent / "igv.js").read_text()),
    # This UI is the javascript for the loadTracks() IGV function
    # to update the IGV browser with user selected
    # antibody peaks data
    ui.output_ui("IGV_tracks"),
    # Dropdown menu for antibody selection
    ui.input_select(id="select_antibody",
                    label="Selected antibody:",
                    # Obtain all unique antibodies used across
                    # all experiments
                    choices=list(experiments['antibody'].unique()),
                    selected="CTCF"),
    ui.hr(),
    ui.input_action_button("load", "Load Peaks!"),
    # Prints AWS database version to screen
    ui.output_text(id="out_db_details"),
    # Print table of all experiments data for
    # the selected antibody
    ui.output_table(id="out_table")
)


# Set up app Server
def server(input, output, session):

    # Load track containing all bed coordinates for
    # selected antibody
    @output
    @render.ui
    @reactive.event(input.load)  # Run when button is pressed
    def IGV_tracks():
        # Read in bedgraph of all peaks for selected antibody
        peaks = samples_peaks()
        # Rename columns for IGV compatibility
        peaks.rename(columns={'stop': 'end',
                              'strength': 'value',
                              'study_id': 'name'}, inplace=True)
        # Convert to JSON format for IGV
        jsonfile = peaks.to_json(orient='records')
        json2 = json.loads(jsonfile)

        # Grab the antibody of interest for labeling
        sample_antibody = input.select_antibody()

        # Create JavaScript call to loadTrack function
        # using JSON bed file
        # \u007b and \u007d are used in place of
        # {      and  } to allow the use of f-string
        # replacement
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
        # for place in the HTML body
        return tracks

    # Return database information as string
    @reactive.Calc
    def db_info():

        conn = connect_to_db()
        stmt = "SELECT VERSION();"

        cursor = conn.cursor()
        cursor.execute(stmt)
        res = cursor.fetchall()
        conn.close()
        string = "MySQL Version: " + str(res[0]) + \
            " | Hosted Using Amazon Web Services"
        return string

    # Given a selected antibody and the button
    # is pressed to load peaks, perform an
    # inner-join on experiments table and peaks
    # table and return only peaks that match the
    # antibody selected
    @reactive.Calc
    @reactive.event(input.load)  # Run when button is pressed
    def samples_peaks():
        # Connect to database using AWS credentials
        conn = connect_to_db()
        # SQL Query for the peaks data
        sample_antibody = input.select_antibody()
        stmt = f"""
        SELECT chr, start, stop, strength, bnolan.all_samples_peaks.study_id
        FROM bnolan.all_samples_peaks
        JOIN bnolan.all_samples_experiments
        ON all_samples_experiments.study_id = all_samples_peaks.study_id
        WHERE all_samples_experiments.antibody='{sample_antibody}';
        """
        # Read in data as pandas dataframe
        df = pd.read_sql(stmt, con=conn)
        return df

    # Render database information as text output, using
    # string created in db_info()
    @output
    @render.text
    def out_db_details():
        return f"Current database: {db_info()}"

    # Render table with experiments that match
    # selected antibody
    @output
    @render.table
    def out_table():
        anti = input.select_antibody()
        df = experiments.loc[experiments['antibody'] == f'{anti}']
        return df


# Runs the app
app = App(app_ui, server)
