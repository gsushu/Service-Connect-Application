# insert_dummy_data.py
import sys
import os
import random
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values
from passlib.context import CryptContext

# Password hashing setup (matching your auth.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

# Database connection string
DATABASE_URL = "postgresql://neondb_owner:npg_IOzo2lHDFaq7@ep-polished-paper-a54rdfdi-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require" # Replace with your actual URL if different

# Request statuses - updated to match SQLAlchemy Enum
REQUEST_STATUS_CHOICES = ["pending", "negotiating", "accepted", "inprogress", "completed", "cancelled"]

# Urgency levels
URGENCY_LEVELS = ["Low", "Medium", "High"]

# Worker statuses
WORKER_STATUSES = ["pending", "approved", "rejected"]

# Connect to the database
try:
    conn = psycopg2.connect(DATABASE_URL)
    print("Connected to database successfully!")
    cursor = conn.cursor()
except Exception as e:
    print(f"Database connection error: {e}")
    sys.exit(1)

# Clear existing data (optional, comment out if not needed)
# Corrected 'worker_categories' to 'worker_service_categories'
# Removed 'worker_services' as the table is removed from models
tables_to_truncate = [
    "request_quotes", # Has FK to requests and workers
    "requests",       # Has FK to users, workers, services, user_locations
    "user_locations", # Has FK to users
    "worker_service_categories", # Join table for workers and service_categories
    "services",       # Has FK to service_categories
    "service_categories",
    "workers",
    "users",
    "admins"
]
# Truncate tables that might exist from previous schema if needed, then the current ones
# Add 'worker_services' here IF you had it from an OLD schema and want to ensure it's gone
# but it's better to handle schema migrations separately.
# For now, we only truncate tables defined in the NEW schema.
# If 'worker_services' table still exists physically in DB from old schema and causes FK issues,
# you might need to manually DROP it or add it here for a one-time cleanup.

print("Attempting to truncate tables...")
for table in tables_to_truncate:
    try:
        # Check if table exists before truncating
        cursor.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}');")
        table_exists = cursor.fetchone()[0]
        if table_exists:
            cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
            print(f"Truncated table {table}")
        else:
            print(f"Table {table} does not exist, skipping truncation.")
    except Exception as e:
        print(f"Error truncating table {table}: {e}")
        conn.rollback() # Rollback on error for this table
        # Decide if you want to exit or continue
        # sys.exit(f"Failed to truncate {table}. Exiting.")

conn.commit()
print("Table truncation process completed.")

# Generate dummy data

# 1. Admin data
admins_data = []
admin_passwords = []

for i in range(5):  # Creating 5 admins
    username = f"admin{i+1}"
    password = f"admin{i+1}pass"
    hashed_password = get_password_hash(password)
    admins_data.append((username, hashed_password))
    admin_passwords.append((username, password))

try:
    if admins_data:
        query = "INSERT INTO admins (username, password) VALUES %s RETURNING admin_id;"
        # Reset sequence only if table exists and is empty or we want to overwrite
        cursor.execute("SELECT setval(pg_get_serial_sequence('admins', 'admin_id'), 1, false);")
        execute_values(cursor, query, admins_data)
        print(f"{len(admins_data)} Admin data inserted successfully!")
        conn.commit()
except Exception as e:
    print(f"Error inserting admin data: {e}")
    conn.rollback()

# 2. User data
users_data = []
user_passwords = []
user_ids = []

for i in range(20):  # Creating 20 users
    username = f"user{i+1}"
    email = f"user{i+1}@example.com"
    mobile = f"90000{i:05d}"
    password = f"user{i+1}pass"
    hashed_password = get_password_hash(password)
    users_data.append((username, email, mobile, hashed_password))
    user_passwords.append((username, password))

try:
    if users_data:
        query = "INSERT INTO users (username, email, mobile, password) VALUES %s RETURNING user_id;"
        cursor.execute("SELECT setval(pg_get_serial_sequence('users', 'user_id'), 1, false);")
        admin_ids_returned = execute_values(cursor, query, users_data, fetch=True)
        user_ids = [row[0] for row in admin_ids_returned]
        print(f"{len(user_ids)} User data inserted successfully!")
        conn.commit()
