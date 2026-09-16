# MVP-001 – First Traffic Simulation

## Purpose

Establish the smallest possible working foundation for the project by proving that traffic can be simulated on a real-world road network.

The result should be something we can actually run and observe, rather than only an architectural or technical proof of concept.

## Goals

* A small real-world area can be represented as a routable road network.
* Multiple vehicles can travel through that network simultaneously.
* The simulation can be started repeatedly and observed visually.
* The project has a working technical foundation that later MVPs can extend.

## Context

The project currently contains the vision, roadmap and initial architecture, but no executable mobility simulation.

The architecture identifies geographic data, a mobility simulation engine and orchestration as the likely initial foundation.

This MVP is the first validation that those concepts can form a working system.

## Scope

The MVP includes:

* One small, selected real-world geographic area.
* The area's road network.
* Motor vehicles travelling between different locations in the network.
* Routing of vehicles through the network.
* A visual representation where the road network and moving vehicles can be observed.
* A repeatable way to start the simulation from the project workspace.

The traffic may be synthetic and does not need to represent actual traffic volumes or travel behaviour.

## Out of Scope

The following are deliberately excluded from this MVP:

* Realistic population or travel demand.
* Individual people or households.
* Bicycles.
* Pedestrians.
* Public transport.
* Buildings, water, parks and other map features that are not required for traffic simulation.
* Real traffic measurements.
* Traffic calibration.
* Road closures or infrastructure changes.
* Scenario comparison.
* Custom web interface.
* Custom map visualization.
* Traffic analysis or advanced statistics.

These capabilities belong in later MVPs. The purpose of MVP-001 is only to establish a working simulation foundation.

## Acceptance Criteria

* A real-world road network for the selected area is loaded into the simulation.
* At least 10 vehicles can be simulated simultaneously on that network.
* Vehicles follow valid routes through the road network.
* The simulation can be observed visually while it is running.
* The simulation reaches completion without manual intervention or simulation errors.
* A developer can start the simulation again using documented project instructions.

## Outcome at close (YYYY-MM-DD)

To be completed when the MVP is closed.

Report the actual outcome against each acceptance criterion, including anything that was only partially delivered or changed during implementation.
