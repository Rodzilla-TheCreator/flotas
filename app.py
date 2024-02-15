from flask import Flask, render_template, request, redirect, url_for, flash, jsonify,json
import mysql.connector
from datetime import datetime, timedelta
from hdbcli import dbapi as hana
import logging




logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'carepa'
#.\venv\Scripts\Activate
#flask run --debug
def get_db_connection():
    """Establece conexión con la base de datos."""
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='MechanicOrganizationalSystem'
    )

def connect_hana(server='172.16.31.16', puerto=30015, usuario='ADMIN_FLOTA', clave ='Montasa2024') -> hana.Connection:
    """
    Función que se encarga de realizar la conexión con la base de datos en HANA.
    Recibe como parámetro la dirección IP, puerto, usuario y clave del servidor.

    Utiliza la librería hdbcli, módulo dbapi.
    """
    try:
        connection = hana.connect(address=server, port=puerto, user=usuario, password=clave)
        print("Conexión exitosa a HANA DB.")
        return connection
    except hana.Error as e:
        print(f"Error al conectar a HANA DB: {e}")
connection = connect_hana()

    
@app.route('/')
def home():
    return render_template('home.html')






@app.route('/assign_supply/<int:order_id>', methods=['POST'])
def assign_supply(order_id):
    supply_code = request.form.get('supply_code')  # Usar el código del suministro como identificador
    quantity = request.form.get('quantity')
    default_status = "Esperando"

    if not supply_code or not quantity:
        flash('No supply or quantity selected!', 'error')
        return redirect(url_for('work_order_detail', order_id=order_id))

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Obtener los detalles del suministro y el SupplyID de la base de datos local
        cursor.execute('''
            SELECT SupplyID, Description
            FROM Supplies
            WHERE CodigoSap = %s
        ''', (supply_code,))
        supply_details = cursor.fetchone()

        if supply_details:
            supply_id, description = supply_details  # Desempaqueta el SupplyID y la descripción

            # Insertar el suministro en WorkOrderSupplies usando los detalles obtenidos de la base de datos local
            cursor.execute('''
                INSERT INTO WorkOrderSupplies (OrderID, SupplyID, CodigoSap, Description, Quantity, Status)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (order_id, supply_id, supply_code, description, quantity, default_status))
            conn.commit()
            flash('Supply assigned successfully!', 'success')
        else:
            flash('Supply details not found!', 'error')

    except Exception as err:
        print("Error: ", err)
        flash('Failed to assign supply!', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('work_order_detail', order_id=order_id))









@app.route('/unassign_supply/<int:order_id>/<supply_code>', methods=['POST'])
def unassign_supply(order_id, supply_code):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Asegúrate de que 'CodigoSap' es el nombre correcto de la columna en tu tabla 'WorkOrderSupplies'
        cursor.execute('DELETE FROM WorkOrderSupplies WHERE OrderID = %s AND CodigoSap = %s', (order_id, supply_code))
        conn.commit()
        flash('Supply unassigned successfully!', 'success')
    except Exception as err:
        print("Error: ", err)
        flash('Failed to unassign supply!', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('work_order_detail', order_id=order_id))



def refresh_supplies_from_sap():
    # Conectar a SAP HANA
    hana_conn = connect_hana()
    if hana_conn:
        try:
            hana_cursor = hana_conn.cursor()
            # Ejecutar la consulta en SAP HANA
            hana_cursor.execute('''
                SELECT "ItemCode" AS "CodigoSap", "ItemName" AS "Name", 
                       "ItemName" AS "Description", "OnHand" AS "QuantityInStock"
                FROM SBO_MONTASAHN.OITM
                WHERE "WhsCode" = '04' AND "validFor" = 'Y'
            ''')
            supplies_from_sap = hana_cursor.fetchall()
            
            # Conectar a la base de datos local (SQL)
            local_conn = get_db_connection()
            local_cursor = local_conn.cursor()
            
            for sap_supply in supplies_from_sap:
                codigo_sap, name, description, quantity_in_stock = sap_supply
                
                # Verificar si el suministro ya existe en la base de datos local
                local_cursor.execute('SELECT * FROM Supplies WHERE CodigoSap = %s', (codigo_sap,))
                existing_supply = local_cursor.fetchone()
                
                if existing_supply:
                    # Actualizar el suministro si ya existe
                    local_cursor.execute('''
                        UPDATE Supplies
                        SET Name = %s, Description = %s, QuantityInStock = %s
                        WHERE CodigoSap = %s
                    ''', (name, description, quantity_in_stock, codigo_sap))
                else:
                    # Insertar el nuevo suministro si no existe
                    local_cursor.execute('''
                        INSERT INTO Supplies (CodigoSap, Name, Description, QuantityInStock)
                        VALUES (%s, %s, %s, %s)
                    ''', (codigo_sap, name, description, quantity_in_stock))
                
            # Confirmar los cambios en la base de datos local
            local_conn.commit()
        except hana.Error as e:
            print(f"Error al obtener suministros de SAP HANA: {e}")
        finally:
            hana_cursor.close()
            hana_conn.close()
            local_cursor.close()
            local_conn.close()





#assign supply hacia sap





#supply status update

@app.route('/supply_status_update/<company>', methods=['GET', 'POST'])
def supply_status_update(company):
    app.logger.debug("Entered supply_status_update route")
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        app.logger.debug(f"POST request data: {request.form}")

        if 'new_status' in request.form:
            order_id = request.form['order_id']
            supply_id = request.form['supply_id']
            new_status = request.form['new_status']

            app.logger.debug(f"Updating supply status for order {order_id}, supply {supply_id} to {new_status}")
            cursor.execute('''
                UPDATE WorkOrderSupplies 
                SET Status = %s 
                WHERE OrderID = %s AND SupplyID = %s
            ''', (new_status, order_id, supply_id))
            conn.commit()

        if 'mechanic_pin' in request.form:
            mechanic_pin = request.form['mechanic_pin']
            checked_supplies = request.form.getlist('supply_ids[]')
            app.logger.debug(f"Mechanic PIN submitted: {mechanic_pin}, supplies: {checked_supplies}")

            cursor.execute('SELECT MechanicID FROM Mechanics WHERE PinCode = %s', (mechanic_pin,))
            mechanic = cursor.fetchone()

            if mechanic:
                mechanic_id = mechanic[0]
                for supply_id in checked_supplies:
                    app.logger.debug(f"Marking supply {supply_id} as received by mechanic {mechanic_id}")
                    cursor.execute('''
                        UPDATE WorkOrderSupplies 
                        SET Status = 'Recibido', ReceivedByMechanicID = %s 
                        WHERE SupplyID = %s
                    ''', (mechanic_id, supply_id))
                conn.commit()
                flash('Supplies marked as received.', 'success')
            else:
                flash('Invalid mechanic PIN.', 'error')

        # No need to close cursor and connection here if you're going to use them in the same request context below

    # Process GET request for initial page load or after redirect
    search_order_id = request.args.get('search_order_id', '')
    search_name = request.args.get('search_name', '')
    app.logger.debug(f"GET request: search_order_id={search_order_id}, search_name={search_name}")

    # Modified query to include CodigoSap
    cursor.execute('''
        SELECT ws.OrderID, ws.SupplyID, s.CodigoSap, s.Description, ws.Quantity, ws.Status, ws.ReceivedByMechanicID, m.Name as MechanicName
        FROM WorkOrderSupplies ws
        JOIN Supplies s ON ws.SupplyID = s.SupplyID
        LEFT JOIN Mechanics m ON ws.ReceivedByMechanicID = m.MechanicID
        WHERE (%s = '' OR ws.OrderID LIKE %s)
        AND (%s = '' OR s.Description LIKE %s)
        ORDER BY CASE WHEN ws.Status = 'Listo' THEN 0 WHEN ws.Status = 'Esperando' THEN 1 ELSE 2 END, ws.OrderID
    ''', (search_order_id, f'%{search_order_id}%', search_name, f'%{search_name}%'))

    supplies = cursor.fetchall()
    app.logger.debug(f"Supplies fetched: {supplies}")

    cursor.close()
    conn.close()

    return render_template('supply_status_update.html', supplies=supplies, company=company)




#supply status update


#mechanic work hours summary

def get_week_range(date):
    # Convert to a datetime object if the input is a string
    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d").date()

    # Find the most recent Monday
    week_start = date - timedelta(days=date.weekday())

    # Find the following Sunday
    week_end = week_start + timedelta(days=6)

    return week_start, week_end

def update_mechanic_work_hour_summary(mechanic_id, date):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Calculate work hours for the day as TIME
        cursor.execute('''
            SELECT SEC_TO_TIME(SUM(TIME_TO_SEC(TIMEDIFF(EndTime, StartTime))))
            FROM TimeTracking
            WHERE MechanicID = %s AND DATE(StartTime) = %s
        ''', (mechanic_id, date))
        daily_duration = cursor.fetchone()[0] or '00:00:00'

        # Update or insert into DailyMechanicWorkHours
        cursor.execute('''
            INSERT INTO DailyMechanicWorkHours (MechanicID, Date, TotalHours)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE TotalHours = VALUES(TotalHours)
        ''', (mechanic_id, date, daily_duration))

        # Calculate work hours for the week
        week_start, week_end = get_week_range(date)
        cursor.execute('''
            SELECT SEC_TO_TIME(SUM(TIME_TO_SEC(TIMEDIFF(EndTime, StartTime))))
            FROM TimeTracking
            WHERE MechanicID = %s AND DATE(StartTime) BETWEEN %s AND %s
        ''', (mechanic_id, week_start, week_end))
        weekly_duration = cursor.fetchone()[0] or '00:00:00'

        # Update or insert into WeeklyMechanicWorkHours
        cursor.execute('''
            INSERT INTO WeeklyMechanicWorkHours (MechanicID, WeekStartDate, TotalHours)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE TotalHours = VALUES(TotalHours)
        ''', (mechanic_id, week_start, weekly_duration))

        # Similarly, calculate work hours for the month and update MonthlyMechanicWorkHours
        month_start = date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        cursor.execute('''
            SELECT SEC_TO_TIME(SUM(TIME_TO_SEC(TIMEDIFF(EndTime, StartTime))))
            FROM TimeTracking
            WHERE MechanicID = %s AND DATE(StartTime) BETWEEN %s AND %s
        ''', (mechanic_id, month_start, month_end))
        monthly_duration = cursor.fetchone()[0] or '00:00:00'

        month_str = date.strftime('%Y-%m')  # Format as 'YYYY-MM'
        cursor.execute('''
            INSERT INTO MonthlyMechanicWorkHours (MechanicID, Month, TotalHours)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE TotalHours = VALUES(TotalHours)
        ''', (mechanic_id, month_str, monthly_duration))

        conn.commit()
    except mysql.connector.Error as err:
        print("SQL Error: ", err)
    finally:
        cursor.close()
        conn.close()


@app.route('/mechanic_work_hours_summary/<company>', methods=['GET', 'POST'])
def mechanic_work_hours_summary(company):
    filter_date_str = request.args.get('filter_date', datetime.now().strftime('%Y-%m-%d'))
    filter_date = datetime.strptime(filter_date_str, '%Y-%m-%d')

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Fetch data for daily summary
        cursor.execute("SELECT * FROM DailyMechanicWorkHours WHERE Date = %s", (filter_date_str,))
        daily_summary = cursor.fetchall()

        # Calculate week range
        week_start, week_end = get_week_range(filter_date_str)
        cursor.execute("SELECT * FROM WeeklyMechanicWorkHours WHERE WeekStartDate = %s", (week_start,))
        weekly_summary = cursor.fetchall()

        # Fetch data for monthly summary
        month_str = filter_date.strftime("%Y-%m")  # Format month and year as "YYYY-MM"
        cursor.execute("SELECT * FROM MonthlyMechanicWorkHours WHERE Month = %s", (month_str,))
        monthly_summary = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template('mechanic_work_hours_summary.html', daily_summary=daily_summary, weekly_summary=weekly_summary, monthly_summary=monthly_summary, filter_date=filter_date_str,company=company)

#mechanic work hours summary


#unassign mechanic


@app.route('/unassign_mechanic', methods=['POST'])
def unassign_mechanic():
    order_id = request.form['order_id']
    mechanic_id = request.form['mechanic_id']
    end_time = datetime.now()

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Update TimeTracking to set the end time for this mechanic
        cursor.execute('UPDATE TimeTracking SET EndTime = %s WHERE OrderID = %s AND MechanicID = %s AND EndTime IS NULL', (end_time, order_id, mechanic_id))
        
        # Remove mechanic assignment from MechanicWorkOrder
        cursor.execute('DELETE FROM MechanicWorkOrder WHERE OrderID = %s AND MechanicID = %s', (order_id, mechanic_id))

        # Commit changes and update mechanic work hour summary
        conn.commit()
        update_mechanic_work_hour_summary(mechanic_id, end_time.date())
    except mysql.connector.Error as err:
        print("SQL Error: ", err)
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('work_order_detail', order_id=order_id))



@app.route('/assign_mechanic', methods=['POST'])
def assign_mechanic():
    order_id = request.form['order_id']
    mechanic_id = request.form['mechanic_id']
    start_time = datetime.now()

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get VehicleID from the WorkOrders table
        cursor.execute('SELECT VehicleID FROM WorkOrders WHERE OrderID = %s', (order_id,))
        vehicle_id = cursor.fetchone()[0]

        # Update or insert assignment in MechanicWorkOrder
        cursor.execute('REPLACE INTO MechanicWorkOrder (OrderID, MechanicID) VALUES (%s, %s)', (order_id, mechanic_id))

        # Insert into TimeTracking table with VehicleID
        cursor.execute('INSERT INTO TimeTracking (OrderID, MechanicID, StartTime, VehicleID) VALUES (%s, %s, %s, %s)', (order_id, mechanic_id, start_time, vehicle_id))

        # Commit changes and update mechanic work hour summary
        conn.commit()
        update_mechanic_work_hour_summary(mechanic_id, start_time.date())
    except mysql.connector.Error as err:
        print("SQL Error: ", err)
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('work_order_detail', order_id=order_id))

#assign mechanic



@app.route('/vehicles')
def vehicles_list():
    company = request.args.get('company', 'MontasaHN')  # Default to MontasaHN if no company is specified
    vehicle_id = request.args.get('vehicle_id')
    availability = request.args.get('availability')
    conn = get_db_connection()
    cursor = conn.cursor()

    # Seleccionar la tabla según la empresa
    if company == 'MontasaHN':
        table_name = 'Vehicles'
    elif company == 'MontasaCR':
        table_name = 'VehiculosCR'
    elif company == 'Monhaco':
        table_name = 'VehiculosMonhaco'
    else:
        table_name = 'Vehicles'  # Default table if no valid company is specified

    query = f"SELECT * FROM {table_name}"
    conditions = []
    parameters = []

    if vehicle_id:
        conditions.append("VehicleID = %s")
        parameters.append(vehicle_id)
    if availability:
        conditions.append("Status = %s")
        parameters.append(availability)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # Añadir la cláusula ORDER BY para ordenar los vehículos por HorometroDesdeUltimoMantenimiento de mayor a menor
    query += " ORDER BY HorometroDesdeUltimoMantenimiento DESC"

    cursor.execute(query, tuple(parameters))
    vehicles = cursor.fetchall()

    # Consultas para contar los vehículos por estado, ajustadas a la tabla específica de la empresa
    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE Status = 'Disponible'")
    disponible_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE Status = 'En Renta'")
    en_renta_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE Status = 'En Taller'")
    en_taller_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE Status = 'Reparación Externa'")
    reparacion_externa_count = cursor.fetchone()[0]

    total_vehicles = disponible_count + en_renta_count + en_taller_count + reparacion_externa_count
    disponible_percentage = (disponible_count / total_vehicles) * 100 if total_vehicles > 0 else 0
    en_renta_percentage = (en_renta_count / total_vehicles) * 100 if total_vehicles > 0 else 0
    en_taller_percentage = (en_taller_count / total_vehicles) * 100 if total_vehicles > 0 else 0
    reparacion_externa_percentage = (reparacion_externa_count / total_vehicles) * 100 if total_vehicles > 0 else 0
    
    cursor.close()
    conn.close()

    # Pasar también la empresa seleccionada a la plantilla para mostrarla en la interfaz
    return render_template('vehicles.html', company=company, vehicles=vehicles, disponible_count=disponible_count, en_renta_count=en_renta_count, en_taller_count=en_taller_count, disponible_percentage=disponible_percentage, en_renta_percentage=en_renta_percentage, en_taller_percentage=en_taller_percentage, reparacion_externa_count=reparacion_externa_count, reparacion_externa_percentage=reparacion_externa_percentage)


    


#Ordenes de SERVICIO Principio

@app.route('/add_work_order/<company>', methods=['GET', 'POST'])
def add_work_order(company):
    conn = get_db_connection()
    cursor = conn.cursor()

    vehicle_table_map = {
        'MontasaHN': 'Vehicles',
        'MontasaCR': 'vehiculosCR',
        'Monhaco': 'vehiculosMonhaco'
    }

    # Obtén la tabla de vehículos correcta según la compañía, usa 'Vehicles' como predeterminado
    vehicle_table = vehicle_table_map.get(company, 'Vehicles')

    # Construye y ejecuta la consulta SQL utilizando la tabla de vehículos correcta
    sql_query = '''
        SELECT VehicleID, VehicleName FROM {} 
        WHERE Status IN ("Disponible", "En Renta") OR VehicleName = "Generico"
    '''.format(vehicle_table)  # Usa format para insertar el nombre de la tabla

    cursor.execute(sql_query)
    vehicles = cursor.fetchall()


    if request.method == 'POST':
        # Extrae los valores del formulario
        vehicle_id = request.form['vehicle_id']
        work_type = request.form.get('work_type')
        lugar = request.form['lugar']
        dueno = request.form['dueno']
        marca = request.form['marca']
        description = request.form['description']

        # Check if the vehicle is generic
        cursor.execute('SELECT VehicleName FROM Vehicles WHERE VehicleID = %s', (vehicle_id,))
        vehicle_name = cursor.fetchone()[0]

        # Allow multiple work orders for a generic vehicle
        if vehicle_name != "Generico":
            cursor.execute('SELECT * FROM WorkOrders WHERE VehicleID = %s AND Status != "Completed"', (vehicle_id,))
            existing_order = cursor.fetchone()

            if existing_order:
                message = "There is already an open work order for this vehicle."
                cursor.close()
                flash(message)
                return redirect(url_for('work_orders'))

        # Determine the status based on the work_type
        work_order_status = "Maintenance" if work_type == 'Maintenance' else "Repair"

        # Insert the new work order
        cursor.execute('''
        INSERT INTO WorkOrders (VehicleID, WorkType, Description, Status, Lugar, Dueno, Marca, Empresa)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (vehicle_id, work_type, description, work_order_status, lugar, dueno, marca, company))
        conn.commit()
        new_order_id = cursor.lastrowid  # Get the ID of the newly created work order

        # Create mechanic and logistics quality checks for the new work order
        create_mechanic_quality_check(conn, new_order_id)
        create_logistics_quality_check(conn, new_order_id)

        # Update the vehicle's status based on the current status and work type

        cursor.execute('SELECT Status FROM Vehicles WHERE VehicleID = %s', (vehicle_id,))
        current_status = cursor.fetchone()[0]
        vehicle_status = "En Taller" if current_status == "Disponible" else "Reparación Externa"

        cursor.execute('''
        UPDATE Vehicles SET Status = %s WHERE VehicleID = %s
        ''', (vehicle_status, vehicle_id))
        conn.commit()
        cursor.close()
        flash('Work order added successfully.')
        return redirect(url_for('work_orders', company=company))

    cursor.close()
    return render_template('add_work_order.html', vehicles=vehicles, company=company)



