# Smart Racing Championship

Technical report for Design and Analysis of Algorithms.

The title page is populated from report-details.json using the supplied group
names, registration numbers, Section B and Islamabad campus.

## 1. Introduction and problem statement

The project models a racing circuit as a graph. A player and three deterministic
opponents travel through ordered checkpoints, manage fuel and nitro, and react
to changes in road availability. The implementation aims to connect each
required algorithm to a racing, planning, visualization, or championship task.
The assignment's precise requirements and constraints are retained in
`docs/assignment-specification.md`.

### 1.1 Objectives and scope

The problem is to coordinate navigation, discrete resource decisions and ordered
race events over a changing graph. A shortest geometric route can be unsuitable
when it skips a mandatory checkpoint, exceeds available fuel or uses a closed
road. The solution combines graph search with optimization, deterministic event
processing and common-comparator rankings.

The implemented scope includes three authored circuits, ten ordered checkpoints
and at least two shortcuts per circuit, a human racer with three deterministic
opponents, five required screen functions, twelve mandatory algorithm families,
five experimental studies and all three advanced challenges. Machine learning
and reinforcement learning are not used. The interface brand is REDLINE; the
assignment project title is Smart Racing Championship.

## 2. System architecture and game flow

The shared graph and race engine contain no Pygame rendering. Pygame presents
the main menu, settings, route explorer, racing screen, Algorithm Lab, results,
and standings. Players can switch between an overhead 3D broadcast and a flat
tactical view of the same roads, then review the podium and race classification.
The saved reduced-motion setting applies across screens. The Lab animates sorting,
heap and resource-planning decisions from the same functions as the planner,
race and experiments. Authored JSON circuits and seeded generated circuits are
loaded as adjacency-list graphs. A fixed 1/30-second simulation step separates
the race clock from animation frame rate. See `docs/architecture/decisions.md`
for tuned rules and recovery choices.

### 2.1 Package responsibilities

| Layer | Responsibilities and boundary |
| --- | --- |
| core | Graph, vertex, road and cost-profile records; no rendering dependency. |
| algorithms | Manual traversal, routing, optimization, MST, heap and ranking implementations. |
| tracks, resources, events | Circuit validation/generation, resource recommendations and scheduled effects. |
| game | Racer state, legal actions, opponents, fixed-step simulation and race results. |
| championship | Points, total comparator, season progression and bounded-heap leaders. |
| ui | Input translation, screen navigation, camera, HUD and algorithm-trace playback. |
| experiments and tests | Repeatable measurements and independent correctness checks of the shared functions. |

### 2.2 Game flow

Main Menu -> circuit selection -> Route Planner or Quick Race. Championship
starts a three-venue season. A race progresses from grid countdown through legal
road choices, ordered checkpoints and laps to classification. Championship
results update points and standings before the next venue; the final round
reveals the winner. The Algorithm Lab provides step, play, pause and reset for
plain-data recordings from the shared implementations.

Each simulation step processes due road events before opponent decisions and
movement. The engine updates fuel, nitro, checkpoint progress and finish/DNF
state, and exposes results for display. The renderer observes those results;
changing a camera or playing a trace does not select a race outcome.

## 3. Graph models, assumptions and game rules

### 3.1 Graph and racer records

Vertices identify the start, checkpoints, intersections and services. Edges
identify directed or undirected roads with distance, time, fuel, difficulty,
status, shortcut and obstacle attributes. The route cost is a weighted sum of
normalized distance, time, difficulty-adjusted fuel, difficulty and obstacle
terms. All weights are non-negative. Four route presets use different weights;
their scalar scores use different scales and should not be compared directly.

The current defaults are two laps, a 240-second limit, a 100-unit fuel tank,
up to 40 units per station visit, a three-second stop and an initial nitro
charge. Nitro lasts four simulation seconds, increases speed by 1.5 and doubles
fuel use for the affected portion. The score table and total championship
tie-break order follow the assignment. Unfinished racers receive no points.

### 3.2 Route-cost normalization

For an edge e, the optimized cost is
`wd * distance/100 + wt * effectiveTime/10 + wf * adjustedFuel/10 +
wr * (difficulty - 1)/4 + wo * obstacle/1`. Effective time is base time
multiplied by 1.5 when the edge is restricted; adjusted fuel is base fuel
multiplied by `1 + 0.1 * (difficulty - 1)`. The reference values are fixed
scales for the circuit data, so all five terms are non-negative before
weighting. The displayed cost is the same sum optimized by the router.

