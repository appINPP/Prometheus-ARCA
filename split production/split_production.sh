#!/bin/bash

WORKERS=""
EVENTS=""
FLAVOR="MuMinus"
ENERGY="lower"

while [[ $# -gt 0 ]]; do
  case $1 in
    --workers)
      WORKERS="$2"
      shift 2 
      ;;
    --total_events)
      EVENTS="$2"
      shift 2 
      ;;
    --flavor)
      FLAVOR="$2"
      shift 2 
      ;;
    --energy)
      ENERGY="$2"
      shift 2 
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

# Quick safety check
if [ -z "$WORKERS" ] || [ -z "$EVENTS" ]; then
    echo "ERROR: Missing required arguments! Use: --events A (--workers B --flavor MuMinus/NuEbar --energy lower/upper)"
    exit 1
fi

echo "Injecting..."

python injection.py --workers 1 --events_per_worker "$EVENTS" --flavor "$FLAVOR" 

INJ_FILE=$(find /home/username/prometheus/output/"$FLAVOR"/injection_files/ -name "*_LI_output.h5" -mmin -5 | head -n 1)

if [ -z "$INJ_FILE" ]; then
    echo "ERROR: No injection file was created. Stopping pipeline."
    exit 1
fi

ID=$(echo "$INJ_FILE" | tr -dc '0-9')

echo "Injection Complete! File ID: $ID" 

python init_propagation.py --flavor "$FLAVOR" --id "$ID"

echo "Job distributor ready for low energy production!"

EVENTS_PER=$(($EVENTS / $WORKERS))

python propagation.py --workers "$WORKERS" --events_per_worker "$EVENTS_PER" --flavor "$FLAVOR" --id "$ID"

echo "Low energy production done!"

if [ "$ENERGY" = "upper" ]; then
        echo "Producing high energy events..."
        python propagation.py --workers "$WORKERS" --events_per_worker "$EVENTS_PER" --flavor "$FLAVOR" --id "$ID" --energy "$ENERGY"
        echo "High energy production done!"
fi



