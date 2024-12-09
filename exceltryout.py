import os
import logging
import mysql.connector
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)

def standardize_vehicle_name(vehicle_name):
    # Remove leading zeros after the prefix and return the standardized name
    parts = vehicle_name.split('-')
    standardized_name = f"{parts[0]}-{int(parts[1])}" if len(parts) > 1 else vehicle_name
    return standardized_name

def get_db_connection():
    """Establish connection with the database."""
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='MechanicOrganizationalSystem',
    )

def update_horometros_from_excel(file_path, vehicle_table):
    try:
        # Load Excel file
        logging.info("Loading Excel file...")
        df = pd.read_excel(file_path, header=None)
        df.columns = ['VehicleName', 'Horometro']
        
        # Standardize vehicle names
        df['VehicleName'] = df['VehicleName'].apply(standardize_vehicle_name)

        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update each vehicle's Horometro
        logging.info("Updating vehicle Horometros in database...")
        for _, row in df.iterrows():
            vehicle_name = row['VehicleName']
            horometro = row['Horometro']

            if pd.notna(vehicle_name) and pd.notna(horometro) and horometro != 0:
                # Check if the current Horometro in the database is 0
                cursor.execute(f'''
                    SELECT Horometro
                    FROM {vehicle_table}
                    WHERE VehicleName = %s
                ''', (vehicle_name,))
                current_horometro = cursor.fetchone()

                if current_horometro and current_horometro[0] == 0:
                    cursor.execute(f'''
                        UPDATE {vehicle_table}
                        SET Horometro = %s
                        WHERE VehicleName = %s
                    ''', (horometro, vehicle_name))
                    logging.info(f"Updated Horometro for {vehicle_name}: {horometro}")

        # Commit the changes
        conn.commit()

        logging.info("Vehicle Horometros updated successfully.")

        # Close the cursor and connection
        cursor.close()
        conn.close()

    except Exception as e:
        logging.error(f"Error updating Horometros: {e}")

if __name__ == "__main__":
    file_path = 'C:\\Users\\rodrigo.monterroso\\Downloads\\flotas first running 7.9.2024\\flotas Upload 30 6 24\\Flotas\\UploadHorometros.xlsx'
    vehicle_table = 'Vehicles'  # Change this to the appropriate table for the company
    update_horometros_from_excel(file_path, vehicle_table)