except Exception as e:
    print(f"Error inserting user data: {e}")
    conn.rollback()

# 3. Service Categories data
categories_list = [
    "Plumbing", "Electrical", "Carpentry", "Cleaning", "Gardening",
    "Painting", "Flooring", "HVAC", "Roofing", "Appliance Repair",
    "Masonry", "Furniture Assembly", "Window Repair", "Pest Control", "Security"
]

categories_data = [(category,) for category in categories_list]
category_ids = []

try:
    if categories_data:
        query = "INSERT INTO service_categories (name) VALUES %s RETURNING category_id;"
        cursor.execute("SELECT setval(pg_get_serial_sequence('service_categories', 'category_id'), 1, false);")
        category_ids_returned = execute_values(cursor, query, categories_data, fetch=True)
        category_ids = [row[0] for row in category_ids_returned]
        print(f"{len(category_ids)} Service categories inserted successfully!")
        conn.commit()
except Exception as e:
    print(f"Error inserting service categories: {e}")
    conn.rollback()

# 4. Services data
services_data = [] # List of tuples: (name, description, category_id)
service_ids = []
service_map_for_requests = [] # Store (service_id, name, category_id) for easier lookup later

if category_ids:
    for cat_id_idx, cat_id in enumerate(category_ids):
        category_name = categories_list[cat_id_idx] # Relies on categories_list and category_ids maintaining order

        specific_services = []
        if category_name == "Plumbing":
            specific_services = [
                ("Pipe Repair", "Fix leaking or broken pipes"),
                ("Drain Cleaning", "Unclog and clean drains"),
                ("Faucet Installation", "Install new faucets"),
                ("Water Heater Repair", "Fix water heater issues")
            ]
        elif category_name == "Electrical":
            specific_services = [
                ("Outlet Installation", "Install new electrical outlets"),
                ("Light Fixture Installation", "Install ceiling or wall lights"),
                ("Circuit Breaker Repair", "Fix or replace circuit breakers"),
                ("Electrical Panel Upgrade", "Upgrade electrical service panel")
            ]
        else:
            specific_services = [
                (f"{category_name} Service 1", f"Basic {category_name.lower()} service"),
                (f"{category_name} Service 2", f"Advanced {category_name.lower()} service"),
                (f"{category_name} Installation", f"Install {category_name.lower()} components")
            ]

        for name, desc in specific_services:
            services_data.append((name, desc, cat_id))

    try:
        if services_data:
            query = "INSERT INTO services (name, description, category_id) VALUES %s RETURNING service_id, name, category_id;"
            cursor.execute("SELECT setval(pg_get_serial_sequence('services', 'service_id'), 1, false);")
            services_returned = execute_values(cursor, query, services_data, fetch=True)
            service_ids = [row[0] for row in services_returned]
            service_map_for_requests = [(row[0], row[1], row[2]) for row in services_returned] # Store (id, name, cat_id)
            print(f"{len(service_ids)} Services inserted successfully!")
            conn.commit()
    except Exception as e:
        print(f"Error inserting services: {e}")
        conn.rollback()
else:
    print("No category IDs found, skipping service data insertion.")


# 5. Worker data
workers_data_tuples = [] # For insertion
worker_passwords = []
worker_category_relations_to_insert = [] # Tuples of (worker_id_placeholder, category_id)
worker_ids = []

