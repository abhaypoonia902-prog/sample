#!/usr/bin/env python3
"""
ZetaTech HMS - IoT Room Simulator

This script simulates IoT devices that monitor and update room occupancy status.
It demonstrates the IoT integration concept without requiring physical hardware.

Usage:
    python iot_simulator.py

The simulator will:
1. Connect to the ZetaTech HMS API
2. Randomly update room occupancy status
3. Simulate realistic room usage patterns
"""

import requests
import random
import time
import argparse
from datetime import datetime
from typing import List, Dict

# Configuration
API_BASE_URL = "http://localhost:8000"
UPDATE_INTERVAL = 30  # seconds between updates

class IoTSimulator:
    """IoT Device Simulator for Room Monitoring"""
    
    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url
        self.rooms: List[Dict] = []
        print(f"🏥 ZetaTech HMS - IoT Simulator")
        print(f"📡 API Endpoint: {api_url}")
        print("-" * 50)
    
    def fetch_rooms(self) -> bool:
        """Fetch all rooms from the API."""
        try:
            response = requests.get(f"{self.api_url}/iot/rooms")
            if response.status_code == 200:
                self.rooms = response.json()
                return True
            else:
                print(f"❌ Failed to fetch rooms: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to API at {self.api_url}")
            print("   Make sure the backend server is running: uvicorn main:app --reload")
            return False
        except Exception as e:
            print(f"❌ Error fetching rooms: {e}")
            return False
    
    def update_room_status(self, room_id: int, is_occupied: bool, api_key: str) -> bool:
        """Update room occupancy status via API."""
        try:
            response = requests.put(
                f"{self.api_url}/iot/rooms/{room_id}",
                headers={"X-API-Key": api_key},
                json={"is_occupied": is_occupied, "current_patient_id": None}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error updating room {room_id}: {e}")
            return False
    
    def simulate_room_activity(self):
        """Simulate realistic room occupancy changes."""
        if not self.rooms:
            print("⚠️  No rooms available for simulation")
            return
        
        # Pick a random room
        room = random.choice(self.rooms)
        room_id = room['id']
        room_number = room['room_number']
        room_type = room['room_type']
        current_status = room['is_occupied']
        api_key = room.get('api_key', f'iot_key_{room_number}')
        
        # Determine new status based on current status
        # If occupied, 70% chance of becoming available (patient leaves)
        # If available, 30% chance of becoming occupied (new patient)
        if current_status:
            new_status = random.random() > 0.7  # 30% stay occupied
            action = "Patient discharged" if not new_status else "Patient still in room"
        else:
            new_status = random.random() < 0.3  # 30% chance of new patient
            action = "New patient admitted" if new_status else "Room remains available"
        
        # Only update if status changes
        if new_status != current_status:
            success = self.update_room_status(room_id, new_status, api_key)
            if success:
                status_icon = "🔴" if new_status else "🟢"
                status_text = "OCCUPIED" if new_status else "AVAILABLE"
                print(f"{status_icon} Room {room_number} ({room_type}) is now {status_text}")
                print(f"   → {action}")
                print(f"   → Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print()
                
                # Update local cache
                room['is_occupied'] = new_status
                room['last_updated'] = datetime.now().isoformat()
    
    def print_room_status(self):
        """Print current status of all rooms."""
        print("\n📊 Current Room Status:")
        print("-" * 50)
        
        occupied = sum(1 for r in self.rooms if r['is_occupied'])
        available = len(self.rooms) - occupied
        
        print(f"   Total Rooms: {len(self.rooms)}")
        print(f"   🟢 Available: {available}")
        print(f"   🔴 Occupied: {occupied}")
        print()
        
        for room in sorted(self.rooms, key=lambda x: x['room_number']):
            status_icon = "🔴" if room['is_occupied'] else "🟢"
            status_text = "Occupied" if room['is_occupied'] else "Available"
            print(f"   {status_icon} Room {room['room_number']:6} ({room['room_type']:12}) - {status_text}")
        
        print("-" * 50)
        print()
    
    def run(self, duration_minutes: int = None, verbose: bool = True):
        """Run the IoT simulator."""
        print("🚀 Starting IoT Simulator...")
        print()
        
        # Initial fetch
        if not self.fetch_rooms():
            print("❌ Failed to initialize. Exiting.")
            return
        
        self.print_room_status()
        
        print(f"⏱️  Update interval: {UPDATE_INTERVAL} seconds")
        print(f"🔄 Simulating room occupancy changes...")
        print("   Press Ctrl+C to stop")
        print()
        
        start_time = time.time()
        update_count = 0
        
        try:
            while True:
                # Check if duration exceeded
                if duration_minutes and (time.time() - start_time) > (duration_minutes * 60):
                    print(f"\n⏹️  Simulation completed after {duration_minutes} minutes")
                    break
                
                # Simulate activity
                self.simulate_room_activity()
                update_count += 1
                
                # Print status every 10 updates
                if verbose and update_count % 10 == 0:
                    self.print_room_status()
                
                # Wait before next update
                time.sleep(UPDATE_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Simulator stopped by user")
        
        # Final status
        print(f"\n📈 Statistics:")
        print(f"   Total updates: {update_count}")
        print(f"   Runtime: {(time.time() - start_time) / 60:.1f} minutes")
        print("\n👋 Goodbye!")


def seed_initial_data():
    """Seed initial data if not already present."""
    print("🌱 Seeding initial data...")
    try:
        response = requests.post(f"{API_BASE_URL}/seed")
        if response.status_code == 200:
            print("✅ Initial data seeded successfully")
            return True
        else:
            print(f"⚠️  Seed response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="ZetaTech HMS - IoT Room Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python iot_simulator.py              # Run indefinitely
  python iot_simulator.py -d 5         # Run for 5 minutes
  python iot_simulator.py --seed       # Seed initial data only
        """
    )
    parser.add_argument(
        "-d", "--duration",
        type=int,
        help="Run simulation for specified minutes (default: run indefinitely)"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed initial data and exit"
    )
    parser.add_argument(
        "--api-url",
        default=API_BASE_URL,
        help=f"API base URL (default: {API_BASE_URL})"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet mode (less output)"
    )
    
    args = parser.parse_args()
    
    # Seed data if requested
    if args.seed:
        seed_initial_data()
        return
    
    # Create and run simulator
    simulator = IoTSimulator(api_url=args.api_url)
    simulator.run(duration_minutes=args.duration, verbose=not args.quiet)


if __name__ == "__main__":
    main()
