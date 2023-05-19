var igvDiv = document.getElementById("igv-div");
      // Set up browser on the locus
      // of MYC as an arbitrary starting
      // point
      var options =
        {
            genome: "hg38",
            locus: "chr8:127,736,588-127,739,371"
        };

        // Declare variable to be later
        // referenced by loadTracks()
        var IGVBROWSER = 0;

         // Initialise IGV browser
        igv.createBrowser(igvDiv, options)
                .then(function (browser) {
                    console.log("Created IGV browser");
                    // Assign browser to declared variable
                    IGVBROWSER = browser;
                })