# Add work order


#work orders

  
 
@app.route('/work_orders/<company>')  # Añade el parámetro 'company' a la ruta
def work_orders(company):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Filtra las órdenes de trabajo activas por empresa
    cursor.execute('''
        SELECT DISTINCT wo.OrderID
        FROM WorkOrders wo
        WHERE wo.Status != 'Completed' AND wo.Empresa = %s
        ORDER BY wo.OrderID
    ''', (company,))  # Añade el parámetro 'company' a la consulta
    active_order_ids = cursor.fetchall()

    # Filtra los nombres de vehículos activos por empresa
    cursor.execute('''
        SELECT DISTINCT v.VehicleName
        FROM WorkOrders wo
        JOIN Vehicles v ON wo.VehicleID = v.VehicleID
        WHERE wo.Status != 'Completed' AND wo.Empresa = %s
        ORDER BY v.VehicleName
    ''', (company,))  # Añade el parámetro 'company' a la consulta
    active_vehicle_names = cursor.fetchall()


    # Retrieve all search terms and date range
    order_id_query = request.args.get('order_id', '')
    vehicle_name_query = request.args.get('vehicle_name', '')
    description_query = request.args.get('description', '')
    start_date = request.args.get('start_date', '2024-01-01')
    now = datetime.now()
    end_date = (now + timedelta(days=1)).strftime('%Y-%m-%d')
    end_date = request.args.get('end_date', end_date)

    # Constructing the SQL query based on search parameters
    query_conditions = ["wo.Status != 'Completed'"]
    query_params = []

    if order_id_query:
        query_conditions.append("wo.OrderID LIKE %s")
        query_params.append(f'%{order_id_query}%')

    if vehicle_name_query:
        query_conditions.append("v.VehicleName LIKE %s")
        query_params.append(f'%{vehicle_name_query}%')

    if description_query:
        query_conditions.append("wo.Description LIKE %s")
        query_params.append(f'%{description_query}%')

    query_conditions.append("wo.CreatedTime BETWEEN %s AND %s")
    query_params.extend([start_date, end_date])

    query_conditions.append("wo.Empresa = %s")
    query_params.append(company)

    where_clause = " AND ".join(query_conditions)
    sql_query = f'''
        SELECT wo.OrderID, wo.VehicleID, wo.WorkType, wo.Description, v.VehicleName, wo.CreatedTime
        FROM WorkOrders wo
        JOIN Vehicles v ON wo.VehicleID = v.VehicleID
        WHERE {where_clause}
        ORDER BY wo.OrderID DESC
    '''
    cursor.execute(sql_query, tuple(query_params))
    work_orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('work_orders.html', work_orders=work_orders, active_order_ids=active_order_ids, active_vehicle_names=active_vehicle_names, order_id_query=order_id_query, vehicle_name_query=vehicle_name_query, description_query=description_query, start_date=start_date, end_date=end_date, company=company)