| Preset | Distance | Time | Fuel | Difficulty | Obstacle |
| --- | ---: | ---: | ---: | ---: | ---: |
| Balanced | 1 | 1 | 1 | 1 | 1 |
| Speed | 0.2 | 3 | 0.2 | 0.2 | 0.3 |
| Economy | 0.3 | 0.2 | 3 | 0.3 | 0.2 |
| Safety | 0.3 | 0.3 | 0.3 | 3 | 3 |

The speed, economy and safety profiles prioritize their named objective;
balanced weights give every normalized term the same multiplier. These are
design choices, not measurements of the relative value of different units.
Changing reference values or weights can change the selected route, and one
scalar score cannot represent all possible trade-offs.

### 3.3 Assumptions and validation

The graph uses adjacency lists and stable identifiers rather than assuming IDs
are consecutive array positions. Roads may be directed or undirected, and
parallel roads retain separate IDs. Negative, invalid or non-finite costs are
rejected. A blocked road cannot be entered. Checkpoint searches exclude later
mandatory checkpoints on each leg; reaching the final checkpoint is followed by
a legal return to the start. Validation checks the full directed circuit,
services, alternatives, shortcuts and a feasible fuel plan.

A* uses Euclidean coordinates as a lower-bound construction rather than assuming
road length equals map distance. All scalar weights are non-negative. Integer
pickup costs and a single detour budget define the 0/1 knapsack model. Fixed-route
refuelling discretizes fuel in 0.1-unit steps with conservative rounding and
optimizes fixed stop time, rather than an unrestricted joint route/resource plan.

### 3.4 Race, resources, events and deterministic opponents

A station provides at most 40 fuel units per visit without exceeding capacity.
Unavailable services and unaffordable road entries are rejected. Nitro capacity
is three; a boost consumes one charge. Pickups are consumed after collection.
An opponent refuels at an active station below 25 fuel units. The three opponent
policies use main-route following, shortest-distance routing and a deterministic
shortcut preference, respectively; service detours must preserve checkpoint order.

Events use (trigger time, priority, insertion sequence). A closure takes precedence
over restriction and oil effects. Oil increases difficulty by one, capped at
five; restrictions multiply time by 1.5. A racer already on a road completes that
crossing. Temporary effects expire independently and are recomputed against the
baseline and surviving effects. Cancellation is lazy. Opponents wait when no
route exists and retry after changes; no affordable departure and no refuelling
option causes DNF. The time limit resolves prolonged waits.

### 3.5 Championship scoring and tie-breaking

Finishing positions 1 through 10 earn 25, 18, 15, 12, 10, 8, 6, 4, 2 and 1 points.
Unfinished racers earn zero. All standings algorithms use the ascending key
(-total points, -wins, sum of positions, best fastest lap, racer ID). Thus more
points and wins rank first; smaller position sums and best-lap times break later
ties, followed by stable racer ID. No additional bonus points are awarded.

## 4. Algorithm design, pseudocode and correctness

V is the vertex count, E the road count, m the item/route length, B the integer budget, C the discretized fuel capacity, n the record count and k the requested leader count. Complexity describes the implementation model, separately from measured milliseconds.

| Algorithm | Current role | Time / space |
| --- | --- | --- |
| BFS | Reachability and minimum-edge paths in exploration | O(V+E) / O(V) auxiliary |
| DFS | Traversal, with cycle, weak-component, dead-end and bounded path helpers | O(V+E) traversal / O(V); component view uses O(V+E) space; path enumeration can be exponential |
| Dijkstra | Non-negative route optimization and opponent routing | O((V+E) log V) with a binary heap |
| A* | Heuristic route search and comparison | Worst case comparable to Dijkstra; depends on heuristic |
| Dynamic programming | 0/1 pickup choices and discrete fixed-route refuelling | O(mB) for knapsack with reconstruction, O(m(C+1)) for fixed-stop-time refuelling |
| Greedy | Feasible benefit-to-cost pickup comparison | O(m log m) sorting |
| Backtracking | Ordered checkpoint placement during generation | Exponential worst case |
| Kruskal | Undirected generated-circuit backbone | O(E log E) with union-find |
| Binary heap | Route queue, deterministic event queue and top-k | O(log n) insert/extract; O(1) peek |
| Merge Sort | Primary championship ranking | O(n log n) time, O(n) space |
| Quick Sort | Alternate standings comparison | O(n log n) average, O(n²) worst case |
| Heap Sort | Alternate standings comparison | O(n log n) time, O(1) auxiliary space after copying |

