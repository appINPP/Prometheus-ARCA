# Prometheus-ARCA

batches_production.py produces neutrino simulations in batches. You may choose the amount of workers (n_workers) and the total number of simulated events (n_events_total). Note that if the total number of events isn't a multiple of the number of workers, you may end up with fewer simulations than expected. 
