# Redistricting Moneyball

Code for the Princeton Gerrymandering Project's model to identify races where voters have the most leverage to prevent partisan gerrymandering in 2021. Our findings are in this [Redistricting Moneyball Map](https://election.princeton.edu/data/moneyball/). Below is a file dictionary as well as a brief methodology. We also link to [a more in-depth methodlogy](https://docs.google.com/document/d/1iNWxfLuYnP_TpYXfqx_yK7wopI6qji6QgCvEZYtiS6g/edit?usp=sharing).

## File Dictionary

Short descriptions of each python file in the repository.

- cnalysis_forecasts_2018.py
  - Analyze historical accuracy of handicapped estimates
- cnalysis_input_components.py
  - Generates handicap forecasting input data
  - Fixes incumbency errors, adds cvap by district, creates a turnout estimate, and adds old election results
- density.py
  - Classify each state legislative district into rural, exurban, suburban, and urban based on population density
- district_areal_interpolation.py
  - Assign relevant congressional district to each state upper chamber legislative district
  - Assign relevant state upper chamber district to each state lower chamber legislative district
  - Assignments are based on overlapping area
- economist_forecasts.py
  - Scrape statewide election forecasts from the economist
- foundations_blending.py
  - Test how to blend foundations forecast and CNalysis forecasts
- foudnations_input_components.py
  - Generate foundations model input data
  - Puts together historical election results
- foundations_prediction_2020.py
  - Predict margin of each relevant state legislative race using foundations model
- foundations_residuals_2020.py
  - Evaluate differences between foundations model and CNalysis model
- historical_presidential_results.py
  - Extract historical presidential results by state legislative district
- incumbency_2016_and_2018.py
  - Identify incumbents in 2016 and 2018
- preprocess.py
  - Execute all necessary code from other files before running the model
- redistricting_moneyball.py
  - Calculate statewide results for power of a vote
- update_cnalysis_forecasts.py
  - Add updates provided by CNalsysis to their ratings
- voter_power.py
  - Functions to assist calculating voter power when executing redistricting_moneyball.py
- wikipedia_lower_chamber_incumbency.py
  - Extract current incumbency from wikipedia for lower chambers
- wikipedia_upper_chamber_incumbency.py
  - Extract current incumbency from wikipedia for upper chambers

## Dependencies

- [Chrome Driver](https://chromedriver.chromium.org/downloads)
- BeautifulSoup
- geopandas
- numpy
- pandas
- scipy
- selenium
- sklearn
- titlecase
- tqdm
- webdriver

## Brief Methodology

<b>Step 1: In each state, determine which 2020 electoral outcomes would give neither party the power to enact a partisan gerrymander.</b> This is determined by the redistricting protocol set in the state’s constitution. In many states, the two chambers of the state legislature draw the new districts, the governor may veto the plan, and the state legislature can override a veto with a supermajority. As a result, a state will have bipartisan redistricting as long as (1) one party does not control the governorship and both chambers of the state legislature and (2) one party does not have supermajorities in both chambers of the state legislature. Some states have no governor’s veto (e.g. NC), and we adjust the desired electoral outcomes accordingly. We assume that states with an independent redistricting commission (e.g. AZ) will not enact partisan gerrymanders. We focus on congressional gerrymandering and not state legislative gerrymandering, but it turns out that many of the high-leverage states have similar laws for the two processes.

<b>Step 2: In each state, determine the likelihood of an electoral outcome that results in bipartisan control of redistricting.</b> This is not so easy; most forecasts for national elections rely heavily on public polling, but this data is not available for state legislature races. Furthermore, each state has tens or hundreds of small districts, each of which has different candidates and uncertain local dynamics. For this reason, we rely heavily on the race ratings of CNalysis, the only organization that offers comprehensive ratings for individual state legislature races. The group, led by Chaz Nuttycombe, looks at statewide election results in each district, adjusts for the effect of incumbent popularity, researches challengers to assess their quality, goes through campaign finance reports, and predicts demographic trends.

Our model of state legislature elections takes as input the CNalysis race ratings, which consist of a favored party and a confidence level of “Uncontested,” “Safe,” “Lean,” “Tilt,” or “Toss-Up” (no favored party for Toss-Up). We then incorporate results from recent state legislature and presidential elections, which slightly differentiates districts with the same rating. Next, we model uncertainty in the outcome of each race, accounting for the possibility of a uniform shift across the state or among urban/suburban/rural voters. Putting all of this together, we can calculate the probability that the state legislature elections result in bipartisan control over redistricting.

<b>Step 3: In each district in a state, find the amount that a single new vote impacts the bipartisan control probability.</b> We go through every district and run the model from step 2 after adding one to the expected number of votes for a given party. The change in probability gives an estimate of the chances that a given voter in the district will cast the consequential vote for bipartisan redistricting.

<b>Step 4: Quantify the effect across different states.</b> Partisan gerrymandering is more impactful in more populous states, since it affects more seats in U.S. Congress. We estimate that these effects are about proportional to the number of congressional districts minus one, so we multiply the voter powers from step 3 by this number (based on projected 2020 Census results). After normalizing to a 0-100 scale, we get a list of the relative redistricting voter powers to prevent partisan gerrymandering.