**Data structures.** The graph stores vertex/road records with adjacency lists.
BFS uses a FIFO queue, visited set and parent map. DFS uses a traversal stack or
recursion with visited/component state. Routing uses distance and parent-road
maps plus an indexed binary heap and vertex-position map. Knapsack and
refuelling use discrete state tables with reconstruction choices. Greedy uses
an ordered item list. Kruskal uses a sorted road list and disjoint-set union;
backtracking keeps a partial placement and candidate set. Events combine the
heap with active-event/effect maps. Merge and Quick Sort use lists; Heap Sort
uses an array heap. Live top-k retains at most k entries in the manual heap.

### 4.1 BFS

```text
visited = {s}; parent[s] = NONE; enqueue(s)
while queue is not empty:
    u = dequeue()
    for each open outgoing road (u, v):
        if v not in visited:
            visited.add(v); parent[v] = u; enqueue(v)
return visitation order, parents, counters, trace
```

 Set the start parent to none and enqueue it. While the queue is not
empty, remove its front vertex; for each open outgoing road, record the parent
and enqueue an undiscovered neighbor. The FIFO queue visits vertices in
nondecreasing edge count, so the first parent chain found for a vertex has the
minimum number of roads. The explorer uses the resulting parents and trace.

### 4.2 DFS and bounded alternatives

```text
visit(u):
    mark u; append u to traversal
    for each open outgoing neighbor v:
        if v is unvisited: parent[v] = u; visit(v)
for each root needed by component analysis:
    if root is unvisited: visit(root)
# Mixed-road cycle analysis handles undirected components first.
```

 Mark the start, then repeatedly follow an
unvisited outgoing neighbor, recording its parent; backtrack when a vertex has
no remaining neighbors. A visited set prevents infinite traversal of cycles.
Separate graph helpers test cycles, weak components and dead ends. Alternative
paths backtrack over vertices already on the current path and stop at explicit
state, path-count and length limits. A limited search can be incomplete; a
single traversal is linear, while simple-path enumeration may be exponential.
For mixed directed and undirected roads, cycle detection first finds
undirected components and cycles. A directed road inside one component closes
a cycle; directed roads between components are then checked with directed DFS.
This avoids mistaking the reversal of one two-way road for a cycle and takes
O(V+E) time and space.
Weak components similarly build an undirected view of open roads and visit it
in O(V+E) time and space; the directed state of each original road is unchanged.

### 4.3 Dijkstra

```text
dist[s] = 0; all other distances = infinity
insert (0, s) into indexed min-heap
while heap is not empty:
    u = extract_min()
    if u == target: reconstruct path and return
    for each legal outgoing road (u, v):
        if dist[u] + cost(u,v) < dist[v]:
            update distance and parent road of v
            insert or decrease_key(v, dist[v])
return unreachable
```

 Set the start distance to zero, insert it into an indexed
min-heap, and repeatedly extract the least tentative distance. For each legal
outgoing road, relax the destination and insert or decrease its heap entry.
The heap keeps at most one entry per vertex, with a vertex-to-position map.
With non-negative costs, extracting the destination gives optimal cost. Parent
roads reconstruct the path; blocked roads are excluded. Insertions, decreases
and extractions take O(log V), giving O((V+E) log V) time and O(V) heap space.

### 4.4 A-star

```text
alpha = minimum cost(e)/geometric_length(e)
# Ignore zero geometric lengths; use zero when necessary.
h(v) = alpha * EuclideanDistance(v, target)
run the shared relaxation search with heap key g(v) + h(v)
return path, g(target), expanded/relaxed/heap counters
```

 Use the same relaxation and parents, but order the heap by the sum
of tentative cost and a geometric lower bound to the target. The minimum current
edge-cost-to-geometric-length ratio makes this bound consistent; zero is a safe
fallback. Therefore a current target extraction is optimal under the same
non-negative cost assumption. Ordered laps run separate searches for each next
checkpoint while excluding later checkpoints from each leg.

