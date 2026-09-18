# A Class that connects to a MySQL Database and provides some basic functions to interact with it.
# On creation, db, tabele, username and passwort and port are given as parameters.
# If table does not exist, it will be created. The SQL for this is read from a file.
# Functions:
#   - getLatestData: Returns the last x rows of a table
#   - insertData: Inserts a row into a table
#   - deleteData: Deletes a row from a table
#   - getTable: Returns the whole table as excel

import mysql.connector
import pandas as pd
import re

class MySQLDB:
    def __init__(self, host, db, table, username, password, port, excel_path):
        self.host = host
        self.db = db
        self.table = table
        self.username = username
        self.password = password
        self.port = port
        self.connection = None
        self.cursor = None
        self.columns = []
        self.excel_path = excel_path
        with open('create_table.sql', 'r') as file:
            self.create_table_sql = file.read()
        
        def setColumns():
            def lookup_creation_parameters(column_name, sql):
                # Regular expression to match the column definition
                pattern = re.compile(rf'`{column_name}`\s+([^,]+)')
                match = pattern.search(sql)
                if match:
                    return match.group(1).strip()
                return None
            # get all columns from table
            self.cursor.execute(f"SHOW COLUMNS FROM {self.table}")
            columns = self.cursor.fetchall()
            self.connection.commit()  # Fetch all results before executing a new query
            for column in columns:
                self.columns.append(column[0])
            #print("Columns in table:", self.columns)
            # get columns from create_table.sql file read into self.create_table_sql
            columns_defined = re.findall(r'`(\w+)`', self.create_table_sql)
            columns_defined.remove(self.table) # remove table name from list
            #print("Columns in create_table.sql:", columns_defined)
            
            # remove columns from table that are not in create_table.sql
            for column in self.columns:
                if column not in columns_defined:
                    print(f"Column '{column}' not in create_table.sql, removing...")
                    self.cursor.execute(f"ALTER TABLE {self.table} DROP COLUMN {column}")
                    self.connection.commit()
                    self.columns.remove(column)
                    
            # add columns to table that are in create_table.sql but not in table, reuse the sql definition for this defined in create_table.sql
            for column in columns_defined:
                if column not in self.columns:
                    print(f"Column '{column}' not in table, adding...")
                    self.cursor.execute(f"ALTER TABLE {self.table} ADD COLUMN {column} {lookup_creation_parameters(column, self.create_table_sql)}")
                    self.connection.commit()
                    self.columns.append(column)
                    
            print("Columns in table after update structure:", self.columns)
            
        try:
            self.connect()
            ## check if table exists
            self.cursor.execute(f"SHOW TABLES LIKE '{self.table}'")
            result = self.cursor.fetchone()
            if not result:
                print("Table does not exist, creating...")
                self.create_table()
                self.disconnect()
                self.connect()
                setColumns()
                # check if excel file exists
                try:
                    with open(self.excel_path):
                        pass
                    excel = self.read_xlsx()
                    print(excel)
                    # print excel columns
                    print("Columns in excel:", excel.columns)
                    # check if columns in excel are in table
                    not_in_table = [column for column in excel.columns if column not in self.columns]
                    if not excel.empty:
                        print("Inserting data from excel...")
                        print("Rows in excel that are not in database: ", not_in_table)
                        # remove columns that are not in table from excel
                        excel.drop(columns=not_in_table, inplace=True)
                        for index, row in excel.iterrows():
                            #convert row to dictionary
                            row = row.to_dict()
                            self.insert_data(row, silent=True)
                except FileNotFoundError:
                    print(f"File '{self.excel_path}' not found, skipping import from excel")
                    pass
                
            else:
                setColumns()
            

        except mysql.connector.Error as error:
            print("Failed to initialize MySQL database:", error)
            exit()
            
    def read_xlsx(self):
        # read T_Basis.xlsx to pandas dataframe
        df = pd.read_excel(self.excel_path)
        # convert float values in column id to integer values with a lambda function
        df['id'] = df['id'].apply(lambda x: int(x))
        # define column id as integer
        df['id'] = df['id'].astype(int)
        print(df)
        # convert data in columns unterschrift_haft, reparatur_ok, din_pruef to 0 if FALSCH or to 1 if WAHR, if empty set to 0
        #remove column unterschrift_rep if exists
        if 'unterschrift_rep' in df.columns:
            df.drop('unterschrift_rep', axis=1, inplace=True)
        df['unterschrift_haft'] = df['unterschrift_haft'].apply(lambda x: 1 if x == 'WAHR' or x == 1 else 0)
        df['unterschrift_haft'] = df['unterschrift_haft'].astype(int)
        df['din_pruef'] = df['din_pruef'].apply(lambda x: 1 if x == 'WAHR' or x == 1 else 0)
        df['din_pruef'] = df['din_pruef'].astype(int)
        # remove column zettel_fehlt if exists
        if 'zettel_fehlt' in df.columns:
            df.drop('zettel_fehlt', axis=1, inplace=True)

        # fill all empty and NaN values with
        df['datum'] = df['datum'].fillna('1970-1-1')
        df['vorname'] = df['vorname'].fillna('')
        df['nachname'] = df['nachname'].fillna('')
        df['telefon'] = df['telefon'].fillna('')
        df['email'] = df['email'].fillna('')
        df['geraet_art'] = df['geraet_art'].fillna('')
        df['defekt_besch'] = df['defekt_besch'].fillna('')
        df['reparatur_erg'] = df['reparatur_erg'].fillna('')
        df['reparatur_besch'] = df['reparatur_besch'].fillna('')
        df['reparatur_dauer'] = df['reparatur_dauer'].fillna(0)
        df['reparatur_dauer'] = df['reparatur_dauer'].astype(int)
        df['reparateur'] = df['reparateur'].fillna('')

        # convert datum to mysql date format
        df['datum'] = pd.to_datetime(df['datum']).dt.strftime('%Y-%m-%d')
        # add column qr_token if not exists
        if 'unterschrift' not in df.columns:
            df['unterschrift'] = ''
            df['unterschrift'] = df['unterschrift'].astype(str)
        else:
            df['unterschrift'].fillna('', inplace=True)
            df['unterschrift'] = df['unterschrift'].astype(str)
            
        if 'qr_token' not in df.columns:
            df['qr_token'] = ''
            df['qr_token'] = df['qr_token'].astype(str)
        else:
            df['qr_token'].fillna('', inplace=True)
            df['qr_token'] = df['qr_token'].astype(str)
        return df

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.username,
                password=self.password,
                port=self.port,
                database=self.db
            )
            self.cursor = self.connection.cursor()
            print("Connected to MySQL database")
        except mysql.connector.Error as error:
            print("Failed to connect to MySQL database:", error)
            
    def is_connected(self):
        return self.connection.is_connected()

    def disconnect(self):
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("Disconnected from MySQL database")

    def create_table(self):
        try:
            self.cursor.execute(self.create_table_sql)
            print("Table created successfully")
        except mysql.connector.Error as error:
            print("Failed to create table:", error)

    def get_latest_data(self, num_rows):
        try:
            query = f"SELECT * FROM {self.table} ORDER BY id DESC LIMIT {num_rows}"
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            rows = []
            for row in result:
                row_dict = {}
                for i in range(len(columns)):
                    row_dict[columns[i]] = row[i]
                rows.append(row_dict)
            return rows
        except mysql.connector.Error as error:
            print("Failed to get latest data:", error)
            
    def get_row(self, row_id):
        try:
            query = f"SELECT * FROM {self.table} WHERE id = {row_id}"
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            if result:
                columns = [desc[0] for desc in self.cursor.description]
                row_dict = {}
                for i in range(len(columns)):
                    row_dict[columns[i]] = result[i]
                return row_dict
            else:
                print("No data found")
        except mysql.connector.Error as error:
            print("Failed to get row:", error)

    def insert_data(self, data, silent=False):
        try:
            columns = ', '.join(data.keys())
            values = ', '.join(['%s'] * len(data))
            query = f"INSERT INTO {self.table} ({columns}) VALUES ({values})"
            # Check if keys (columns) are in self.columns
            for key in data.keys():
                if key not in self.columns:
                    print(f"Column '{key}' does not exist in the table")
                    return
            self.cursor.execute(query, list(data.values()))
            self.connection.commit()
            if not silent:
                print("Data inserted successfully")
            return self.cursor.lastrowid  # Return the id/index of the inserted row
        except mysql.connector.Error as error:
            print("Failed to insert data:", error)
            print("Data:",data, "Query:",query)
            if not silent:
                print(query)
                print(list(data.values()))
            
    def update_data(self, row_id, data):
        try:
            query = f"UPDATE {self.table} SET "
            for key, value in data.items():
                query += f"{key} = '{value}', "
            query = query[:-2]  # Remove the last comma and space
            query += f" WHERE id = {row_id}"
            self.cursor.execute(query)
            self.connection.commit()
            if self.cursor.rowcount > 0:
                print("Data updated successfully")
            else:
                print("No data found to update")
        except mysql.connector.Error as error:
            print("Failed to update data:", error)

    def delete_data(self, row_id):
        try:
            query = f"DELETE FROM {self.table} WHERE id = {row_id}"
            self.cursor.execute(query)
            self.connection.commit()
            if self.cursor.rowcount > 0:
                print("Data deleted successfully")
            else:
                print("No data found to delete")
        except mysql.connector.Error as error:
            print("Failed to delete data:", error)

    def get_table(self):
        try:
            query = f"SELECT * FROM {self.table}"
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            df = pd.DataFrame(result, columns=columns)
            df.set_index('id', inplace=True)  # Set 'id' as the index
            return df
        except mysql.connector.Error as error:
            print("Failed to get table:", error)