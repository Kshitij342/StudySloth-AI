"""Pre-configured sample study notes for instant testing and demonstration."""

SAMPLE_NOTES = {
    "Biology: Cellular Respiration & Energy": """# Topic: Cellular Respiration and Energy Transformation

Cellular respiration is the biochemical process by which living cells break down glucose (C6H12O6) in the presence of oxygen to produce adenosine triphosphate (ATP), carbon dioxide, and water.

Overall Chemical Equation:
C6H12O6 + 6 O2 -> 6 CO2 + 6 H2O + ~30-32 ATP

Key Stages of Cellular Respiration:
1. Glycolysis:
   - Takes place in the cytoplasm.
   - Anaerobic process (does not require oxygen).
   - 1 glucose molecule is split into 2 pyruvate molecules.
   - Net yield: 2 ATP (via substrate-level phosphorylation) and 2 NADH.

2. Pyruvate Oxidation (Link Reaction):
   - Occurs as pyruvate enters the mitochondrial matrix.
   - Pyruvate is converted into Acetyl-CoA, producing 1 NADH and releasing 1 CO2 per pyruvate (2 NADH and 2 CO2 per glucose).

3. Krebs Cycle (Citric Acid Cycle):
   - Located in the mitochondrial matrix.
   - Acetyl-CoA combines with oxaloacetate to form citrate.
   - Per turn (2 turns per glucose): Produces 3 NADH, 1 FADH2, 1 ATP (or GTP), and releases 2 CO2.
   - Total per glucose: 6 NADH, 2 FADH2, 2 ATP, 4 CO2.

4. Oxidative Phosphorylation (Electron Transport Chain & Chemiosmosis):
   - Located along the inner mitochondrial membrane (cristae).
   - Electrons from NADH and FADH2 are transferred along protein complexes I through IV.
   - Protons (H+) are pumped across the inner membrane into the intermembrane space, establishing an electrochemical proton gradient.
   - Protons flow back into the matrix through ATP Synthase, powering ATP synthesis (Chemiosmosis).
   - Oxygen serves as the final electron acceptor, combining with electrons and protons to form water.
   - Generates approximately 26-28 ATP.

Differences with Fermentation:
When oxygen is absent, cells undergo anaerobic fermentation (Lactic acid fermentation in muscles, or alcoholic fermentation in yeast) to regenerate NAD+ so glycolysis can continue, producing only 2 net ATP per glucose.""",

    "Computer Science: Big-O & Data Structures": """# Topic: Algorithm Analysis and Core Data Structures

Algorithm efficiency is measured by time complexity and space complexity using Asymptotic (Big-O) notation, which characterizes the growth rate of resource consumption as the input size (n) approaches infinity.

Common Big-O Complexities (from best to worst):
- O(1) - Constant Time: Accessing an array element by index, hash table lookup (average case).
- O(log n) - Logarithmic Time: Binary search on a sorted array, balanced search tree operations.
- O(n) - Linear Time: Linear search through an unsorted list, traversing a linked list.
- O(n log n) - Linearithmic Time: Efficient sorting algorithms (Merge Sort, Heap Sort, Quick Sort average).
- O(n^2) - Quadratic Time: Nested loops, naive sorting algorithms (Bubble Sort, Selection Sort, Insertion Sort).
- O(2^n) - Exponential Time: Recursive calculation of Fibonacci numbers without memoization, generating all subsets.
- O(n!) - Factorial Time: Traveling Salesperson Problem brute-force solution.

Core Linear Data Structures:
1. Arrays: Contiguous block of memory. Fast random access O(1), but expensive insertions/deletions O(n) when shifting elements is required.
2. Linked Lists: Nodes containing data and pointers to next nodes. Dynamic size, O(1) insertions at head, but O(n) sequential access.
3. Stacks: LIFO (Last In, First Out) principle. Operations: Push and Pop are O(1). Used in call stacks, undo mechanisms, and parsing expressions.
4. Queues: FIFO (First In, First Out) principle. Operations: Enqueue and Dequeue are O(1). Used in task scheduling and breadth-first search.

Hash Tables (Dictionaries):
- Stores key-value pairs using a hash function.
- Average case: O(1) insertion, deletion, and lookup.
- Worst case: O(n) if excessive hash collisions occur. Handled via chaining (linked lists) or open addressing.""",

    "World History: The Industrial Revolution": """# Topic: The First Industrial Revolution (c. 1760 – 1840)

The First Industrial Revolution marked a profound transition from agrarian, handicraft economies dominated by human and animal labor to modern industrial economies driven by mechanized manufacturing, machine tools, and steam power.

Origins in Great Britain:
Great Britain became the cradle of industrialization due to several intersecting factors:
- Abundant natural resources, especially coal and iron ore deposits.
- Agricultural Revolution improvements that increased food supply and freed agricultural workers for factory labor.
- Capital accumulation from global maritime commerce and colonial markets.
- Stable legal and banking systems, including strong patent protections.

Key Technological Innovations:
1. Steam Engine: James Watt's improvements (1769–1776) on Thomas Newcomen's atmospheric engine drastically improved fuel efficiency and introduced rotary motion, untethering factories from riverbanks.
2. Textile Mechanization: John Kay's Flying Shuttle (1733), James Hargreaves' Spinning Jenny (1764), and Richard Arkwright's Water Frame (1769) transformed cotton spinning into mass production.
3. Iron Smelting: Henry Cort's puddling process (1784) enabled large-scale refining of pig iron into wrought iron, providing materials for bridges, machinery, and railways.

Socio-Economic Impacts:
- Urbanization: Rapid migration from rural villages into densely packed industrial cities like Manchester and Birmingham, creating severe sanitation and housing shortages.
- Factory System: Strict labor discipline, 12-to-16-hour workdays, dangerous working conditions, and widespread child labor.
- Rise of New Social Classes: The industrial bourgeoisie (factory owners and capitalists) and the industrial working proletariat.
- Emergence of New Economic Theories: Adam Smith's free-market capitalism (The Wealth of Nations, 1776) and early socialist critiques culminating in Karl Marx and Friedrich Engels' labor analyses."""
}
