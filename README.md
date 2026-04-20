# Revit BIM Analytics Pipeline

Data pipeline extracting building 
information from Revit models using Dynamo 
and the Revit API, processed in Python, 
and visualized in a Streamlit dashboard.

## Pipeline
Revit Model → Dynamo + Revit API → 
Python Processing → Streamlit Dashboard

## What It Extracts
- Room data — names, areas, levels, categories
- Wall data — types, lengths, areas by level
- Floor data — areas by level
- Door and window counts by level
- Wall material layers and thicknesses
- Early-stage embodied carbon estimates (ICE V3.0)

## Tools
- Dynamo (Revit API / FilteredElementCollector)
- Python (Pandas, Streamlit, Plotly)
- ICE V3.0 carbon factors
