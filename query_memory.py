#!/usr/bin/env python3
"""Query UserMemory for a specific user"""
import sqlite3
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('adgen.db')
cursor = conn.cursor()

# Query for user_id=6 (wooseoktest)
user_id = 6

print(f"\n{'='*80}")
print(f"UserMemory records for user_id={user_id} (wooseoktest)")
print(f"{'='*80}\n")

cursor.execute("""
    SELECT id, user_id, memory_text, importance, created_at, updated_at
    FROM user_memories
    WHERE user_id = ?
    ORDER BY created_at DESC
""", (user_id,))

results = cursor.fetchall()

if results:
    for row in results:
        memory_id, uid, memory_text, importance, created_at, updated_at = row
        print(f"Memory ID: {memory_id}")
        print(f"User ID: {uid}")
        print(f"Importance: {importance}")
        print(f"Created: {created_at}")
        print(f"Updated: {updated_at}")
        print(f"\nMemory Text:")
        print("-" * 80)
        print(memory_text)
        print("-" * 80)
        print()
else:
    print(f"No memory records found for user_id={user_id}")
    print("\nThis could mean:")
    print("1. The dialogue didn't complete (is_complete=False)")
    print("2. final_content was empty")
    print("3. Memory update failed silently")
    print("\nCheck server logs for memory update messages.")

conn.close()

print(f"\n{'='*80}\n")