### 4.5 Knapsack DP

```text
DP[0,b] = 0 for b = 0..budget
for i = 1..item_count:
    for b = 0..budget:
        DP[i,b] = DP[i-1,b]
        if cost[i] <= b:
            DP[i,b] = max(DP[i,b],
                benefit[i] + DP[i-1,b-cost[i]])
walk table backwards to recover selected item IDs
```

 For each pickup and budget, store the better value between
skipping it and taking it if its integer cost fits. Begin with an all-zero row,
then walk the completed table backwards to recover chosen items. Each row uses
only the previous row, so every item is used at most once and induction on the
number of items gives the optimal benefit for each budget. Runtime and storage
are O(mB), where B is the numeric budget, not its bit length.

### 4.6 Refuelling DP

```text
T[finish,f] = 0 for all legal fuel levels f
for route position i in reverse order:
    for fuel level f = 0..capacity:
        compare feasible no-stop and available-station transitions
        deduct conservatively rounded next-road fuel
        store minimum stop time and reconstruction choice
reconstruct a feasible minimum-stop-time fuel plan
return infeasible if the initial state is infinite
```

 Work backwards from zero remaining time at the finish.
At each vertex and fuel level, compare skipping the station with paying a
fixed stop time and taking up to 40 units. Deduct the next road's requirement.
More arrival fuel can only preserve or improve the next state's time, so the
largest permitted purchase gives the best future time for any positive stop.
A linear scan of each row records the first fuel level achieving each equal
time. The planner reconstructs the smallest purchases attaining the optimum
in O(m(C+1)) total time and storage. Impossible states cost infinity. Fuel is
rounded conservatively to tenths. The game's automatic fill at the same stops
can leave extra fuel. The resource-planning notes give the full recurrence.

### 4.7 Greedy pickup choice

```text
take each positive-benefit zero-cost item once
sort remaining items by decreasing benefit/cost, then ID
for item in that order:
    if item fits the remaining budget:
        select item; update budget and benefit
return feasible selection and trace
```

 Process positive-benefit zero-cost items first, then
consider the remaining items in descending exact benefit-to-cost ratio with ID
ties. Select an item only if it fits the remaining scalar detour budget. The
selected benefit is updated incrementally, including in Lab traces, so the
sorting step dominates the O(m log m) time. The result is feasible but not
always optimal: the supplied budget-10 case produces
benefit 30 versus the DP optimum of 48. The study includes two further checked
counterexamples.

### 4.8 Backtracking and Kruskal

```text
sort undirected candidate roads by weight, then stable ties
for road (u,v):
    if find(u) != find(v): add road; union(u,v)
reject if a connected backbone was not formed
add lap and alternative roads
place(partial):
    if placement is complete: return partial
    for each remaining candidate in deterministic order:
        if candidate satisfies current constraints:
            choose candidate
            answer = place(partial)
            if answer succeeds: return answer
            undo candidate
    return failure
place checkpoints/services/obstacles using place(empty)
add one-way roads; validate complete circuit
retry deterministically up to the configured attempt limit
```

 The generator attempts candidate placements,
rejects choices that violate spacing or route constraints, and backtracks when a
partial placement cannot be completed. It accepts a candidate only after circuit
validation, with bounded retries. Kruskal sorts undirected candidate roads by
weight and adds an edge only when union-find places its endpoints in different
components. The cut property yields a minimum spanning forest; connected
candidates yield a spanning tree. Extra roads supply laps and alternatives.
The generated circuit then adds two one-way roads and validates the resulting
directed track. In the Lab, Kruskal uses the selected track's undirected
subgraph and reports the excluded one-way roads.

### 4.9 Binary heap and event queue

```text
schedule(event):
    push (time, priority, next_sequence, event_id)
cancel(event_id): mark event inactive
while heap minimum is due:
    key = pop_min()
    if event is active: yield event
apply temporary effects and schedule independent expirations
recompute road state from baseline and all remaining effects
```

 Insert by appending and sifting upward; remove
the root by moving the last element to the root and sifting downward. These
operations preserve the parent-before-children invariant. Event keys include
trigger time, priority and insertion sequence, so extracting the minimum gives
the specified deterministic order. Cancellation is lazy and temporary effects
have independent expiration events. A closure takes precedence over oil and
speed restrictions; an explicit temporary shortcut opening changes the
baseline only for its duration, while an overlapping closure still wins.

