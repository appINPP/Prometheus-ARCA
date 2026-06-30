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
    echo "ERROR: Missing required arguments! Use: --total_events A --workers B (--flavor MuMinus/NuEbar --energy lower/upper)"
    exit 1
fi

INJ_BATCH=1000
LOW_BATCH=500
HIGH_BATCH=120

echo "Injecting..."

INJ_START=$(date +%s)
CHUNK=$((INJ_BATCH*WORKERS))

while [ "$EVENTS" -ge "$CHUNK" ]; do
  python injection.py --workers "$WORKERS" --events_per_worker "$INJ_BATCH" --flavor "$FLAVOR" 
  EVENTS=$((EVENTS-CHUNK))
done

if [ "$EVENTS" -ge "$INJ_BATCH" ]; then
  python injection.py --workers "$((EVENTS/INJ_BATCH))" --events_per_worker "$INJ_BATCH" --flavor "$FLAVOR"
fi

if [ "$((EVENTS%INJ_BATCH))" -ne 0 ]; then
  python injection.py --workers 1 --events_per_worker "$((EVENTS%INJ_BATCH))" --flavor "$FLAVOR"
fi

INJ_FILES=$(find /home/username/prometheus/output/"$FLAVOR"/injection_files/ -name "*_LI_output.h5" -newermt "@$INJ_START")

if [ -z "$INJ_FILES" ]; then
    echo "ERROR: No injection file was created. Stopping pipeline."
    exit 1
fi

IDS=()
for file in $INJ_FILES; do
    filename=$(basename "$file")
    id=$(echo "$filename" | cut -d'_' -f1)
    if [ -n "$id" ]; then
        IDS+=("$id")
    fi
done

echo "Injection Complete! ${#IDS[@]} Files. IDs: ${IDS[*]}" 

for ID in "${IDS[@]}"; do
  echo "Propagation stage for injection file $ID..."
  
  python init_propagation.py --flavor "$FLAVOR" --id "$ID"
  echo "Job distributor ready for low energy production!"
  
  python propagation.py --workers "$WORKERS" --events_per_worker "$LOW_BATCH" --flavor "$FLAVOR" --id "$ID"
  echo "Low energy production done for file $ID!"
done 

if [ "$ENERGY" = "upper" ]; then
        for ID in "${IDS[@]}"; do
          echo "Producing high energy events for injection file $ID..."
          python propagation.py --workers "$WORKERS" --events_per_worker "$HIGH_BATCH" --flavor "$FLAVOR" --id "$ID" --energy "$ENERGY"
          echo "High energy production done!"
        done
fi
