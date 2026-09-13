import json
import time
import sys
import uuid
from pathlib import Path
import requests
import argparse

# Ensure evidence generation works
from demo.generate_evidence import generate_evidence

def load_scenario():
    p = Path(__file__).parent / "scenario.json"
    with open(p) as f:
        return json.load(f)

def check_backend(api_base):
    try:
        r = requests.get(f"{api_base}/incidents", timeout=2)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"ERROR: Backend unreachable at {api_base}. Ensure uvicorn is running.")
        print(f"Details: {e}")
        sys.exit(1)

def build_event(scenario, bus_cfg, evt_id, evidence_path):
    return {
        "edge_event_id": evt_id,
        "event_id": evt_id,
        "anomaly_type": scenario["anomaly_type"],
        "event_type": scenario["anomaly_type"],
        "confidence": scenario["base_confidence"],
        "severity": scenario["base_severity"],
        "priority_score": scenario["base_priority_score"],
        "latitude": bus_cfg["latitude"],
        "longitude": bus_cfg["longitude"],
        "bus_id": bus_cfg["id"],
        "route_id": scenario["route_id"],
        "evidence_path": str(evidence_path),
        "status": "Pending",
        "speed_kmh": bus_cfg["speed"]
    }

def post_event(api_base, event, evidence_path):
    print(f"\nPosting edge event for {event['bus_id']}...")
    try:
        with open(evidence_path, "rb") as fh:
            resp = requests.post(
                f"{api_base}/ingest",
                data={"event_data": json.dumps(event)},
                files={"image_file": (evidence_path.name, fh, "image/jpeg")},
                timeout=5,
            )
        resp.raise_for_status()
        incident = resp.json()
        print(f"Success! Incident ID: {incident['incident_id']}")
        return incident
    except Exception as e:
        print(f"Failed to post event: {e}")
        if 'resp' in locals():
            print(resp.text)
        sys.exit(1)

def transition_status(api_base, incident_id, status, notes):
    print(f"Transitioning {incident_id} -> {status}...")
    try:
        r = requests.patch(
            f"{api_base}/incidents/{incident_id}/status",
            json={"status": status, "notes": notes},
            timeout=5
        )
        r.raise_for_status()
        print(f"Marked {status}")
    except Exception as e:
        print(f"Transition failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="SIH26124 Demo Orchestrator")
    parser.add_argument("--auto-advance", action="store_true", help="Automatically step through the resolution lifecycle")
    args = parser.parse_args()

    print("==================================================")
    print(" SIH26124 DEMO ORCHESTRATOR")
    print("==================================================\n")

    scenario = load_scenario()
    api_base = scenario["api_base_url"]
    
    check_backend(api_base)
    
    evidence_path = Path(__file__).resolve().parents[1] / "data" / "evidence" / "demo_pothole.jpg"
    generate_evidence(evidence_path)
    
    print("\n--- PHASE 1: INITIAL DETECTION ---")
    print("Simulating BUS-01 detecting a pothole on Route 42A.")
    
    evt1_id = f"EVT-{uuid.uuid4().hex[:10].upper()}"
    incident = post_event(api_base, build_event(scenario, scenario["bus_1"], evt1_id, evidence_path), evidence_path)
    inc_id = incident["incident_id"]
    
    pause1 = scenario["bus_1"]["pause_after_sec"]
    print(f"\nLook at the Command Center dashboard! A new critical card should appear.")
    print(f"Waiting {pause1} seconds for demonstration...")
    time.sleep(pause1)
    
    print("\n--- PHASE 2: MULTI-BUS VERIFICATION ---")
    print("Simulating BUS-02 driving over the exact same location and detecting the same pothole.")
    
    evt2_id = f"EVT-{uuid.uuid4().hex[:10].upper()}"
    incident = post_event(api_base, build_event(scenario, scenario["bus_2"], evt2_id, evidence_path), evidence_path)
    
    pause2 = scenario["bus_2"]["pause_after_sec"]
    print(f"\nLook at the Command Center dashboard again!")
    print(f"The incident card should now display a 'Verified by 2 Buses' badge and severity should be elevated.")
    print(f"Waiting {pause2} seconds for demonstration...")
    time.sleep(pause2)
    
    if args.auto_advance:
        print("\n--- PHASE 3: AUTONOMOUS LIFECYCLE RESOLUTION ---")
        delay = scenario["auto_advance_delay_sec"]
        
        # Next state from VERIFIED is ASSIGNED
        time.sleep(delay)
        transition_status(api_base, inc_id, "ASSIGNED", "Auto-demo: Dispatching maintenance crew.")
        
        time.sleep(delay)
        transition_status(api_base, inc_id, "IN_PROGRESS", "Auto-demo: Crew arrived at site.")
        
        time.sleep(delay)
        transition_status(api_base, inc_id, "RESOLVED", "Auto-demo: Pothole patched and verified.")
        
        print("\nDemo complete! The map pin should now be Green.")
    else:
        print("\n--- PHASE 3: MANUAL LIFECYCLE RESOLUTION ---")
        print("To complete the demo, click on the incident card in the dashboard.")
        print("Use the 'Operational Resolution Actions' buttons in the drawer to advance the incident to RESOLVED.")
        
    print("\n==================================================")
    print(" DEMO FINISHED")
    print("==================================================")

if __name__ == "__main__":
    main()
