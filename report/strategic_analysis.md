# Task 2 - Strategic Analysis

## Q8. The Hiring Request

**Decision: do not approve eight new agents.** The four-week forecast produces three hub-level shortfalls before transfers: H01 needs two more agents, H03 one, and H04 two. H02 and H05 have forecast surplus capacity, but transfer rules restrict moves to the same cluster and only permit moves out of hubs whose pre-move Week 2 utilisation is below 75%.

### Hub-by-hub recommendation

| Hub | Current active | Peak forecast requirement (Q7) | Recommendation | Incremental first-month cost |
|---|---:|---:|---|---:|
| H01 Greenfield | 10 | 12 | Transfer two Fixed agents from H02. | BDT 4,000 transfer fees |
| H02 Lakeview | 11 | 8 | Donor hub. Move A1018 and A1015 to H01; nine agents remain, still above the peak requirement. | No incremental cost |
| H03 Riverside | 12 | 13 | Do not add a permanent agent initially. Launch the hold-reduction programme and monitor its 14-day ramp. | BDT 15,000 programme |
| H04 Hillcrest | 9 | 11 | Hire two Fixed agents. This is the highest-priority permanent staffing gap. | BDT 43,800 salary + hiring fees |
| H05 Brookside | 11 | 10 | No hire. Keep the buffer and address the three high-return agents. H05 cannot transfer to a shortage hub outside Cluster C. | No incremental cost |
| H06 Westwood | 9 | 9 | No staffing change. | No incremental cost |

H02's Week 2 utilisation is 56.17%, and H05's is 71.49%, so both are eligible donor hubs. Only H02 can help H01 within Cluster A. H05 cannot solve H01/H03/H04 shortages because transfers are limited to the same cluster; H06 does not need the spare agent.

### Transfer candidates

- **A1018 - Lorus Brannick (Fixed):** 270 deliveries from 291 assigned attempts (92.78%); 9 returns (3.09%).
- **A1015 - Toren Larkin (Fixed):** 308 deliveries from 339 assigned attempts (90.86%); 9 returns (2.65%).

Both are Active H02 agents and can move to H01 within Cluster A. The one-time transfer cost is BDT 2,000 each.

### Why Riverside needs an operational intervention

H03 recorded 874 Week 2 holds, of which 563 (64.42%) were agent-side. Late Dispatch alone accounted for 312 holds. Its attempts-per-order rate rose from 1.298 in Week 1 to 1.393 in Week 2. Adding an agent could hide the process issue rather than fix it.

The hold-reduction programme costs BDT 15,000 per hub and is modelled to remove 50% of agent-side holds at full effect after 14 days. Under a linear ramp assumption from 27 October:
- Week 1: about 70 holds avoided; H03 projected utilisation is 87.9% of standard capacity.
- Week 2: about 215 holds avoided; utilisation is 86.1%.
- Week 3: about 289 holds avoided; utilisation is 84.5%.
- Week 4: about 283 holds avoided; utilisation is 82.8%.

The first two weeks sit above the 85% planning target but below the 100% standard workload. This is a managed temporary exception, not a claim that the 85% target is met immediately.

## Q9. The Budget

**Recommendation: spend BDT 62,800 and retain BDT 7,200 as contingency.** The per-hub incremental-cost allocation is shown in Q8 above; transferred agents remain on the existing payroll, so only the one-time transfer fees are incremental at H01/H02.

| Use | Basis | Amount |
|---|---|---:|
| Fixed salaries for two H04 hires | 2 × BDT 16,900 | BDT 33,800 |
| Hiring fees | 2 × BDT 5,000 | BDT 10,000 |
| Transfers H02 → H01 | 2 × BDT 2,000 | BDT 4,000 |
| H03 hold-reduction programme | One hub | BDT 15,000 |
| **Total** |  | **BDT 62,800** |
| **Unallocated reserve** | BDT 70,000 - BDT 62,800 | **BDT 7,200** |

### Why Fixed hires at H04

The new-agent ramp rule is applied as 60% of the 40-attempt standard for the first seven days (24 attempts/day), then 85% of standard (34 attempts/day) for the rest of the 26 paid working days:
- Monthly attempt capacity estimate: (7 × 24) + (19 × 34) = 814 attempts.
- H04 delivered/assigned rate in the observed period: 87.13%.
- Estimated deliveries per new agent: about 709.
- Fixed pay: BDT 16,900/month.
- Variable pay estimate: (26 × BDT 300) + (709 × BDT 14) = about BDT 17,729/month.

Fixed is estimated to be BDT 829 cheaper per new agent at H04's observed delivery rate.

### Expected return from the Riverside programme

Using H03's Week 2 agent-side hold rate (563 / 2,190 orders), expected programme reductions over the four-week forecast are approximately 856 hold events. At BDT 30 per hold, that represents approximately **BDT 25,682** of direct avoided hold charges. Programme cost is BDT 15,000, so the modelled direct benefit is BDT 10,682 net of programme cost (about 71% net ROI), before valuing the additional 856 attempts of capacity freed by avoiding repeat attempts.

This is a forecast. It assumes the intervention starts on 27 October and ramps linearly to full 50% effect in 14 calendar days. The assessment provides the maximum reduction and time to full effect, but not the precise ramp trajectory.

### Strict-target alternative

If management treats 85% as an absolute cap rather than a planning target, a third agent would be needed at H03 for the forecast. One Variable H03 hire, two Fixed H04 hires and the two H02→H01 transfers would cost approximately BDT 68,036, leaving about BDT 1,964, but the H03 hold programme would not be funded. This option meets the staffing target more conservatively but leaves the agent-side dispatch problem unresolved and gives up the modelled direct hold-charge savings. The recommended plan accepts a short two-week H03 target exception, with a clear trigger to reconsider capacity if actual workload exceeds the standard.

## Q10. The Risks

| Risk | Early indicator | First-two-week trigger / response |
|---|---|---|
| Riverside programme does not reduce agent-side holds | Agent-side holds per order vs 25.71% Week 2 baseline | Track daily and weekly. Confirm the intervention is live and responsible owners are acting. If the reduction trend is not visible by Day 14, add temporary capacity or revise the process. |
| Riverside workload exceeds planned buffer | Attempts per agent per day; 85% target = 34, standard = 40 | Planned programme scenario is about 35.2 and 34.4 attempts/agent/day in Weeks 1 and 2. Escalate if daily average exceeds 40 or backlog/service levels worsen. |
| H04 new hires ramp more slowly than assumed | Assigned attempts per new agent per day | Expect 24/day during first seven days. Pair with experienced agents and escalate if actual productivity is materially below the ramp assumption. |
| H02 transfer leaves too little reserve | H02 utilisation after two transfers | Nine agents remain against a peak requirement of eight. Monitor daily; do not make a third transfer. |
| H05 returns stay high | Return ratios for A1045, A1046 and A1047 | All three exceed 15%; review route/hand-off/customer evidence and coach using specific return reasons. |
| Forecast is understated | Actual orders and attempts/order vs forecast | Proposed management trigger: investigate when actual daily orders exceed plan by 10% or attempts/order rises 5% above the modelled rate. Re-run staffing weekly. |

**Decision rule:** keep the two H04 hires and H02→H01 transfers. Continue the H03 no-hire approach only while workload remains below the 40-attempt standard and the hold programme is showing measurable progress. Use the BDT 7,200 reserve only against an observed trigger, not as an automatic hiring pool.
