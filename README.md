# Redistricting Moneyball

## File Dictionary

## Brief Methodology

<b>Step 1: In each state, determine which 2020 electoral outcomes would give neither party the power to enact a partisan gerrymander.</b><br>This is determined by the redistricting protocol set in the state’s constitution. In many states, the two chambers of the state legislature draw the new districts, the governor may veto the plan, and the state legislature can override a veto with a supermajority. As a result, a state will have bipartisan redistricting as long as (1) one party does not control the governorship and both chambers of the state legislature and (2) one party does not have supermajorities in both chambers of the state legislature. Some states have no governor’s veto (e.g. NC), and we adjust the desired electoral outcomes accordingly. We assume that states with an independent redistricting commission (e.g. AZ) will not enact partisan gerrymanders. We focus on congressional gerrymandering and not state legislative gerrymandering, but it turns out that many of the high-leverage states have similar laws for the two processes.

Step 2: In each state, determine the likelihood of an electoral outcome that results in bipartisan control of redistricting. This is not so easy; most forecasts for national elections rely heavily on public polling, but this data is not available for state legislature races. Furthermore, each state has tens or hundreds of small districts, each of which has different candidates and uncertain local dynamics. For this reason, we rely heavily on the race ratings of CNalysis, the only organization that offers comprehensive ratings for individual state legislature races. The group, led by Chaz Nuttycombe, looks at statewide election results in each district, adjusts for the effect of incumbent popularity, researches challengers to assess their quality, goes through campaign finance reports, and predicts demographic trends.

Our model of state legislature elections takes as input the CNalysis race ratings, which consist of a favored party and a confidence level of “Uncontested,” “Safe,” “Lean,” “Tilt,” or “Toss-Up” (no favored party for Toss-Up). We then incorporate results from recent state legislature and presidential elections, which slightly differentiates districts with the same rating. Next, we model uncertainty in the outcome of each race, accounting for the possibility of a uniform shift across the state or among urban/suburban/rural voters. Putting all of this together, we can calculate the probability that the state legislature elections result in bipartisan control over redistricting.

Step 3: In each district in a state, find the amount that a single new vote impacts the bipartisan control probability. We go through every district and run the model from step 2 after adding one to the expected number of votes for a given party. The change in probability gives an estimate of the chances that a given voter in the district will cast the consequential vote for bipartisan redistricting.

Step 4: Quantify the effect across different states. Partisan gerrymandering is more impactful in more populous states, since it affects more seats in U.S. Congress. We estimate that these effects are about proportional to the number of congressional districts minus one, so we multiply the voter powers from step 3 by this number (based on projected 2020 Census results). After normalizing to a 0-100 scale, we get a list of the relative redistricting voter powers to prevent partisan gerrymandering.