if category_ids:
    for i in range(20): # Create 20 workers
        username = f"worker{i+1}"
        email = f"worker{i+1}@example.com"
        mobile = f"80000{i:05d}"
        employee_number = f"EMP{i+1:04d}"
        password = f"worker{i+1}pass"
        hashed_password = get_password_hash(password)
        status = random.choice(WORKER_STATUSES)
        pincode = f"{random.randint(10000, 99999)}"
        radius = random.randint(5, 30)

        workers_data_tuples.append((username, email, mobile, employee_number, hashed_password, status, pincode, radius))
        worker_passwords.append((username, password))

        # Assign 1-3 random categories to this worker (using placeholder for worker_id)
        num_worker_categories = random.randint(1, min(3, len(category_ids)))
        selected_cat_ids_for_worker = random.sample(category_ids, num_worker_categories)
        for cat_id in selected_cat_ids_for_worker:
            worker_category_relations_to_insert.append((i, cat_id)) # Use 'i' as placeholder for worker index
else:
    print("No category IDs available, skipping worker data and their category assignments.")

if workers_data_tuples:
    try:
        query = """
        INSERT INTO workers (username, email, mobile, employee_number, password, status, pincode, radius)
        VALUES %s RETURNING worker_id;
        """
        cursor.execute("SELECT setval(pg_get_serial_sequence('workers', 'worker_id'), 1, false);")
        workers_returned = execute_values(cursor, query, workers_data_tuples, fetch=True)
        worker_ids = [row[0] for row in workers_returned]
        print(f"{len(worker_ids)} Workers inserted successfully!")
        conn.commit()
    except Exception as e:
        print(f"Error inserting workers: {e}")
        conn.rollback()
else:
    print("No worker data to insert.")

# 6. Worker-Category relationships (using worker_service_categories table)
actual_worker_category_relations = []
if worker_ids and worker_category_relations_to_insert:
    for worker_idx_placeholder, cat_id in worker_category_relations_to_insert:
        if worker_idx_placeholder < len(worker_ids):
            actual_worker_id = worker_ids[worker_idx_placeholder]
            actual_worker_category_relations.append((actual_worker_id, cat_id))

if actual_worker_category_relations:
    try:
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'worker_service_categories');")
        table_exists = cursor.fetchone()[0]
        if table_exists:
            # No sequence to reset for a join table with composite primary key
            query = "INSERT INTO worker_service_categories (worker_id, category_id) VALUES %s ON CONFLICT (worker_id, category_id) DO NOTHING;"
            execute_values(cursor, query, actual_worker_category_relations)
            print(f"{len(actual_worker_category_relations)} Worker-Category relationships inserted successfully!")
            conn.commit()
        else:
            print("Table 'worker_service_categories' does not exist, skipping relationship insertion.")
    except Exception as e:
        print(f"Error inserting worker-category relationships: {e}")
        conn.rollback()
else:
    print("No worker-category relationships to insert (possibly due to no workers or no relations defined).")


# Section 7 for Worker-Service relationships has been REMOVED as per SQLAlchemy model changes.
# If you still need a way to indicate worker availability for specific services,
# you'd need to re-introduce a table like worker_services in your models.


# 8. User Locations
user_locations_data_tuples = [] # For insertion (user_id, address, pincode)
location_ids = []
user_location_map = {} # To store user_id -> [location_id1, location_id2, ...]

pincodes_sample = [f"{random.randint(10000, 99999)}" for _ in range(15)] # Corrected variable name
areas = ["Downtown", "Uptown", "Westside", "Eastside", "Northend", "Southend"]
streets = ["Main St", "Oak Ave", "Maple Rd", "Pine Blvd", "Cedar Ln", "Elm Dr"]

if user_ids:
    for user_id in user_ids:
        num_locations = random.randint(1, 3)
        user_location_map[user_id] = [] # Initialize list for this user

        for _ in range(num_locations):
            area = random.choice(areas)
            street = random.choice(streets)
            number = random.randint(1, 9999)
            pincode = random.choice(pincodes_sample)
            address = f"{number} {street}, {area}"
            user_locations_data_tuples.append((user_id, address, pincode))

    try:
        if user_locations_data_tuples:
            query = "INSERT INTO user_locations (user_id, address, pincode) VALUES %s RETURNING location_id, user_id;"
            cursor.execute("SELECT setval(pg_get_serial_sequence('user_locations', 'location_id'), 1, false);")
            locations_returned = execute_values(cursor, query, user_locations_data_tuples, fetch=True)

            for loc_id, returned_user_id in locations_returned:
                location_ids.append(loc_id)
                if returned_user_id in user_location_map:
                    user_location_map[returned_user_id].append(loc_id)
                else: # Should not happen if logic is correct
                    user_location_map[returned_user_id] = [loc_id]

            print(f"{len(location_ids)} User locations inserted successfully!")
            conn.commit()
    except Exception as e:
        print(f"Error inserting user locations: {e}")
        conn.rollback()
