import pandas as pd
import mysql.connector

# Function to get database connection
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='MechanicOrganizationalSystem',
    )

# Load the relevant rows and columns from the provided Excel file for the vehicles
file_path = r'C:/Users/rodrigo.monterroso/Downloads/24-09-2024 reporte de ubicacion monaco -.xlsx'  # Corrected path
sheet_vehicles = pd.read_excel(file_path, sheet_name=' Y EQUIPOS ', skiprows=7, usecols="I:O,R", nrows=140)

# Debugging: Print the first few rows to inspect the DataFrame structure
print(f"DEBUG: First few rows of the DataFrame:\n{sheet_vehicles.head()}")

# Debugging: Print the column headers to ensure proper loading of columns
print(f"DEBUG: Column names: {sheet_vehicles.columns}")

# Establish database connection
conn = get_db_connection()
cursor = conn.cursor()

# Iterate through the rows and build SQL queries based on column positions
for index, row in sheet_vehicles.iterrows():
    vehicle_name = row.iloc[0]  # Column I (Vehicle name)
    status = row.iloc[6]  # Column O (Status: 1 for work order, 2 for departure order)
    location = row.iloc[7]  # Column R (Location)

    # Debugging: Print the current row
    print(f"DEBUG: Vehicle Name: {vehicle_name}, Status: {status}, Location: {location}")

    # Query the vehiculosmonhaco table to find the vehicle's ID and current info
    vehicle_query = f"SELECT VehicleID, Status, Horometro, Empresa, Marca FROM vehiculosmonhaco WHERE VehicleName = '{vehicle_name}'"
    print(f"DEBUG: Executing query to find vehicle {vehicle_name}: {vehicle_query}")
    cursor.execute(vehicle_query)
    vehicle_data = cursor.fetchone()

    # If vehicle is found, proceed to create work or departure order
    if vehicle_data:
        vehicle_id, current_status, horometro, empresa, marca = vehicle_data
        print(f"DEBUG: Vehicle found - ID: {vehicle_id}, Status: {current_status}, Horometro: {horometro}, Empresa: {empresa}, Marca: {marca}")

        if status == 1:
            # Generate a work order
            print(f"DEBUG: Generating work order for vehicle {vehicle_name}")
            work_order_query = f"""
            INSERT INTO WorkOrders (VehicleID, WorkType, Description, Status, Lugar, Dueno, Marca, Empresa)
            VALUES (
                {vehicle_id},
                'Maintenance',
                'Generated from Excel',
                'En Taller',
                '{location}',
                '{empresa}',
                '{marca}',
                'Monhaco'
            );
            """
            print(f"DEBUG: Work Order Query:\n{work_order_query}")

        elif status == 2:
            # Generate a departure order
            print(f"DEBUG: Generating departure order for vehicle {vehicle_name}")
            departure_order_query = f"""
            INSERT INTO OrdenesdeSalida (VehicleID, VehicleName, IdOperador, NombreOperador, Comentarios, Ubicacion, Empresa, HoraCreado, OrdenDeSap, ClienteID, HorometroSalida)
            VALUES (
                {vehicle_id},
                '{vehicle_name}',
                16,  # 'Nadie' operator
                'Nadie',
                'Generated from Excel',
                '{location}',
                'Monhaco',
                NOW(),
                '1234',  # Assuming a generic SAP order number
                3,  # Cliente Tres
                {horometro}  # Use the horometro from the SQL data
            );
            """
            print(f"DEBUG: Departure Order Query:\n{departure_order_query}")
        else:
            print(f"DEBUG: No action for vehicle {vehicle_name} with status {status}")

    else:
        # If vehicle is not found in the SQL table
        print(f"DEBUG: Vehicle {vehicle_name} not found in the vehiculosmonhaco table.")
    
# Close the cursor and connection
cursor.close()
conn.close()
