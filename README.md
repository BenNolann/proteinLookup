# proteinLookup
A Python Shiny web application for the investigation of DNA-binding protein sites.

### Availability
https://bennolan.shinyapps.io/proteinlookup/

### Overview
This application uses data from ChIP-atlas (https://chip-atlas.org/) and is essentially a demonstration of the use of an *IGV* browser, *AWS* for data storage and *Shiny for Python* for web-application development and hosting. 

### File Description

*app.py:* Shiny for Python script that is used to execute the web application. Contains code for User Interface and Server components.
*igv.js:* JavaScript file for the initialization of the embedded Integrated Genome Browser [IGV] in the web-application. 
*requirements.txt:* Required python modules to deploy the application. This file is used by *rsconnect* for the deployment of the web-application to [shinyapps.io](https://www.shinyapps.io/).
*LICENSE:* MIT license for the project. 
*AWS_login.py:* Not included in this repository for security reasons.
*.gitignore:* Ignore files not required for web-application AND ignore the AWS login file. The format of the login file *AWS_login.py* not included in this git repo is:

```{python}
import mysql.connector

# Connect to AWS database

def connect_to_db():
    conn = mysql.connector.connect(
        host = "",
        user = "",
        passwd = "",
        auth_plugin = "",
     )
     return conn
```