else:
    print("Skipping user location insertion due to missing user_ids.")

# 9. Service Requests
requests_master_list = [] # Stores dicts of request data before DB insertion
now = datetime.now()
NUM_REQUESTS = 60
actual_request_ids = [] # Initialize actual_request_ids here

print(f"\nGenerating {NUM_REQUESTS} service requests...")

if user_ids and service_map_for_requests and location_ids and user_location_map:
    for i in range(NUM_REQUESTS):
        user_id_chosen = random.choice(user_ids)

        # Ensure the chosen user has locations
        if not user_location_map.get(user_id_chosen):
            # print(f"User {user_id_chosen} has no locations, skipping request for this user.")
            # Fallback: pick any location if user has none (though this shouldn't happen with current logic)
            if not location_ids:
                print("No locations available at all. Cannot create request.")
                continue
            location_id_chosen = random.choice(location_ids)
        else:
            location_id_chosen = random.choice(user_location_map[user_id_chosen])

        service_id_chosen, service_name_chosen, _ = random.choice(service_map_for_requests)
        status_chosen = random.choice(REQUEST_STATUS_CHOICES)

        description_text = f"Request #{i+1} for {service_name_chosen} (Status: {status_chosen})"
        urgency_chosen = random.choice(URGENCY_LEVELS)
        additional_notes_text = f"Notes for request {i+1}." if random.random() > 0.5 else None

        days_ago_created = random.randint(5, 120)
        created_at_time = now - timedelta(days=days_ago_created, hours=random.randint(0,23), minutes=random.randint(0,59))

        user_quoted_price_val = round(random.uniform(25, 250), 2) if random.random() < 0.7 else None

        worker_id_final = None
        final_price_val = None
        updated_at_time = created_at_time

        if status_chosen in ["accepted", "inprogress", "completed"]:
            if worker_ids: worker_id_final = random.choice(worker_ids)
            else: # No workers, cannot be in these states logically
                status_chosen = "pending" # demote status

        if status_chosen in ["accepted", "inprogress", "completed"] and worker_id_final: # Check worker_id_final too
            final_price_val = round(random.uniform(max(30.0, (user_quoted_price_val or 40.0) * 0.8), (user_quoted_price_val or 300.0) * 1.5), 2)
            if days_ago_created > 1:
                days_ago_updated = random.randint(1, days_ago_created - 1) # Update must be after create
                updated_at_time = now - timedelta(days=days_ago_updated)
            else: # Updated within the same day
                updated_at_time = created_at_time + timedelta(hours=random.randint(1,12))

        elif status_chosen == "cancelled":
            # A request could be cancelled before or after a worker was assigned (implicitly)
            if random.random() < 0.4 and worker_ids: # Simulating cancellation after a worker might have been implicitly chosen
                worker_id_final = random.choice(worker_ids) # This worker_id is on the request table
                final_price_val = round(random.uniform(40, 350), 2) # Could be a "final" offer before cancellation
            if days_ago_created > 1:
                days_ago_updated = random.randint(1, days_ago_created - 1)
                updated_at_time = now - timedelta(days=days_ago_updated)
            else:
                updated_at_time = created_at_time + timedelta(hours=random.randint(1,24))

        # Ensure updated_at is not before created_at and not in future
        if updated_at_time < created_at_time:
            updated_at_time = created_at_time + timedelta(minutes=random.randint(5,60))
        if updated_at_time > now:
            updated_at_time = now

        requests_master_list.append({
            "user_id": user_id_chosen, "worker_id": worker_id_final, "service_id": service_id_chosen,
            "user_location_id": location_id_chosen, "status": status_chosen, "description": description_text,
            "urgency_level": urgency_chosen, "additional_notes": additional_notes_text,
            "created_at": created_at_time, "updated_at": updated_at_time,
            "user_quoted_price": user_quoted_price_val, "final_price": final_price_val,
            "temp_id": i # Temporary ID for mapping to quotes later
        })

    requests_tuples_for_db = [
        (r['user_id'], r['worker_id'], r['service_id'], r['user_location_id'], r['status'],
         r['description'], r['urgency_level'], r['additional_notes'], r['created_at'],
         r['updated_at'], r['user_quoted_price'], r['final_price'])
        for r in requests_master_list
    ]

    if requests_tuples_for_db:
        try:
            query = """
            INSERT INTO requests (
                user_id, worker_id, service_id, user_location_id,
                status, description, urgency_level, additional_notes, created_at, updated_at,
                user_quoted_price, final_price
            ) VALUES %s RETURNING request_id;
            """
            cursor.execute("SELECT setval(pg_get_serial_sequence('requests', 'request_id'), 1, false);")
            requests_returned = execute_values(cursor, query, requests_tuples_for_db, fetch=True)
            actual_request_ids = [row[0] for row in requests_returned]
            print(f"{len(actual_request_ids)} Service requests inserted successfully!")
            conn.commit()
        except Exception as e:
            print(f"Error inserting service requests: {e}")
            conn.rollback()
    else:
        print("No request tuples generated for DB insertion.")
