# Competitive_Pokemon_Battle_Prep
This project is a hybrid analytics tool combining a Python preprocessing script with an Excel‑based dashboard for competitive Pokémon team preparation. The Python script reads and normalizes Pokémon Showdown’s JSON data (moves, types, abilities, formats, etc.), producing clean tables that feed directly into Excel. The dashboard then transforms this data into a structured, automated interface for analyzing team composition, coverage, and matchup readiness.

# Core Capabilities 
- Python Data Loader
  - Parses Showdown JSON/JS datasets into clean, normalized tables for Excel consumption using pandas and custom parsing logic.
- Dynamic Type Coverage Analysis
  - Automatically computes weaknesses, resistances, and immunities using spill formulas and structured references.
- Role & Category Mapping
  - Flags missing roles such as hazards, removal, speed control, and defensive utility.
- Modular Helper Tables
  - Includes reusable tables for types, moves, abilities, and roles to keep formulas clean and maintainable.
- Interactive Dashboard
  - Provides a single‑page view of team strengths, weaknesses, and matchup considerations.
- Future Integration
-   Designed to pair with a separate battle‑analytics engine for opponent scouting, event‑level analysis, and predictive modeling.

# Technology Used
- Excel
  - Structured References
  - Dynamic Arrays
  - Conditional Formatting
  - Index, Vlookup, Let/Lambda
- Python
  - Pandas
  - JSON parsing
  - Data Cleaning
  - Formatting
