README

STRUCTURE:
*Optimiser has the Battery + HWT optimisation tool itself*
Unconnected folders:
*Analysis has a few template scripts for analysing the output files from the optimiser*
*Solar Combiner is just a simple script for combining multiple CSVs to one long CSV*

CREDITS:
*most of this was developed by Seb Vetterlein in 2021, some additional stuff was done by Antonin (Tonda) Samal in 2022*
   both University of Bath Final Year Projects

-----------------NEW VERSIONS 2, 3, 4 README BY ANTONIN tonda.samal@gmail.com ------------

Works on Anaconda Python 3.9 on Windows 10

The newly developed code is much messier than the original but bear with me, it kinda works (unless it doesn't, of course)

When there was something changed from the original V1 code, it is typically described in a comment starting with "T:"
This documentation is to get better with time

Please note: the FYP report references 4 versions of the optimiser, however, there are 2 main variant:
	Versions 1 & 2 use an old OF, only optimising the Mixergy hot water tanks
		V2 has only added carbon intensity and price. These two run on the same files (which have to differ from the other versions), denoted as V12 typically
			See the V1 readme file to see the documentation for Version 2. only differences are:
				* naming of key files ends with V12
				* Runnable Code: longRunnerV1_2.py = run the runOptimiserV12 for multiple subsequent days and output its daily summary to CSV
				* fetchCI/CI_rest.py = Carbon Intensity data loader from API, data processed via SystemAssembler as in V1
	
	Versions 3 & 4 use a new OF, minimising total electricity costs & carbon by optimising battery & hot water tanks
		V4 has only added Cost of Throughput (CoT) - thus, it runs on the same files, set CoT to 0 to see V3 results
		The V4 (and V3) is divided into its full scope files and battery-only (battonly) files - to skip lower quality data from Mixergy API
			Following documentation considers the V4 battery+HWT - where significantly different from V1

V4 Updated Contents:
  Runnable Code:
    longRunner-batteryHWT.py
    longRunner-batteryHWT-mixdate.py
    runOptimizer.py
  Configuration Files:
    systemconfig-v5.json
  Supporting Libraries:
    optimizer.py 
    optimiserbattonly.py
    fetchCI/CI_rest.py
    fetchSM/SMfromCSV.py
  Other Files:
    damons_HH_combined_20-22_DUoS_21up_Battery.csv
    owensquare-2020-2022-intervals-30min.csv


Description of the main edited features since V1
----- Runnable Code -----
**longRunner-batteryHWT.py**

From provided start date and duration in days, it loops through all the consecutive days,
  calls runOptimizer on it by modifying a template systemconfig.json file with the
  new dates. Calculates/collects the values to export to the CSV and writes out (to folder "longRun")
It's definitely very beautiful.
All changes to values need to be made in the code. By default, uses systemconfig-v5.json
  as the template system configuration
Optimises battery + HW tanks 
(!! Mixergy API password deleted, email tonda.samal@gmail.com or damon@owensquare.coop to get it (or run battonly versions)!!)
"battonly" version does not include HWT

**longRunner-batteryHWT-mixdate.py**
Same as longRunner-batteryHWT.py but enables using a different day's data for Mixergy tanks 
   - useful when it is missing data from API


**runOptimizer.py**
As in V1, loads system config (by default systemconfig-v5.json), assembles the system with
  SystemAssembler.py, passes the system dict to the optimizer which solves. Extracts
  the optimised power value(s), writes the timeseries data to csv (in folder "output")
Assumes use of exactly 2 HWTs, "ECC" and "Nursery"
"battonly" version does not include HWT

----- Libraries -----
**optimizer.py**
Creates the linear programming problem, then it solves it, outputs data to the runOptimiser
   Creates decision variables: 
      Total simulated OSCE Import & Export
      Battery simulated Import  Export
      Mixergy simulated Power use (for each tank included)
   Set Battery input parameters:
      It is not nice, but all battery parameters are set in this code
      All can be reasonably changed & have in comments their units
   New Objective Function (OF):
      Minimation of (the total cost (inc. carbon cost) of Import - total cost of Export + cost of battery use (throughput))
   Constraints:
      Mixergy has the same as in V1
      Battery uses similar as the Mixergy, has midnight SOC set at the value given by input parameter
      Power balance equation ensures that grid sim export & import are equal with other loads
"battonly" version does not include HWT

----- Configuration Files -----
**systemconfig-v5.json**
JSON object, loaded in to describe a system.

optimization_duration:  Length of optimisation in hours
supply_period_duration: Length of supply period in minutes
carbon_price: input price of carbon in [GBP/tCO2eq] 
   - not necessarily equal to how much the cost will increase / how much carbon will be saved

E: Emissions from the grid = carbon intensity
   loading from API
   by default uses Regional average HH data - for that, it needs the postcode of the building



------------------ORIGINAL VERSI0N 1 README BY SEBASTIAN ---------------

README

Developed for Anaconda Python 3.8.3 on Ubuntu on WSL

Contents:
  Runnable Code:
    bulkRunner.py
    runOptimizer.py
  Configuration Files:
    systemconfig-v3.json
    tank_parameters.json
  Supporting Libraries:
    mixergyModel.py
    optimizer.py
    SystemAssembler.py
    utilities.py
    fetchLJ/lj_rest.py
    fetchLJ/LJfromCSV.py
    fetchPV/PVfromCSV.py
    mixergyio_main/*
  Other Files:
    damons_ECC-gen-meter-intervals.csv
    damons_HH_combined.csv

----- Runnable Code -----
**bulkRunner.py**
From provided starting dates, calculates every combination of tank-day and energy-day
  then calls runOptimizer on it by modifying a template systemconfig.json file with the
  new dates. Calculates/collects the values to export to the CSV and writes out
It's pretty shoddy because this isn't designed for production, just for my benefit.
All changes to values need to be made in the code. By default, uses systemconfig-v3.json
  as the template system configuration

**runOptimizer.py**
Loads system config (by default systemconfig-v3.json), assembles the system with
  SystemAssembler.py, passes the system dict to the optimizer which solves. Extracts
  the optimised power value(s), writes the timeseries data to csv

----- Configuration Files -----
**systemconfig-v3.json**
JSON object, loaded in to describe a system.

optimization_duration:  Length of optimisation in hours
supply_period_duration: Length of supply period in minutes

_I, X, G, tanks_
Each of these can be retrieved from any valid source. Obviously the tanks have to return
  an object with tank descriptions in it, so the entire set of valid sources doesn't apply

_Valid Sources for I, X, G_
Case sensitive
As defined in SystemAssembler.py:
"included": The object whose source is "included" includes a "data" field containing its value
"JSON"    : The object should be loaded from the JSON file path specified in the "filename" field
"LJ_REST" : ALPHA. Using the "date_from" field for the source and the optimization_duration, access the LimeJump REST API and retrieve data for every supply period
              Note LJ supply periods are implicitly 30min long, so fix supply_period_duration. Update the API key in lj_rest.py for access
"LJ_CSV"  : Using the "date_from" field for the source, retrieve LJ supply period data (again, fixed to 30min with provided data) from the file at "filename"
"PV_CSV"  : Fetch PV generation data for the PV4 array from "filename" for optimization_duration from "date_from". implicitly 30minutely with provided data

_Valid sources for tanks_
"included" or "JSON", defined as above
Within tanks, each tank should be defined
Valid tank sources are "included" or "MixergyModel"

"included"    : Expects a corresponding "data" key, with "H" key as list of length (supply-periods in optimization_duration)
"MixergyModel": Access the tank_parameters file at "filename", retrieve the parameters for tank "tankname" and pull API values
                  from "date_from" for optimization_duration. Not supply_period_duration dependent

**tank_parameters.json**
A dictionary, with keys which define the tank name. Each key contains:

  "user_pass": list, [str(username), str(password)] for the Mixergy account connected with this tank
  "tank_id"  : The mixergy tank ID, e.g. MX001224
  "params"   :
     "TANK_LOSSES"           : List of length (length(unusual_periods) + 1) containing Excel-calculated %/s loss rate for default case, unusual_period1, unusual_period2, etc
     "HEATING_TANK_GAIN"     : As above, but for %/kWh as found in Excel
     "heater_power"          :  Heater power in kW
     "supply_period_duration": Should be set to match systemconfig. Shoddy, I know, but I was short on time!
     "unusual_periods"       : Optional. Dictionary containing numbered keys, beginning from 1. Each key defined as:
       "time_from" : time (in 24hr clock) when the special period begins
       "time_to"   : time (in 24hr clock) when the special period ends
                     Note lower numbered periods take priority.

----- Example Configuration -----
**systemconfig-v3.json** - updated to v5
Provides for the dual-tank configuration as discussed in report
{
    "optimization_duration": 24,
    "supply_period_duration": 30,
    "I": {
        "source": "LJ_CSV",
        "filename": "./input_data/damons_HH_combined.csv",
        "date_from": "2021-01-21T00:00:00"
    },
    "X": {
        "source": "LJ_CSV",
        "filename": "./input_data/damons_HH_combined.csv",
        "date_from": "2021-01-21T00:00:00"
    },
    "G": {
        "source": "PV_CSV",
        "filename": "./input_data/damons_ECC-gen-meter-intervals.csv",
        "date_from": "2021-01-21T00:00:00"
    },
    "tanks": {
        "source": "included",
        "data": {
            "ECC": {
                "source": "MixergyModel",
                "filename": "./input_data/tank_parameters.json",
                "tankname": "ECC",
                "date_from": "2021-03-31T00:00:00"
            },
            "Damon": {
                "source": "MixergyModel",
                "filename": "./input_data/tank_parameters.json",
                "tankname": "Damon",
                "date_from": "2021-03-31T00:00:00"
            }
        }
    }
}

**tank_parameters.json**
Passwords have been removed, contact Damon or me if you're trying to run the code
{
    "ECC": {
        "user_pass": ["damon@somewhere.coop", "psw"],
        "tank_id": "MX001224",
        "params": {
            "TANK_LOSSES": [-0.0003726711, -0.0016186246],
            "HEATING_TANK_GAIN" : [6.182967037, 8.091063334],
            "heater_power": 3,
            "supply_period_duration": 30
        },
        "unusual_periods": {
            "1": {
                "time_from": "05:00",
                "time_to": "18:00"
            }
        }
    },
    "Damon": {
        "user_pass": ["damon@somewhere.net", "psw"],
        "tank_id": "MX001896",
        "params": {
            "TANK_LOSSES": [-0.000735962892],
            "HEATING_TANK_GAIN" : [12.26539269],
            "heater_power": 3,
            "supply_period_duration": 30
        }
    }
}