else:
    print("Skipping service request insertion due to missing user_ids, service_ids/service_map, or location_ids/user_location_map.")

# Map temp_id from requests_master_list to actual_request_id
temp_to_actual_req_id = {}
if actual_request_ids and len(actual_request_ids) == len(requests_master_list): # Ensure mapping is possible
    temp_to_actual_req_id = {
        requests_master_list[j]['temp_id']: actual_request_ids[j]
        for j in range(len(actual_request_ids))
    }
else:
    print("Mismatch in request master list and actual request IDs, or no requests inserted. Skipping quote generation based on this mapping.")


# 10. Request Quotes
request_quotes_data = []
print(f"\nGenerating request quotes...")

if actual_request_ids and worker_ids and temp_to_actual_req_id:
    for req_info in requests_master_list:
        if req_info['temp_id'] not in temp_to_actual_req_id:
            # This request was not successfully inserted or mapped
            continue

        actual_req_id = temp_to_actual_req_id[req_info['temp_id']]
        req_status = req_info['status']
        req_created_at = req_info['created_at']
        req_updated_at = req_info['updated_at'] # This is the request's updated_at

        # Logic for pending/negotiating: workers send quotes
        if req_status in ["pending", "negotiating"]:
            if random.random() < 0.85: # 85% chance of getting quotes
                num_quotes_to_generate = random.randint(1, min(3, len(worker_ids)))
                workers_for_quoting = random.sample(worker_ids, num_quotes_to_generate)

                for q_worker_id in workers_for_quoting:
                    price = round(random.uniform(max(20.0, (req_info['user_quoted_price'] or 30.0) * 0.7),
                                               (req_info['user_quoted_price'] or 300.0) * 1.8), 2)
                    comments = f"Quote for: {req_info['description'][:25]}..."

                    # Quote created_at must be after request created_at and before request updated_at (if request is still pending/negotiating)
                    # and not in the future
                    time_window_for_quote = req_updated_at - req_created_at
                    if time_window_for_quote.total_seconds() <= 0: time_window_for_quote = timedelta(hours=1) # Min 1 hour window

                    q_created_at = req_created_at + timedelta(seconds=random.uniform(0, time_window_for_quote.total_seconds() * 0.8)) # Quote created somewhere within 80% of request's life so far
                    q_created_at = min(q_created_at, now - timedelta(minutes=5)) # Ensure not in future
                    if q_created_at < req_created_at: q_created_at = req_created_at + timedelta(minutes=random.randint(5,30))


                    request_quotes_data.append((actual_req_id, q_worker_id, price, comments, q_created_at, q_created_at)) # updated_at = created_at for new quote

        # Logic for accepted/inprogress/completed: one "winning" quote exists
        elif req_status in ["accepted", "inprogress", "completed"]:
            accepted_worker_id = req_info['worker_id'] # This is the worker_id on the request table
            accepted_price = req_info['final_price']   # This is the final_price on the request table

            if accepted_worker_id and accepted_price is not None:
                comments = f"Accepted: {req_info['description'][:25]}..."

                # Quote created_at must be before request's final update (when it was accepted)
                # And after request creation
                time_window_for_accepted_quote = req_updated_at - req_created_at
                if time_window_for_accepted_quote.total_seconds() <= 0: time_window_for_accepted_quote = timedelta(hours=1)

                # The accepted quote was likely created some time before the request was marked accepted (req_updated_at)
                q_created_at = req_created_at + timedelta(seconds=random.uniform(0, time_window_for_accepted_quote.total_seconds() * 0.5))
                q_created_at = min(q_created_at, req_updated_at - timedelta(hours=1)) # Ensure quote created before request acceptance time
                if q_created_at < req_created_at: q_created_at = req_created_at + timedelta(minutes=random.randint(5,30))

                # The quote's updated_at could be the time it was accepted (matching request's updated_at)
                q_updated_at = req_updated_at
                q_updated_at = min(q_updated_at, now) # Ensure not in future
                if q_updated_at < q_created_at: q_updated_at = q_created_at # Ensure updated not before created

                request_quotes_data.append((actual_req_id, accepted_worker_id, accepted_price, comments, q_created_at, q_updated_at))

                # Optionally, add some "losing" quotes for these requests
                num_other_quotes = random.randint(0, 2)
                other_workers = [w_id for w_id in worker_ids if w_id != accepted_worker_id]
                if num_other_quotes > 0 and other_workers:
                    chosen_other_workers = random.sample(other_workers, min(num_other_quotes, len(other_workers)))
                    for o_worker_id in chosen_other_workers:
                        price = round(random.uniform(max(20.0, (req_info['user_quoted_price'] or 30.0) * 0.6),
                                                   (req_info['user_quoted_price'] or 350.0) * 2.0), 2)
                        comments_other = f"Alternative: {req_info['description'][:20]}..."

                        # These other quotes were also created before request acceptance
                        q_other_created_at = req_created_at + timedelta(seconds=random.uniform(0, time_window_for_accepted_quote.total_seconds() * 0.4))
                        q_other_created_at = min(q_other_created_at, req_updated_at - timedelta(hours=2)) # Ensure created well before acceptance
                        if q_other_created_at < req_created_at: q_other_created_at = req_created_at + timedelta(minutes=random.randint(5,20))
                        q_other_created_at = min(q_other_created_at, now - timedelta(minutes=10))


                        request_quotes_data.append((actual_req_id, o_worker_id, price, comments_other, q_other_created_at, q_other_created_at))

        # Logic for cancelled requests (might have quotes or not)
        elif req_status == "cancelled":
            # Case 1: Cancelled after a worker/price was agreed (less common, but possible)
            if req_info['worker_id'] and req_info['final_price'] and random.random() < 0.3:
                comments = f"Agreed then Cancelled: {req_info['description'][:20]}..."
                # Similar logic to accepted quote's creation time
                time_window_for_cancelled_quote = req_updated_at - req_created_at
                if time_window_for_cancelled_quote.total_seconds() <=0: time_window_for_cancelled_quote = timedelta(hours=1)

                q_created_at = req_created_at + timedelta(seconds=random.uniform(0, time_window_for_cancelled_quote.total_seconds() * 0.5))
                q_created_at = min(q_created_at, req_updated_at - timedelta(hours=1))
                if q_created_at < req_created_at: q_created_at = req_created_at + timedelta(minutes=random.randint(5,30))
                q_created_at = min(q_created_at, now - timedelta(minutes=5))

                request_quotes_data.append((actual_req_id, req_info['worker_id'], req_info['final_price'], comments, q_created_at, q_created_at))
            # Case 2: Cancelled while pending/negotiating, may have some quotes
            elif random.random() < 0.6: # 60% chance of having some quotes before cancellation
                num_quotes_to_generate = random.randint(1, min(2, len(worker_ids)))
                workers_for_quoting = random.sample(worker_ids, num_quotes_to_generate)
                for q_worker_id in workers_for_quoting:
                    price = round(random.uniform(30, 400), 2)
                    comments = f"Quote (req cancelled): {req_info['description'][:20]}..."

                    time_window_for_quote = req_updated_at - req_created_at
                    if time_window_for_quote.total_seconds() <=0: time_window_for_quote = timedelta(hours=1)

                    q_created_at = req_created_at + timedelta(seconds=random.uniform(0, time_window_for_quote.total_seconds() * 0.8))
                    q_created_at = min(q_created_at, req_updated_at - timedelta(minutes=30)) # Quote must be before cancellation time
                    if q_created_at < req_created_at: q_created_at = req_created_at + timedelta(minutes=random.randint(5,20))
                    q_created_at = min(q_created_at, now - timedelta(minutes=5))


                    request_quotes_data.append((actual_req_id, q_worker_id, price, comments, q_created_at, q_created_at))

    if request_quotes_data:
        try:
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'request_quotes');")
            request_quotes_table_exists = cursor.fetchone()[0]

            if request_quotes_table_exists:
                query = """
                INSERT INTO request_quotes (
                    request_id, worker_id, worker_quoted_price,
                    worker_comments, created_at, updated_at
                ) VALUES %s;
                """
                # No sequence to reset for quote_id if it's a simple auto-incrementing PK
                cursor.execute("SELECT setval(pg_get_serial_sequence('request_quotes', 'quote_id'), 1, false);")
                execute_values(cursor, query, request_quotes_data)
                print(f"{len(request_quotes_data)} Request quotes inserted successfully!")
                conn.commit()
            else:
                print("Table 'request_quotes' does not exist, skipping quote data insertion.")
        except Exception as e:
            print(f"Error inserting request quotes: {e}")
            conn.rollback()
    else:
        print("No request quotes data generated to insert.")