### 4.10 Merge Sort

```text
merge_sort(A):
    if length(A) <= 1: return A
    split A into L and R
    return merge(merge_sort(L), merge_sort(R))
merge: repeatedly take the smaller shared ranking key
# Take the left entry first when keys are equal.
```

 Recursively split the entries, sort each half, and merge by the
shared championship key. Both halves are sorted by induction, and repeatedly
choosing their smallest front entry produces the sorted result. Its O(n log n)
work uses O(n) additional storage for merging.

### 4.11 Quick Sort

```text
quick_sort(A):
    if length(A) <= 1: return A
    pivot = ranking key of the middle entry
    partition A into lower, equal and greater keys
    return quick_sort(lower) + equal + quick_sort(greater)
```

 Choose the middle entry's key as pivot, partition entries into
lower, equal and greater groups, then recursively sort and concatenate the
outer groups. Each partition preserves all entries and places every lower key
before every greater key, so induction gives a sorted result. Work averages
O(n log n) but can be O(n^2); the lists used by this implementation take space.

### 4.12 Heap Sort and top-k

```text
heap_sort(A):
    build a max-heap under the common ranking key
    repeatedly swap root with last unsorted entry; sift down
leaders(A,k):
    retain at most k records, worst retained record at root
    replace root whenever a better record arrives
    extract and reverse to return leaders best first
```

 Heap Sort builds a max-heap, repeatedly swaps its
root with the final unsorted position, then restores the heap invariant. Each
extraction fixes the greatest remaining key at the end. Top-k scans the field
once, keeping up to k leaders in the shared manual heap with the worst retained
key at its root. A better arrival replaces that root, so after each input the
heap contains the best k records seen so far. Reversing the extraction order
returns them best first. Equal keys retain their original input order. For
positive k the worst-case time is O(n log(k+1)) and storage is O(k).

## 5. Algorithm integration into gameplay

The algorithms are implemented manually in src/smart_racing/algorithms, with
backtracking placement in tracks/generator.py. No external algorithm library
provides a mandatory implementation. The UI consumes plain result records,
parents, selected IDs, traces and counters from these same functions.

| Algorithm | Source module / function | Gameplay invocation |
| --- | --- | --- |
| BFS | graph/traversal.py: bfs | Explorer reachability and minimum-edge routes. |
| DFS | graph/traversal.py: dfs, has_cycle, weak_components, simple_paths | Explorer topology and bounded alternative routes. |
| Dijkstra | routing/shortest.py: shortest_path | Route Planner, ordered legs and opponent shortest routing. |
| A* | routing/shortest.py: shortest_path (astar) | Planner comparison and ordered route searches. |
| DP | optimization/resources.py: knapsack, refuel_plan | Pickup recommendations and fixed-route fuel planning. |
| Greedy | optimization/resources.py: greedy | Pickup comparison with DP and Lab recording. |
| Backtracking | tracks/generator.py: _assign_checkpoints, _place_obstacles | Circuit workshop placement and generation traces. |
| Kruskal | generation/mst.py: kruskal | Generated backbone and selected-track Lab demonstration. |
| Binary heap | structures/heap.py: MinHeap | Routing priorities, event scheduling and live leaders. |
| Merge Sort | sorting/rankings.py: merge_sort | Primary championship standings. |
| Quick Sort | sorting/rankings.py: quick_sort | Alternate dashboard ranking comparison. |
| Heap Sort | sorting/rankings.py: heap_sort | Third dashboard ranking comparison. |

The Lab and benchmark driver call these implementations directly. A trace is a
record of real algorithm decisions, not a separate demonstration algorithm.
Traversal examined-edge counts refer to adjacency entries, so an undirected
road can be counted twice. Routing relaxed counts include attempted relaxations;
heap counters include insertions, decreases and extractions. The alternative-path
view is bounded to 10,000 states, 16 vertices per path and up to five alternatives;
it reports truncation and may omit feasible routes. This endpoint comparison
mode does not itself enforce an ordered lap.

## 6. Testing strategy, cases and results

### 6.1 Strategy and independent references

