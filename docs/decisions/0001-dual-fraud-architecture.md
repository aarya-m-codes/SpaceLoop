# ADR 0001: Dual Fraud and Risk Architecture

## Status
Accepted

## Context
SpaceLoop requires both relational behavioral graph inspection (Trust & Safety Engine A) and real-time numerical feature anomaly detection (ML Fraud Engine B).

## Decision
Implement both independent engines without merging them into a simplistic single engine.