#work orders







@app.route('/work_order_detail/<int:order_id>', methods=['GET'])
def work_order_detail(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the main details of the work order
    cursor.execute('''
        SELECT wo.OrderID, wo.VehicleID, v.VehicleName, wo.WorkType, wo.Description, wo.Status, 
            wo.Lugar, wo.Dueno, wo.Marca, wo.Diagnostico, wo.TrabajoRealizado, wo.CreatedTime, wo.Empresa
        FROM WorkOrders wo
        JOIN Vehicles v ON wo.VehicleID = v.VehicleID
        WHERE wo.OrderID = %s
    ''', (order_id,))
    order = cursor.fetchone()

    if order:
        company = order[12]

        # Fetch all mechanics for assignment
        cursor.execute('SELECT MechanicID, Name FROM Mechanics')
        all_mechanics = cursor.fetchall()

        # Fetch mechanics assigned to this work order
        cursor.execute('''
            SELECT m.MechanicID, m.Name 
            FROM Mechanics m 
            JOIN MechanicWorkOrder mwo ON m.MechanicID = mwo.MechanicID 
            WHERE mwo.OrderID = %s
        ''', (order_id,))
        mechanics = cursor.fetchall()

        # Fetch assigned and available supplies
        cursor.execute('SELECT CodigoSap, Description, Quantity, Status FROM WorkOrderSupplies WHERE OrderID = %s', (order_id,))
        assigned_supplies = cursor.fetchall()
        cursor.execute('SELECT CodigoSap, Description FROM Supplies')
        available_supplies = cursor.fetchall()

        cursor.close()
        conn.close()

        order_dict = {
            'order_id': order[0],
            'vehicle_id': order[1],
            'vehicle_name': order[2],
            'work_type': order[3],
            'description': order[4],
            'status': order[5],
            'Lugar': order[6],
            'Dueno': order[7],
            'Marca': order[8],
            'diagnostico': order[9],
            'trabajoRealizado': order[10],
            'created_time': order[11],
        }

        return render_template('work_order_detail.html', order=order_dict, company=company, available_supplies=available_supplies, assigned_supplies=assigned_supplies, mechanics=mechanics, all_mechanics=all_mechanics)
    else:
        cursor.close()
        conn.close()
        return 'Work Order not found', 404




#work order detail 

#update work orders
@app.route('/update_work_order/<int:order_id>', methods=['POST'])
def update_work_order(order_id):
    diagnostico = request.form.get('diagnostico')
    trabajoRealizado = request.form.get('trabajoRealizado')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Update the work order with the new values
        update_query = '''
            UPDATE WorkOrders
            SET Diagnostico = %s, TrabajoRealizado = %s
            WHERE OrderID = %s
        '''
        cursor.execute(update_query, (diagnostico, trabajoRealizado, order_id))
        conn.commit()
        flash('Work order updated successfully.', 'success')
    except mysql.connector.Error as err:
        flash(f'Error updating work order: {err.msg}', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('work_orders'))

#update work orders

#work order Records

@app.route('/work_orders_record/<company>', methods=['GET'])
def work_orders_record(company):
    order_id_query = request.args.get('order_id', '')
    description_query = request.args.get('description', '')
    vehicle_name_query = request.args.get('vehicle_name', '')
    start_date_query = request.args.get('start_date', '')
    end_date_query = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtén los IDs de orden y nombres de vehículos para opciones de filtro, filtrando por empresa
    cursor.execute('''
        SELECT DISTINCT OrderID 
        FROM WorkOrders 
        WHERE Status = "Completed" AND Empresa = %s 
        ORDER BY OrderID DESC
    ''', (company,))
    order_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute('''
        SELECT DISTINCT VehicleName 
        FROM Vehicles 
        WHERE Empresa = %s 
        ORDER BY VehicleName
    ''', (company,))
    vehicle_names = [row[0] for row in cursor.fetchall()]

    # Construye la consulta SQL basada en parámetros de búsqueda, filtrando por empresa
    query_conditions = ["wo.Status = 'Completed'", "wo.Empresa = %s"]
    query_params = [company]

    if order_id_query:
        query_conditions.append("wo.OrderID = %s")
        query_params.append(order_id_query)

    if description_query:
        query_conditions.append("wo.Description LIKE %s")
        query_params.append(f"%{description_query}%")

    if vehicle_name_query:
        query_conditions.append("v.VehicleName = %s")
        query_params.append(vehicle_name_query)

    if start_date_query and end_date_query:
        query_conditions.append("wo.FinishedTime BETWEEN %s AND %s")
        query_params.extend([start_date_query, end_date_query + " 23:59:59"])

    where_clause = " AND ".join(query_conditions)
    sql_query = f'''
        SELECT wo.OrderID, wo.VehicleID, v.VehicleName, wo.WorkType, wo.Description, wo.CreatedTime, wo.FinishedTime
        FROM WorkOrders wo
        JOIN Vehicles v ON wo.VehicleID = v.VehicleID
        WHERE {where_clause}
        ORDER BY wo.OrderID DESC
    '''
    cursor.execute(sql_query, tuple(query_params))
    work_orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('work_orders_record.html', work_orders=work_orders, order_ids=order_ids, vehicle_names=vehicle_names, selected_order_id=order_id_query, selected_vehicle_name=vehicle_name_query, selected_description=description_query, company=company)

#work order Records

#work order record detail

@app.route('/work_order_record_detail/<company>/<int:order_id>')
def work_order_record_detail(company,order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the details of the completed work order
    cursor.execute('''
        SELECT wo.OrderID, wo.VehicleID, v.VehicleName, wo.WorkType, wo.Description, wo.CreatedTime, wo.FinishedTime, wo.Lugar, wo.Dueno, wo.Marca, wo.Diagnostico, wo.TrabajoRealizado
        FROM WorkOrders wo
        JOIN Vehicles v ON wo.VehicleID = v.VehicleID
        WHERE wo.OrderID = %s AND wo.Status = 'Completed' AND wo.Empresa = %s
    ''', (order_id, company))
    order = cursor.fetchone()

    # Fetch all mechanics and supplies assigned to this work order
    cursor.execute('''
        SELECT m.MechanicID, m.Name
        FROM Mechanics m
        JOIN MechanicWorkOrder mwo ON m.MechanicID = mwo.MechanicID
        WHERE mwo.OrderID = %s
    ''', (order_id,))
    mechanics = cursor.fetchall()

    cursor.execute('''
        SELECT s.SupplyID, s.Name, ws.Quantity
        FROM Supplies s
        JOIN WorkOrderSupplies ws ON s.SupplyID = ws.SupplyID
        WHERE ws.OrderID = %s
    ''', (order_id,))
    supplies = cursor.fetchall()

    cursor.close()
    conn.close()

    if order:
        # Convert the order tuple to a dictionary for easier access in the template
        order_dict = {
            'order_id': order[0],
            'vehicle_id': order[1],
            'vehicle_name': order[2],
            'work_type': order[3],
            'description': order[4],
            'start_date': order[5],
            'end_date': order[6],
            'Lugar': order[7],
            'Dueno': order[8],
            'Marca': order[9],
            'mechanics': mechanics,
            'supplies': supplies
        }
        return render_template('work_order_record_detail.html', order=order_dict,company=company)
    else:
        return 'Work Order not found', 404


#work order record detail





#mechanic quality check

@app.route('/create_mechanic_quality_check/<int:work_order_id>', methods=['GET'])
def create_mechanic_quality_check(conn, work_order_id):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO MechanicQualityChecks (WorkOrderID)
        VALUES (%s)
    ''', (work_order_id,))
    conn.commit()
    cursor.close()


@app.route('/mechanic_quality_check/<int:order_id>')
def mechanic_quality_check(order_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch checklist and mechanic's name based on WorkOrderID
    cursor.execute('''
        SELECT mq.*, m.Name AS MechanicName
        FROM MechanicQualityChecks mq
        LEFT JOIN Mechanics m ON mq.MechanicID = m.MechanicID
        WHERE mq.WorkOrderID = %s
    ''', (order_id,))
    checklist = cursor.fetchone()

    cursor.close()
    conn.close()

    if checklist:
        return render_template('mechanic_quality_check.html', checklist=checklist, order_id=order_id)
    else:
        flash('No checklist found for this work order.', 'error')
        return redirect(url_for('work_order_detail',order_id=order_id))



@app.route('/update_mechanic_quality_checklist/<int:order_id>', methods=['POST'])
def update_mechanic_quality_checklist(order_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        mechanic_id = request.form.get('MechanicID') 
        # Prepare the update query
        update_query = '''
            UPDATE MechanicQualityChecks
            SET 
                MechanicID = %s,
                CambioDeAceiteHidraulico = %s,
                CambioDeFiltroHidraulico = %s,
                LimpiezaDeFiltroDeMalla = %s,
                CambioDeEmpaqueDeTapadera = %s,
                RevisarYPruebaDeSistemaHidraulico = %s,
                RevisionGeneralDeManguerasHidraulicas = %s,
                CambioAceiteMotor = %s,
                CambioFiltroMotor = %s,
                CambioFiltroAire = %s,
                CambioFiltroCombustible = %s,
                RevisionCambioBandaMotor = %s,
                CambioRefrigeranteRadiador = %s,
                CambioTapaderaDistribuidorRotor = %s,
                CambioCandelas = %s,
                CambioCableCandela = %s,
                RevisionSoporteMotor = %s,
                RevisionInyectores = %s,
                RevisionTiempoMotor = %s,
                RevisionTermostato = %s,
                RevisionMultipleAdmision = %s,
                RevisionTornillosManifold = %s,
                RevisionRPM = %s,
                RevisionCargaAlternador = %s,
                CambioAceiteTransmision = %s,
                CambioFiltroTransmision = %s,
                CambioAceiteDiferencial = %s,
                RevisionCambioManguera = %s,
                RevisionFugas = %s,
                RevisionBombasFreno = %s,
                RevisionFricciones = %s,
                RevisionBalinerasRetenedores = %s,
                RevisionEjeDireccion = %s,
                AjustesPedalesFreno = %s,
                RevisarLubricarEjesDelanteros = %s,
                RevisionTambor = %s,
                RevisarFuncionamientoIndicadores = %s,
                RevisarMotorArranque = %s,
                RevisarArnesEquipo = %s,
                RevisarSistemaCarga = %s,
                SocarTerminalBateria = %s,
                RevisionAmpBateria = %s,
                RevisionTaponColadorPolvo = %s,
                RevisionSistemaLucesDelanteras = %s,
                RevisionSistemaLucesTraseras = %s,
                LucesStop = %s,
                ViasDireccionales = %s,
                LucesRetroceso = %s,
                AlarmaRetroceso = %s,
                LuzEstroboscopico = %s,
                Claxon = %s,
                CinturonSeguridad = %s,
                Retrovisores = %s,
                Extintor = %s,
                RevisarTensionCadena = %s,
                RevisarAjustesEmergencias = %s,
                LavadoGeneral = %s,
                LubricacionEngraseTorreCadena = %s,
                CalibracionValvulaMotor = %s,
                AdditionalNotes = %s
            WHERE WorkOrderID = %s
        '''

        # Get values from the form submission
        values = (
            mechanic_id,
            request.form.get('CambioDeAceiteHidraulico') == 'on',
            request.form.get('CambioDeFiltroHidraulico') == 'on',
            request.form.get('LimpiezaDeFiltroDeMalla') == 'on',
            request.form.get('CambioDeEmpaqueDeTapadera') == 'on',
            request.form.get('RevisarYPruebaDeSistemaHidraulico') == 'on',
            request.form.get('RevisionGeneralDeManguerasHidraulicas') == 'on',
            request.form.get('CambioAceiteMotor') == 'on',
            request.form.get('CambioFiltroMotor') == 'on',
            request.form.get('CambioFiltroAire') == 'on',
            request.form.get('CambioFiltroCombustible') == 'on',
            request.form.get('RevisionCambioBandaMotor') == 'on',
            request.form.get('CambioRefrigeranteRadiador') == 'on',
            request.form.get('CambioTapaderaDistribuidorRotor') == 'on',
            request.form.get('CambioCandelas') == 'on',
            request.form.get('CambioCableCandela') == 'on',
            request.form.get('RevisionSoporteMotor') == 'on',
            request.form.get('RevisionInyectores') == 'on',
            request.form.get('RevisionTiempoMotor') == 'on',
            request.form.get('RevisionTermostato') == 'on',
            request.form.get('RevisionMultipleAdmision') == 'on',
            request.form.get('RevisionTornillosManifold') == 'on',
            request.form.get('RevisionRPM') == 'on',
            request.form.get('RevisionCargaAlternador') == 'on',
            request.form.get('CambioAceiteTransmision') == 'on',
            request.form.get('CambioFiltroTransmision') == 'on',
            request.form.get('CambioAceiteDiferencial') == 'on',
            request.form.get('RevisionCambioManguera') == 'on',
            request.form.get('RevisionFugas') == 'on',
            request.form.get('RevisionBombasFreno') == 'on',
            request.form.get('RevisionFricciones') == 'on',
            request.form.get('RevisionBalinerasRetenedores') == 'on',
            request.form.get('RevisionEjeDireccion') == 'on',
            request.form.get('AjustesPedalesFreno') == 'on',
            request.form.get('RevisarLubricarEjesDelanteros') == 'on',
            request.form.get('RevisionTambor') == 'on',
            request.form.get('RevisarFuncionamientoIndicadores') == 'on',
            request.form.get('RevisarMotorArranque') == 'on',
            request.form.get('RevisarArnesEquipo') == 'on',
            request.form.get('RevisarSistemaCarga') == 'on',
            request.form.get('SocarTerminalBateria') == 'on',
            request.form.get('RevisionAmpBateria') == 'on',
            request.form.get('RevisionTaponColadorPolvo') == 'on',
            request.form.get('RevisionSistemaLucesDelanteras') == 'on',
            request.form.get('RevisionSistemaLucesTraseras') == 'on',
            request.form.get('LucesStop') == 'on',
            request.form.get('ViasDireccionales') == 'on',
            request.form.get('LucesRetroceso') == 'on',
            request.form.get('AlarmaRetroceso') == 'on',
            request.form.get('LuzEstroboscopico') == 'on',
            request.form.get('Claxon') == 'on',
            request.form.get('CinturonSeguridad') == 'on',
            request.form.get('Retrovisores') == 'on',
            request.form.get('Extintor') == 'on',
            request.form.get('RevisarTensionCadena') == 'on',
            request.form.get('RevisarAjustesEmergencias') == 'on',
            request.form.get('LavadoGeneral') == 'on',
            request.form.get('LubricacionEngraseTorreCadena') == 'on',
            request.form.get('CalibracionValvulaMotor') == 'on',
            request.form.get('AdditionalNotes'),
            order_id
        )


        # Execute the update query
        cursor.execute(update_query, values)
        conn.commit()

        flash('Checklist updated successfully.', 'success')
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'Database error: {err}', 'error')
        print("SQL Error: ", err)
    finally:
        cursor.close()
        conn.close()

        # Redirect to the work orders page
    return redirect(url_for('work_order_detail',order_id=order_id))

#mechanic quality check

#logistics Quality check

def create_logistics_quality_check(conn, order_id):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO LogisticsQualityChecklist (OrderID)
        VALUES (%s)
    ''', (order_id,))
    conn.commit()
    cursor.close()

@app.route('/logistics_quality_check/<int:order_id>')
def logistics_quality_check(order_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch checklist based on OrderID
    cursor.execute('SELECT * FROM LogisticsQualityChecklist WHERE OrderID = %s', (order_id,))
    checklist = cursor.fetchone()

    cursor.close()
    conn.close()

    if checklist:
        return render_template('logistics_quality_check.html', checklist=checklist, order_id=order_id)
    else:
        flash('No checklist found for this work order.', 'error')
        return redirect(url_for('work_order_detail',order_id=order_id))

@app.route('/update_logistics_quality_checklist/<int:order_id>', methods=['POST'])
def update_logistics_quality_checklist(order_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        operator_id = request.form.get('IdOperador')
        # Prepare the update query with all the checklist items
        update_query = '''
            UPDATE LogisticsQualityChecklist
            SET 
                AlarmaDePrecaucion = %s,
                BotonDeEmergencia = %s,
                LuzEstroboscopica = %s,
                LucesDeTrabajo = %s,
                LucesDeStop = %s,
                LucesDeVias = %s,
                Baterias = %s,
                Pito = %s,
                TaponDeCombustible = %s,
                LubricacionYEngrase = %s,
                SistemaHidraulico = %s,
                BandasDeMotor = %s,
                FugasDeAceites = %s,
                TorreCompleta = %s,
                LavadoGeneral = %s,
                FrenosGeneral = %s,
                CilindroDeGas = %s,
                Mangueras = %s,
                Cuchillas = %s,
                Balineras = %s,
                Palancas = %s,
                Pistones = %s,
                Cadenas = %s,
                Shifter = %s,
                GolpesOAbolladuras = %s,
                IndicadoresTablero = %s,
                CamaraFrontal = %s,
                CamaraTrasera = %s,
                PantallaVisual = %s,
                PinturaGeneral = %s,
                Cinturones = %s,
                Asientos = %s,
                Extintor = %s,
                ExtensionesHorquilla = %s,
                LlavesDeEncendido = %s,
                KitAntiderrame = %s,
                Conos = %s,
                DelanteraIzquierda = %s,
                DelanteraDerecha = %s,
                TraseraIzquierda = %s,
                TraseraDerecha = %s,
                RefrigeranteCoolant = %s,
                LiquidoDeFrenos = %s,
                AceiteHidraulico = %s,
                AceiteMotor = %s,
                Combustible = %s,
                ConectoresDeCorriente = %s,
                CableDeEmergencia = %s,
                Cargador = %s,
                Botones = %s,
                Canasta = %s,
                Joystick = %s,
                Switch = %s,
                AdditionalNotes = %s
                IdOperador = %s
            WHERE OrderID = %s
        '''

        # Get values from the form submission
        values = (
            request.form.get('AlarmaDePrecaucion') == 'on',
            request.form.get('BotonDeEmergencia') == 'on',
            request.form.get('LuzEstroboscopica') == 'on',
            request.form.get('LucesDeTrabajo') == 'on',
            request.form.get('LucesDeStop') == 'on',
            request.form.get('LucesDeVias') == 'on',
            request.form.get('Baterias') == 'on',
            request.form.get('Pito') == 'on',
            request.form.get('TaponDeCombustible') == 'on',
            request.form.get('LubricacionYEngrase') == 'on',
            request.form.get('SistemaHidraulico') == 'on',
            request.form.get('BandasDeMotor') == 'on',
            request.form.get('FugasDeAceites') == 'on',
            request.form.get('TorreCompleta') == 'on',
            request.form.get('LavadoGeneral') == 'on',
            request.form.get('FrenosGeneral') == 'on',
            request.form.get('CilindroDeGas') == 'on',
            request.form.get('Mangueras') == 'on',
            request.form.get('Cuchillas') == 'on',
            request.form.get('Balineras') == 'on',
            request.form.get('Palancas') == 'on',
            request.form.get('Pistones') == 'on',
            request.form.get('Cadenas') == 'on',
            request.form.get('Shifter') == 'on',
            request.form.get('GolpesOAbolladuras') == 'on',
            request.form.get('IndicadoresTablero') == 'on',
            request.form.get('CamaraFrontal') == 'on',
            request.form.get('CamaraTrasera') == 'on',
            request.form.get('PantallaVisual') == 'on',
            request.form.get('PinturaGeneral') == 'on',
            request.form.get('Cinturones') == 'on',
            request.form.get('Asientos') == 'on',
            request.form.get('Extintor') == 'on',
            request.form.get('ExtensionesHorquilla') == 'on',
            request.form.get('LlavesDeEncendido') == 'on',
            request.form.get('KitAntiderrame') == 'on',
            request.form.get('Conos') == 'on',
            request.form.get('DelanteraIzquierda') == 'on',
            request.form.get('DelanteraDerecha') == 'on',
            request.form.get('TraseraIzquierda') == 'on',
            request.form.get('TraseraDerecha') == 'on',
            request.form.get('RefrigeranteCoolant') == 'on',
            request.form.get('LiquidoDeFrenos') == 'on',
            request.form.get('AceiteHidraulico') == 'on',
            request.form.get('AceiteMotor') == 'on',
            request.form.get('Combustible') == 'on',
            request.form.get('ConectoresDeCorriente') == 'on',
            request.form.get('CableDeEmergencia') == 'on',
            request.form.get('Cargador') == 'on',
            request.form.get('Botones') == 'on',
            request.form.get('Canasta') == 'on',
            request.form.get('Joystick') == 'on',
            request.form.get('Switch') == 'on',
            request.form.get('AdditionalNotes'),
            operator_id,
            order_id
        )


        # Execute the update query
        cursor.execute(update_query, values)
        conn.commit()

        flash('Logistics quality checklist updated successfully.', 'success')
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'Database error: {err}', 'error')
        print("SQL Error: ", err)
    finally:
        cursor.close()
        conn.close()

        # Redirect back to the checklist page or another page as needed
    return redirect(url_for('work_order_detail', order_id=order_id))


#logistics Quality check

# Complete Work Order
@app.route('/complete_work_order', methods=['POST'])
def complete_work_order():
    order_id = request.form['order_id']
    finished_time = datetime.now()  # Capture the current time as finished time

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Complete the work order and set the finished time
        cursor.execute('UPDATE WorkOrders SET Status = "Completed", FinishedTime = %s WHERE OrderID = %s', (finished_time, order_id))
        
        cursor.execute('SELECT Empresa FROM WorkOrders WHERE OrderID = %s', (order_id,))
        company = cursor.fetchone()[0] 

        # Fetch the vehicle associated with this work order
        cursor.execute('SELECT VehicleID FROM WorkOrders WHERE OrderID = %s', (order_id,))
        vehicle_id = cursor.fetchone()[0]

        # Get the current status of the vehicle
        cursor.execute('SELECT Status FROM Vehicles WHERE VehicleID = %s', (vehicle_id,))
        current_status = cursor.fetchone()[0]

        # Update vehicle status based on the current status
        if current_status == 'En Taller':
            new_status = 'Disponible'
        elif current_status == 'Reparación Externa':
            new_status = 'En Renta'
        else:
            new_status = current_status  # Keep the current status if it doesn't match the specified conditions

        cursor.execute('UPDATE Vehicles SET Status = %s WHERE VehicleID = %s', (new_status, vehicle_id))

        conn.commit()
    except mysql.connector.Error as err:
        print(f"SQL Error: {err}")
        conn.rollback()  # Roll back in case of error
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('work_orders',company=company))




#complete work order

#start Supply wait

@app.route('/start_supply_wait/<int:order_id>', methods=['POST'])
def start_supply_wait(order_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Check if there's an ongoing supply wait for this order
        cursor.execute('SELECT * FROM SupplyWaitTimes WHERE OrderID = %s AND EndTime IS NULL', (order_id,))
        active_wait = cursor.fetchone()

        if not active_wait:
            # No active wait, start a new wait period
            cursor.execute('INSERT INTO SupplyWaitTimes (OrderID, StartTime) VALUES (%s, NOW())', (order_id,))
            cursor.execute('UPDATE WorkOrders SET Status = %s WHERE OrderID = %s', ('SupplyWait', order_id))
            conn.commit()
            flash('Supply wait time started.', 'success')  # Using flash for messaging
        else:
            # An active wait exists
            flash('Supply wait time is already active.', 'info')  # Using flash for messaging

    except mysql.connector.Error as err:
        print("SQL Error: ", err)
        flash('Error starting supply wait time.', 'error')  # Using flash for messaging
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('work_order_detail', order_id=order_id))

@app.route('/stop_supply_wait/<int:order_id>', methods=['POST'])
def stop_supply_wait(order_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Update the SupplyWaitTimes table to set the end time
        cursor.execute('UPDATE SupplyWaitTimes SET EndTime = NOW() WHERE OrderID = %s AND EndTime IS NULL', (order_id,))
        
        conn.commit()
        flash('Supply wait time stopped.', 'success')
    except mysql.connector.Error as err:
        print("SQL Error: ", err)
        flash('Database error occurred', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('work_order_detail', order_id=order_id))

#stop supply wait

#mechanic work hours

@app.route('/mechanic_work_hours', methods=['GET', 'POST'])
def mechanic_work_hours():
    filter_mechanic_id = request.args.get('filter_mechanic_id')
    search_query = request.args.get('search_query', '')

    conn = get_db_connection()
    mechanics = []
    work_hours = []

    try:
        cursor = conn.cursor()

        # Fetch list of mechanics for the dropdown
        cursor.execute('SELECT MechanicID, Name FROM Mechanics ORDER BY Name')
        mechanics = cursor.fetchall()

        # Build the query based on filters
        query = '''
            SELECT m.Name, tt.OrderID, tt.StartTime, tt.EndTime, TIMEDIFF(tt.EndTime, tt.StartTime) AS Duration
            FROM TimeTracking tt
            JOIN Mechanics m ON tt.MechanicID = m.MechanicID
        '''
        conditions = []
        params = []

        if filter_mechanic_id:
            conditions.append('m.MechanicID = %s')
            params.append(filter_mechanic_id)

        if search_query:
            conditions.append('tt.OrderID LIKE %s')
            params.append('%' + search_query + '%')

        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)

        query += ' ORDER BY tt.StartTime DESC'
        cursor.execute(query, params)
        work_hours = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template('mechanic_work_hours.html', work_hours=work_hours, mechanics=mechanics)


#mechanic work hours

#Ordenes de SERVICIO fin


#ordenes de SALIDA Principio

@app.route('/add_departure_order/<company>', methods=['GET', 'POST'])
def add_departure_order(company):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Mapeo de la empresa a su tabla de vehículos correspondiente
    vehicle_table_map = {
        'MontasaHN': 'Vehicles',
        'MontasaCR': 'vehiculosCR',
        'Monhaco': 'vehiculosMonhaco'
    }

    # Obtén la tabla de vehículos correcta según la empresa
    vehicle_table = vehicle_table_map.get(company, 'Vehicles')  # 'Vehicles' como predeterminado si no se encuentra la empresa

    # Busca vehículos disponibles en la tabla correspondiente
    cursor.execute(f'SELECT VehicleID, VehicleName FROM {vehicle_table} WHERE Status = %s', ('Disponible',))
    available_vehicles = cursor.fetchall()

    cursor.execute('SELECT IdOperador, NombreOperador FROM Operadores')  # Asumiendo que los operadores no están filtrados por empresa
    operadores = cursor.fetchall()

    if request.method == 'POST':
        vehicle_id = request.form['vehicle_id']
        operator_id = request.form['operator_id']
        location = request.form['location']
        comments = request.form['comments']

        # Verifica el estado actual del vehículo en la tabla correspondiente
        cursor.execute(f'SELECT Status FROM {vehicle_table} WHERE VehicleID = %s', (vehicle_id,))
        vehicle_status = cursor.fetchone()

        if vehicle_status and vehicle_status[0] == 'En Taller':
            # Si el vehículo está en taller, muestra un mensaje de error
            flash('El vehículo seleccionado está en taller y no puede ser asignado a una orden de salida.', 'error')
        else:
            try:
                # Inserta en OrdenesdeSalida con VehicleName, NombreOperador y Empresa
                insert_query = f'''
                    INSERT INTO OrdenesdeSalida (VehicleID, VehicleName, IdOperador, NombreOperador, Comentarios, Ubicacion, Empresa, HoraCreado)
                    VALUES (%s, (SELECT VehicleName FROM {vehicle_table} WHERE VehicleID = %s), %s, (SELECT NombreOperador FROM Operadores WHERE IdOperador = %s), %s, %s, %s, NOW())
                '''
                cursor.execute(insert_query, (vehicle_id, vehicle_id, operator_id, operator_id, comments, location, company))

                # Actualiza el estado y la ubicación del vehículo en la tabla correspondiente
                update_vehicle_query = f'''
                    UPDATE {vehicle_table}
                    SET Status = 'En Renta', Ubicacion = %s
                    WHERE VehicleID = %s
                '''
                cursor.execute(update_vehicle_query, (location, vehicle_id))

                conn.commit()
                flash('Orden de salida agregada, ubicación y estado del vehículo actualizados.', 'success')
            except mysql.connector.Error as err:
                conn.rollback()
                flash(f'Error al agregar la orden de salida: {err}', 'error')
            finally:
                cursor.close()
                conn.close()

        return redirect(url_for('active_departure_orders', company=company))

    cursor.close()
    conn.close()

    return render_template('CrearOrdenSalida.html', available_vehicles=available_vehicles, operadores=operadores, company=company)



@app.route('/active_departure_orders/<company>')
def active_departure_orders(company):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Mapeo de la compañía a la tabla de vehículos correspondiente
    vehicle_table_map = {
        'MontasaHN': 'Vehicles',
        'MontasaCR': 'vehiculosCR',
        'Monhaco': 'vehiculosMonhaco'
    }
    vehicle_table = vehicle_table_map.get(company, 'Vehicles')  # Usa 'Vehicles' como predeterminado si la compañía no se encuentra

    # Obtener los nombres de los vehículos para el dropdown, filtrando por empresa
    cursor.execute(f'SELECT DISTINCT VehicleName FROM {vehicle_table} WHERE Empresa = %s ORDER BY VehicleID', (company,))
    vehicle_names = cursor.fetchall()

    # Recuperar el vehículo seleccionado y las fechas desde la solicitud
    selected_vehicle_name = request.args.get('vehicle_name', '')
    start_date = request.args.get('start_date', '2024-01-01')  # Fecha de inicio por defecto
    end_date = request.args.get('end_date', (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))  # Fecha de fin al día siguiente

    # Construir la consulta SQL con los filtros aplicados, incluyendo la empresa
    query = f'''
        SELECT os.IdOrdenSalida, os.VehicleID, v.VehicleName, os.IdOperador, op.NombreOperador as NombreOperador, os.HoraCreado, os.Comentarios
        FROM OrdenesdeSalida os
        JOIN {vehicle_table} v ON os.VehicleID = v.VehicleID
        JOIN Operadores op ON os.IdOperador = op.IdOperador
        WHERE os.HoraRegreso IS NULL AND os.Empresa = %s
    '''
    params = [company]

    if selected_vehicle_name:
        query += ' AND v.VehicleName = %s'
        params.append(selected_vehicle_name)

    # Añadir el filtro de rango de fechas a la consulta
    query += ' AND os.HoraCreado BETWEEN %s AND %s ORDER BY os.IdOrdenSalida DESC'
    params.extend([start_date, end_date])

    cursor.execute(query, tuple(params))
    active_departure_orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('active_departure_orders.html', 
                           active_departure_orders=active_departure_orders, 
                           vehicle_names=vehicle_names, 
                           selected_vehicle_name=selected_vehicle_name, 
                           start_date=start_date, 
                           end_date=end_date, 
                           company=company)


@app.route('/departure_order_detail/<company>/<int:order_id>')
def departure_order_detail(company, order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the main details of the departure order
    cursor.execute('''
        SELECT os.IdOrdenSalida, os.VehicleID, v.VehicleName, os.IdOperador, o.NombreOperador, 
               os.HoraCreado, os.Comentarios, os.HorometroSalida, os.HorometroRegreso, 
               os.HoraRegreso, os.Ubicacion
        FROM OrdenesdeSalida os
        JOIN Vehicles v ON os.VehicleID = v.VehicleID
        JOIN Operadores o ON os.IdOperador = o.IdOperador
        WHERE os.IdOrdenSalida = %s
    ''', (order_id,))
    order_detail = cursor.fetchone()

    cursor.close()
    conn.close()

    if order_detail:
        # Convert the tuple to a dictionary for easier template handling
        order = {
            'IdOrdenSalida': order_detail[0],
            'VehicleID': order_detail[1],
            'VehicleName': order_detail[2],
            'IdOperador': order_detail[3],
            'NombreOperador': order_detail[4],
            'HoraCreado': order_detail[5],
            'Comentarios': order_detail[6],
            'HorometroSalida': order_detail[7],
            'HorometroRegreso': order_detail[8],
            'HoraRegreso': order_detail[9],
            'Ubicacion': order_detail[10]
        }
        return render_template('departure_order_detail.html', order=order, company=company)
    else:
        return 'Departure Order not found', 404




@app.route('/update_departure_order/<company>/<int:order_id>', methods=['POST'])
def update_departure_order(company, order_id):
    # Recuperar los datos del formulario
    horometroSalida = request.form.get('horometroSalida')
    horometroRegreso = request.form.get('horometroRegreso')
    comentarios = request.form.get('comentarios')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Actualizar datos básicos de la orden de salida
        cursor.execute('''
            UPDATE OrdenesdeSalida
            SET HorometroSalida = %s, HorometroRegreso = %s, Comentarios = %s
            WHERE IdOrdenSalida = %s
        ''', (horometroSalida, horometroRegreso, comentarios, order_id))

        # Actualizar el horómetro actual del vehículo, si se proporciona el horómetro de regreso
        if horometroRegreso:
            cursor.execute('''
                UPDATE Vehicles
                SET Horometro = %s
                WHERE VehicleID = (SELECT VehicleID FROM OrdenesdeSalida WHERE IdOrdenSalida = %s)
            ''', (horometroRegreso, order_id))

        conn.commit()
        flash('Orden de salida actualizada con éxito.', 'success')
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'Error al actualizar la orden de salida: {err}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('departure_order_detail', company=company, order_id=order_id))

@app.route('/complete_departure_order/<int:order_id>', methods=['POST'])
def complete_departure_order(order_id):
    company = request.form.get('company')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Actualizar la hora de regreso en la orden de salida
        cursor.execute('''
            UPDATE OrdenesdeSalida
            SET HoraRegreso = NOW()
            WHERE IdOrdenSalida = %s
        ''', (order_id,))

        # Cambiar el estado del vehículo asociado a "Disponible" y actualizar su ubicación a "Montasa"
        cursor.execute('''
            UPDATE Vehicles
            SET Status = 'Disponible', Ubicacion = 'Montasa'
            WHERE VehicleID = (SELECT VehicleID FROM OrdenesdeSalida WHERE IdOrdenSalida = %s)
        ''', (order_id,))

        conn.commit()
        flash('Orden de salida completada y vehículo actualizado.', 'success')
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'Error al completar la orden de salida: {err}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('active_departure_orders', company=company))



@app.route('/departure_orders_record/<company>', methods=['GET', 'POST'])
def departure_orders_record(company):
    order_id_query = request.args.get('order_id', '')
    operator_name_query = request.args.get('operator_name', '')
    vehicle_name_query = request.args.get('vehicle_name', '')
    start_date_query = request.args.get('start_date', '')
    end_date_query = request.args.get('end_date', '')

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        vehicle_table_map = {
        'MontasaHN': 'Vehicles',
        'MontasaCR': 'vehiculosCR',
        'Monhaco': 'vehiculosMonhaco'
    }
        vehicle_table = vehicle_table_map.get(company, 'Vehicles')

        # Asegúrate de tener el nombre de la empresa disponible como 'company'
        cursor.execute('SELECT DISTINCT IdOrdenSalida FROM OrdenesdeSalida WHERE Empresa = %s ORDER BY IdOrdenSalida DESC', (company,))
        order_ids = cursor.fetchall()

        # Fetch vehicle names for filtering options
        cursor.execute(f'SELECT DISTINCT VehicleName FROM {vehicle_table} WHERE Empresa = %s ORDER BY VehicleID', (company,))
        vehicle_names = cursor.fetchall()

        # Fetch operator names for filtering options
        cursor.execute('SELECT DISTINCT NombreOperador FROM Operadores')
        operator_names = [row[0] for row in cursor.fetchall()]


        # Constructing the SQL query based on search parameters
        query_conditions = ["os.HoraRegreso IS NOT NULL", "os.Empresa = %s"]  # Include only completed departure orders for the specified company
        query_params = [company]  # Start the query parameters list with the company

        if order_id_query:
            query_conditions.append("os.IdOrdenSalida = %s")
            query_params.append(order_id_query)

        if operator_name_query:
            query_conditions.append("op.NombreOperador LIKE %s")
            query_params.append(f'%{operator_name_query}%')

        if vehicle_name_query:
            query_conditions.append("v.VehicleName LIKE %s")
            query_params.append(f'%{vehicle_name_query}%')

        if start_date_query:
            query_conditions.append("os.HoraCreado >= %s")
            query_params.append(start_date_query)
        if end_date_query:
            query_conditions.append("os.HoraCreado <= %s")
            query_params.append(end_date_query)

        where_clause = " AND ".join(query_conditions)
        sql_query = f'''
            SELECT os.IdOrdenSalida, os.VehicleID, v.VehicleName, os.IdOperador, op.NombreOperador, 
                    os.HoraCreado, os.Comentarios, os.Ubicacion, os.HoraRegreso
            FROM OrdenesdeSalida os
            JOIN {vehicle_table} v ON os.VehicleID = v.VehicleID
            JOIN Operadores op ON os.IdOperador = op.IdOperador
            WHERE {where_clause}
            ORDER BY os.IdOrdenSalida DESC
        '''
        cursor.execute(sql_query, tuple(query_params))
        departure_orders = cursor.fetchall()


    except mysql.connector.Error as err:
        print("SQL Error: ", err)
        departure_orders = []  # In case of SQL error, return an empty list
    finally:
        cursor.close()
        conn.close()

    return render_template('departure_orders_record.html', departure_orders=departure_orders, order_ids=order_ids, vehicle_names=vehicle_names, operator_names=operator_names, company=company)

@app.route('/departure_order_record_detail/<company>/<int:order_id>')
def departure_order_record_detail(company, order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Mapeo de la compañía a la tabla de vehículos correspondiente
    vehicle_table_map = {
        'MontasaHN': 'Vehicles',
        'MontasaCR': 'vehiculosCR',
        'Monhaco': 'vehiculosMonhaco'
    }
    vehicle_table = vehicle_table_map.get(company, 'Vehicles')  # Usa 'Vehicles' como predeterminado

    # Consultar los detalles de la orden de salida específica utilizando la tabla de vehículos correcta
    cursor.execute(f'''
        SELECT os.IdOrdenSalida, os.VehicleID, v.VehicleName, os.IdOperador, op.NombreOperador, 
               os.HoraCreado, os.Comentarios, os.Ubicacion, os.HorometroSalida, os.HorometroRegreso, os.HoraRegreso
        FROM OrdenesdeSalida os
        JOIN {vehicle_table} v ON os.VehicleID = v.VehicleID
        JOIN Operadores op ON os.IdOperador = op.IdOperador
        WHERE os.IdOrdenSalida = %s AND v.Empresa = %s
    ''', (order_id, company))
    order_detail = cursor.fetchone()

    cursor.close()
    conn.close()

    if order_detail:
        # Pasar los detalles de la orden a la plantilla HTML
        return render_template('departure_order_record_detail.html', order=order_detail, company=company)
    else:
        # En caso de que la orden no exista, mostrar un mensaje o redirigir
        flash('Orden de salida no encontrada.', 'error')
        return redirect(url_for('departure_orders_record',company=company))










#Ordenes de SALIDA Fin

#horometros


@app.route('/update_horometros', methods=['GET', 'POST'])
def update_horometros():
    conn = get_db_connection()
    cursor = conn.cursor()
    error_message = None
    
    if request.method == 'POST':
        vehicle_id = request.form.get('vehicle_id')
        new_horometro = float(request.form.get('new_horometro'))

        # Fetch current horometro for the vehicle
        cursor.execute('SELECT Horometro FROM Vehicles WHERE VehicleID = %s', (vehicle_id,))
        current_horometro = cursor.fetchone()[0]

        if current_horometro is not None and new_horometro < current_horometro:
            error_message = "The new horometro value cannot be less than the current value."
        else:
            current_date = datetime.now().strftime('%Y-%m-%d')
            new_hdum = new_horometro - current_horometro if current_horometro is not None else 0

            # Update both Horometro and FechaActualizacionHorometro
            cursor.execute('UPDATE Vehicles SET Horometro = %s, HorometroDesdeUltimoMantenimiento = %s, FechaActualizacionHorometro = %s WHERE VehicleID = %s', 
                           (new_horometro, new_hdum, current_date, vehicle_id))
            conn.commit()

    search_query = request.args.get('search', '')
    if search_query:
        cursor.execute('SELECT * FROM Vehicles WHERE VehicleName LIKE %s', ('%' + search_query + '%',))
    else:
        cursor.execute('SELECT * FROM Vehicles')
    vehicles = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('vehicles.html', vehicles=vehicles, error_message=error_message)

@app.route('/update_vehicle/<int:vehicle_id>', methods=['POST'])
def update_vehicle_locacion_disponibilidad(vehicle_id):
    Ubicacion = request.form['Ubicacion']
    Disponibilidad = request.form['Disponibilidad']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        update_query = '''
            UPDATE Vehicles
            SET Ubicacion = %s, Disponibilidad = %s
            WHERE VehicleID = %s
        '''
        cursor.execute(update_query, (Ubicacion, Disponibilidad, vehicle_id))
        conn.commit()
        flash('Vehicle updated successfully.', 'success')
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'Error updating vehicle: {err.msg}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('vehicles_list'))


@app.route('/vehicle_search')
def vehicle_search():
    search_term = request.args.get('q', '')  # 'q' es un nombre común para parámetros de búsqueda
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT VehicleID, VehicleName FROM Vehicles WHERE VehicleName LIKE %s", ('%' + search_term + '%',))
    vehicles = cursor.fetchall()
    cursor.close()
    conn.close()
    results = [{'id': vehicle[0], 'text': vehicle[1]} for vehicle in vehicles]  # Asegúrate de que esto coincide con tu estructura de datos
    return jsonify(results)




#horometros




#pin

@app.route('/validate_mechanic_pin')
def validate_mechanic_pin():
    pin = request.args.get('pin')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT MechanicID, Name FROM Mechanics WHERE PinCode = %s', (pin,))
    mechanic = cursor.fetchone()
    cursor.close()
    conn.close()
    if mechanic:
        return jsonify({'id': mechanic['MechanicID'], 'name': mechanic['Name']})
    else:
        return jsonify({'id': None, 'name': None})

@app.route('/validate_operator_pin')
def validate_operator_pin():
    pin = request.args.get('pin')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT IdOperador, NombreOperador FROM Operadores WHERE PinCode = %s', (pin,))
    operator = cursor.fetchone()
    cursor.close()
    conn.close()
    if operator:
        return jsonify({'id': operator['IdOperador'], 'name': operator['NombreOperador']})
    else:
        return jsonify({'id': None, 'name': None})


#pin


#excel
    








if __name__ == '__main__':
    app.run(debug=True)