Unit tests isolate algorithms and domain contracts; integration tests exercise
loading, events, race rules, resource boundaries, screens and championship
progression. Seeds and stable tie-breaking make failures reproducible. Routing
is checked against independent Bellman-Ford comparisons on small mixed graphs;
knapsack is checked with exhaustive subsets; ranking and top-k are checked
against Python's reference ordering under the same total comparator. Such
references are verification tools, not replacements in gameplay.

### 6.2 Assignment minimum coverage

| Area | Cases exercised | Main evidence |
| --- | --- | --- |
| Graph | Single vertex, disconnected, cyclic, branching, dead-end, directed and undirected cases | tests/unit/test_algorithms.py; circuit topology integration tests |
| Routing | Source equals target, unreachable target, blocked edge, equal costs, zero weights, changes during racing | Algorithm unit tests; route-planner QA; closure/replanning race tests |
| Resources | Insufficient fuel, full tank, unavailable station, capacity limits, zero-cost items, infeasible plans | Resource-planning unit tests; test_quick_race_qa.py; race integration tests |
| Events | Simultaneous events, stable ties, cancellation, expiry, unknown targets, overlapping effects | Event-queue unit tests; race/event integration cases |
| Sorting | Empty, singleton, random, sorted, reverse, duplicate-heavy; shared comparator | Sort unit tests; full-sort/top-k agreement tests; Study 5 |
| Integration | Complete race, multiple laps, ordered checkpoints, DNF, closure, championship standings | test_race.py and test_ui_workflow.py |

### 6.3 Recorded results and practical checks

On 23 November 2026, main at 6964f7a passed 252 pytest tests in 51.51 seconds
using the project's Python 3.12.16 environment. Ruff reported all checks passed;
pip check reported no broken requirements. The source and existing packaged
executable passed dummy-SDL smoke tests with exit code zero. These checks were
executed during this review; they do not certify an archive built later.

The packaged executable also opened visibly. Navigation to the Route Planner,
Algorithm Lab and Quick Race worked; BFS-to-DFS selection, the tactical-map toggle
and a player drive action were observed. A full manual race and season were not
completed in this check. The earlier local Application Control launch block was
not reproduced. Headless UI tests and scripted interaction do not establish that
every group member can demonstrate or explain the project.

### 6.4 Reproduction commands

```text
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check src tests experiments scripts
.venv/Scripts/python.exe -m pip check
# Set SDL_VIDEODRIVER=dummy and SDL_AUDIODRIVER=dummy for smoke checks.
.venv/Scripts/python.exe -m smart_racing --smoke-test
```

## 7. Five experimental studies

The following studies use the stored measured dataset, not new timings produced
by formatting this report. Results, generation seeds, selected items and raw
samples are published in experiments/results/studies.json. The benchmark source
is experiments/benchmarks/run_studies.py. Run it from the project root with the
project interpreter to regenerate results; machine load can change timings.
The numeric seed 20261205 is an arbitrary reproducibility identifier, not a date.

{{EXPERIMENTS}}

## 8. Advanced challenges, limitations and future work

### 8.1 Automatic track generation

A seeded generator builds a Kruskal MST backbone, adds a lap and extra roads,
places checkpoints/services/obstacles through constraints and backtracking, adds
two one-way roads, and validates the final directed graph. Degree limits and
spacing protect the current generated family. At most five deterministic attempts
are made by default; failure is reported instead of returning an invalid circuit.

The workshop's invalid-candidate demonstration removes shortcut flags from a
copy and calls the real validator. It is rejected because the circuit no longer
has the required two shortcuts. The displayed rejection reason comes from that
validator. This is a deliberately invalid demonstration, distinct from natural
retry failures. Prior checks validated seeds 0 through 99, and automated races
cover five generated tracks; finite samples do not prove all seeds succeed.

### 8.2 Multi-objective route presets

Section 3.2 gives the balanced, speed, economy and safety weights. On the Copper
Canyon ordered lap, Balanced takes checkpoint 2 directly to 3, whereas Safety
travels 2 -> service vertex 11 -> 3, while preserving the ten-checkpoint order.
The planner displays component costs and recomputes routes after road changes.

A weighted scalar expresses a chosen preference, not all Pareto trade-offs.
Changing normalization or weights can change the chosen route. Scores computed
under different profiles are not directly comparable, and a scalar optimum is
not a joint proof of minimum time, fuel and risk independently.

