# SIH26124 PROJECT CONTEXT

## Problem

Public transport vehicles can act as mobile urban sensing units.

## MVP Objective

Demonstrate that a bus camera can detect a road anomaly,
associate it with location/time/bus information,
send it to a central platform,
visualize it geographically,
prioritize it,
and track its resolution.

## Current Starting Point

Existing repository:
collabdoor/road-anomaly-detection

Existing capabilities:
- YOLOv8m
- trained best.pt
- road anomaly detection
- image inference
- video inference
- live camera inference
- Streamlit interface

## MVP

IN:
- pothole
- crack
- speed bump
- bus simulation
- GPS simulation
- event generation
- event deduplication
- severity
- FastAPI
- SQLite
- React
- GIS map
- incident management
- multi-bus confirmation
- resolution workflow

OUT:
- ANPR
- hit-and-run
- rash driving
- advanced pedestrian risk
- real hardware
- MQTT
- cloud
- PostGIS
- predictive maintenance
- LLM
- OD analysis

## Architecture

Video
→ YOLO
→ Event Builder
→ FastAPI
→ SQLite
→ React
→ Map
→ Escalation
→ Resolution

## Golden Rule

The MVP must demonstrate the complete vertical slice
rather than partially implementing many features.