else:
    print("Skipping request quotes insertion due to missing actual_request_ids, worker_ids, or temp_to_actual_req_id mapping.")


# Print summary
print("\n--- DATA INSERTION SUMMARY ---")
print(f"Admins: {len(admins_data)}")
print(f"Users: {len(user_ids)}") # Using len(user_ids) as it reflects actual insertions
print(f"Workers: {len(worker_ids)}")
print(f"Service Categories: {len(category_ids)}")
print(f"Services: {len(service_ids)}")
print(f"User Locations: {len(location_ids)}")
print(f"Service Requests: {len(actual_request_ids)}")
print(f"Request Quotes: {len(request_quotes_data)}")
print(f"Worker-Category Relationships: {len(actual_worker_category_relations)}")
# Worker-Service Relationships section was removed

print("\n--- LOGIN CREDENTIALS (SAMPLE) ---")
print("Admins (first one):")
if admin_passwords: print(f"  Username: {admin_passwords[0][0]}, Password: {admin_passwords[0][1]}")

print("\nUsers (first one):")
if user_passwords: print(f"  Username: {user_passwords[0][0]}, Password: {user_passwords[0][1]}")

print("\nWorkers (first one):")
if worker_passwords: print(f"  Username: {worker_passwords[0][0]}, Password: {worker_passwords[0][1]}")

# Close connection
cursor.close()
conn.close()
print("\nDatabase connection closed.")
print("Dummy data insertion script finished.")