### 8.3 Efficient live championship analytics

The dashboard displays a selectable top-k using the manual bounded heap and the
same total comparator as full standings. It stores only k retained records and
rebuilds retrieval from the current entries. Study 5 compares k=5 with k=n-1.
Small k reduces retained storage and per-record heap work; when k approaches n,
memory and ordered extraction approach those of ranking the full field. The
current feature is repeated retrieval over updated standings, rather than a
persistent incrementally indexed leaderboard.

### 8.4 Limitations

Generated tracks follow a ring-based family. Alternative-path enumeration is
bounded and can be incomplete. Resource plans use a fixed route and discretized
fuel; later events and nitro use can invalidate a full-tank recommendation.
Opponents use fixed deterministic policies. Study inputs are small, synthetic
and measured on one machine; trace construction and interpreter overhead are
included. Timings do not establish asymptotic complexity or all gameplay workloads.
A complete human season, final report review, final ZIP extraction/execution,
required malware check, demonstration and viva remain submission tasks.

### 8.5 Future improvements

Expand generated topology families while retaining directed playability checks.
Evaluate more independently seeded graphs and authored-circuit route workloads,
larger sizes and additional machines. Add distributions of timings and better
instrumented sorting comparisons. Explore multi-criteria/Pareto route displays
and joint resource-aware routing while retaining explainable deterministic rules.
Complete user playtesting for controls, error feedback and reduced-motion use.
These are future directions, not claims of implemented behavior.

## 9. Conclusion

Smart Racing Championship connects a changing graph to ordered races, finite
resources and deterministic event processing. The twelve manual algorithm
families are shared across gameplay, the Algorithm Lab and five measured studies.
All three advanced challenges are implemented. Automated evidence covers the
assignment's minimum test classes, with 252 tests passing in the recorded review.

The experiments distinguish correctness, work counters and finite runtime
measurements. BFS and DFS scan the adjacency structure; A* can reduce search
work with a useful lower bound; DP improves benefit on checked greedy
counterexamples; heaps enforce deterministic event order and retain small leader
sets; all full rankings agree under one championship comparator. Submission
readiness additionally requires the remaining archive and human checks.

## 10. References and acknowledgements

[1] Course assignment: Smart Racing Championship, Design and Analysis of
Algorithms. Local transcription: docs/assignment-specification.md. Defines
requirements, test classes, studies, challenges and submission format.

[2] Python Software Foundation. Python documentation: https://docs.python.org/3/.
Interpreter and standard-library reference.

[3] Pygame contributors. Pygame documentation: https://www.pygame.org/docs/.
Game input, display, audio and rendering library.

[4] pytest contributors. pytest documentation: https://docs.pytest.org/.
Automated test framework. Ruff: https://docs.astral.sh/ruff/ (static checks).

[5] ReportLab. ReportLab documentation: https://docs.reportlab.com/.
Technical-report generation. PyMuPDF: https://pymupdf.readthedocs.io/ (PDF review).

[6] PyInstaller development team. https://pyinstaller.org/.
Windows executable packaging. Matplotlib: https://matplotlib.org/ (experiment tooling).

[7] Sedgewick and Wayne. Algorithms, Section 2.4, TopM example:
https://algs4.cs.princeton.edu/code/javadoc/edu/princeton/cs/algs4/TopM.html.
Reference for the bounded-priority-queue approach; the project implements its own heap.

[8] FAST-NUCES official website, university marks:
https://nu.edu.pk/Content/images/FAST.png and
https://nu.edu.pk/Content/images/NU-logo.jpg. Retrieved 23 November 2026.
The FAST mark is reproduced in black on this academic report; institutional
marks remain their owners' property. Source notes: docs/report/assets/README.md.

[9] Barlow Project Authors. Barlow and Barlow Condensed fonts, SIL Open Font
License 1.1, retained in assets/fonts/OFL.txt. Bundled game fonts.

[10] Asset provenance: assets/images/README.md and assets/audio/README.md.
Game scene imagery was generated using OpenAI image generation; synthesized
sound has a reproducible project script. REDLINE's monogram and circuit data are
project-authored. This report omits colored game photography to meet the requested
black-only layout. External libraries support presentation, testing, packaging
and reporting; mandatory algorithms are manually implemented.
