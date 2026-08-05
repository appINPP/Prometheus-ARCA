#Split Production

Split Production was created to face the bottleneck of the high computational expense of propagating high energy events. The idea is to utilise the separate functions of the Prometheus code (found in `prometheus/prometheus.py`) of injection, propagation and output construction to first inject a large number of neutrinos on the entire energy range and then filter which events to move to the propagation stage. This way, lower energy events and high energy events would be simulated separately with respect to their computational needs, lifting the need to manually alter the amount of high/lower energy events simulated to respect their ratio. 

To do this in a way that supports multiprocessing, a job distributor was set to flag injected events as PENDING, CLAIMED or DONE to propagate fully the injection file for the specific energy range, lower or upper.

To elaborate on the differences between the two versions:
+ `version 1`:
++ workers claim events dynamically
++ PENDING refers to unpropagated events, CLAIMED to events picked up by workers and DONE events that have been done being propagated.
+ `version 2`
++ events for propagation are distributed to workers
++ PENDING refers to unpropagated events, CLAIMED to events handed to workers and DONE events that have had their output written. The change in the DONE flagging was done as a better safety measure to confirm the existence of a simulation output and with the perspective of setting CLAIMED events as PENDING at the start of the propagation script for crash recovery. This idea, however, assumes that the simulation code doesn't normally raise errors (otherwise it will start a vicious cycle of crashes, which doesn't sound as fun).

The need for `version 2` came to be after `version 1` was verified it caused RAM accumulation. 

Version 1 has further documentation inside the folder (useful for understanding both versions) as it was meant to be the chosen workflow for production. Version 2 has not been validated and the scripts are taken as they were. In the validation folders there are additional scripts that could be used to test Version 2 (unpolished). 

##Suggestions for future work
+ Neither version follows the correct os.environment (by order) as it was set in batches_production.py. That should be implemented correctly.
+ Neither version clears up C/C++ and JAX memory as seen, again, in batches_production.py. This might be trivial for Version 2 since workers spawn and die repeatedly, but will surely make a difference for Version 1.
+ Validation of functionality of Version 2. Given that works, the automation script of Version 1 can be used as it is, and have split production as the default peoduction workflow.
