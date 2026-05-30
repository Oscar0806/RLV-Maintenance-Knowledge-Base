"""Load and process the RLV maintenance knowledge base."""

import json
import pandas as pd
import os


def load_database():
    """Load the JSON database and return structured DataFrames."""
    data_path = os.path.join(os.path.dirname(__file__), "data",
                             "rlv_maintenance_data.json")
    
    with open(data_path, "r") as f:
        db = json.load(f)
    
    # Vehicles DataFrame
    vehicles_df = pd.DataFrame(db["vehicles"])
    
    # Maintenance records DataFrame
    records_df = pd.DataFrame(db["maintenance_records"])
    
    # Merge vehicle info into records
    merged_df = records_df.merge(
        vehicles_df[["id", "name", "operator", "class"]],
        left_on="vehicle_id",
        right_on="id",
        suffixes=("", "_vehicle")
    )
    merged_df.rename(columns={"name": "vehicle_name"}, inplace=True)
    
    taxonomy = db["classification_taxonomy"]
    metadata = db["metadata"]
    
    return vehicles_df, records_df, merged_df, taxonomy, metadata


def get_summary_stats(merged_df):
    """Compute summary statistics for the dashboard."""
    stats = {
        "total_records": len(merged_df),
        "vehicles_covered": merged_df["vehicle_id"].nunique(),
        "subsystems_covered": merged_df["subsystem"].nunique(),
        "total_maintenance_hours": merged_df["estimated_duration_hours"].sum(),
        "flight_critical_pct": round(
            (merged_df["criticality"] == "Flight-Critical").mean() * 100, 1
        ),
        "records_by_vehicle": merged_df["vehicle_name"].value_counts().to_dict(),
        "records_by_subsystem": merged_df["subsystem"].value_counts().to_dict(),
        "records_by_type": merged_df["maintenance_type"].value_counts().to_dict(),
        "records_by_method": merged_df["inspection_method"].value_counts().to_dict(),
        "records_by_phase": merged_df["turnaround_phase"].value_counts().to_dict(),
        "records_by_criticality": merged_df["criticality"].value_counts().to_dict(),
        "hours_by_vehicle": merged_df.groupby("vehicle_name")[
            "estimated_duration_hours"].sum().to_dict(),
        "hours_by_subsystem": merged_df.groupby("subsystem")[
            "estimated_duration_hours"].sum().to_dict(),
    }
    return stats


if __name__ == "__main__":
    vehicles, records, merged, taxonomy, metadata = load_database()
    stats = get_summary_stats(merged)
    
    print(f"Database: {metadata['title']}")
    print(f"Records: {stats['total_records']}")
    print(f"Vehicles: {stats['vehicles_covered']}")
    print(f"Subsystems: {stats['subsystems_covered']}")
    print(f"Total maintenance hours: {stats['total_maintenance_hours']}")
    print(f"Flight-critical: {stats['flight_critical_pct']}%")