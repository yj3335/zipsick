# demo/query_db.py
# Simple helper script to inspect ClickHouse tables and print data counts.

import os
from storage.clickhouse import client

def inspect_db():
    try:
        ch = client()
        print("Connected to ClickHouse successfully.")
        
        # 1. Show existing tables
        tables = ch.query("SHOW TABLES FROM outbreak").result_rows
        print("\nTables in database 'outbreak':")
        for table in tables:
            print(f" - {table[0]}")
            
        # 2. Get signals count
        signals_count = ch.query("SELECT count() FROM outbreak.outbreak_signals").result_rows[0][0]
        print(f"\nTotal rows in 'outbreak_signals' table: {signals_count}")
        
        # 3. Get alerts count
        alerts_count = ch.query("SELECT count() FROM outbreak.alerts").result_rows[0][0]
        print(f"Total rows in 'alerts' table: {alerts_count}")
        
        # 4. Show sample baseline signals if present
        if signals_count > 0:
            print("\nRecent 5 signals in 'outbreak_signals':")
            sample_signals = ch.query(
                "SELECT timestamp, zip, symptom, source_type, synthetic FROM outbreak.outbreak_signals ORDER BY timestamp DESC LIMIT 5"
            ).named_results()
            for s in sample_signals:
                print(f" - [{s['timestamp']}] ZIP={s['zip']} Symptom={s['symptom']} Source={s['source_type']} Synthetic={s['synthetic']}")
                
        # 5. Show sample alerts if present
        if alerts_count > 0:
            print("\nRecent 5 alerts in 'alerts':")
            sample_alerts = ch.query(
                "SELECT created_at, alert_id, zip, symptom, recent_count, z_score, clinical_status FROM outbreak.alerts ORDER BY created_at DESC LIMIT 5"
            ).named_results()
            for a in sample_alerts:
                print(f" - [{a['created_at']}] AlertID={a['alert_id']} ZIP={a['zip']} Symptom={a['symptom']} RecentCount={a['recent_count']} Z-Score={a['z_score']} Status={a['clinical_status']}")
                
    except Exception as e:
        print(f"Error inspecting database: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    inspect_db()
