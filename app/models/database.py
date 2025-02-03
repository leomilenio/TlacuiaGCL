import sqlite3
from datetime import datetime, timedelta

class ConcesionesDB:
    def __init__(self, db_name='concesiones.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._crear_tablas()
        
    def _crear_tablas(self):
        """Crea las tablas necesarias si no existen"""
        self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS grantingEmisor (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_emisor TEXT NOT NULL,
                nombre_vendedor TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS Contacto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emisor_id INTEGER NOT NULL,
                numero INTEGER,
                correo_electronico TEXT,
                FOREIGN KEY (emisor_id) REFERENCES grantingEmisor(id)
            );
            
            CREATE TABLE IF NOT EXISTS Concesiones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emisor_id INTEGER NOT NULL,
                tipo TEXT CHECK(tipo IN ('Nota de credito', 'Factura')),
                folio TEXT NOT NULL,
                fecha_recepcion TEXT DEFAULT CURRENT_DATE,
                fecha_vencimiento TEXT NOT NULL,
                finalizada BOOLEAN DEFAULT 0,  
                FOREIGN KEY (emisor_id) REFERENCES grantingEmisor(id)
            );
            
            CREATE TABLE IF NOT EXISTS Documentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concesion_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                tipo TEXT CHECK(tipo IN ('PDF', 'Excel', 'CSV')),
                contenido BLOB NOT NULL,
                FOREIGN KEY (concesion_id) REFERENCES Concesiones(id)
            );
                                  
            CREATE TABLE IF NOT EXISTS DocumentoProducto (
                documento_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                tipo_dato TEXT CHECK(tipo_dato IN ('ingreso', 'corte')),
                FOREIGN KEY(documento_id) REFERENCES Documentos(id),
                FOREIGN KEY(producto_id) REFERENCES Productos(id)
            );
                                  
            CREATE TABLE IF NOT EXISTS Productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concesion_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                descripcion TEXT NOT NULL,
                isbn TEXT,
                pvp_unitario REAL,
                precio_neto REAL NOT NULL,
                precio_total REAL NOT NULL,
                cantidad_vendida INTEGER DEFAULT 0,
                FOREIGN KEY (concesion_id) REFERENCES Concesiones(id)
            );

            CREATE TABLE IF NOT EXISTS ReportesPDF (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concesion_id INTEGER NOT NULL,
                nombre_archivo TEXT NOT NULL,
                contenido BLOB NOT NULL,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (concesion_id) REFERENCES Concesiones(id)
            );                       
        ''')
        self.conn.commit()
    

    def obtener_documento_por_id(self, doc_id):
        self.cursor.execute('SELECT nombre, tipo, contenido FROM Documentos WHERE id = ?', (doc_id,))
        result = self.cursor.fetchone()
        if result:
            return {
                'nombre': result[0],
                'tipo': result[1],
                'contenido': result[2]
            }
        return None

    def marcar_concesion_como_finalizada(self, concesion_id):
        self.cursor.execute('''
            UPDATE Concesiones 
            SET finalizada = 1 
            WHERE id = ?
        ''', (concesion_id,))
        self.conn.commit()

    def obtener_concesion_por_id(self, concesion_id):
        self.cursor.execute('SELECT * FROM Concesiones WHERE id = ?', (concesion_id,))
        column_names = [column[0] for column in self.cursor.description]
        row = self.cursor.fetchone()
        if not row:
            return None
        concesion = dict(zip(column_names, row))
        concesion['status'] = self._calcular_status(concesion['fecha_recepcion'], concesion['fecha_vencimiento'])
        return concesion

    def obtener_concesiones_no_finalizadas_con_emisor(self):
            """Obtiene todas las concesiones no finalizadas con el nombre del emisor y folio,
            filtrando solo aquellas que tienen documentos vinculados"""
            self.cursor.execute('''
            SELECT c.id, ge.nombre_emisor, c.folio, c.fecha_recepcion, c.fecha_vencimiento
            FROM Concesiones c
            JOIN grantingEmisor ge ON c.emisor_id = ge.id
            WHERE c.finalizada = 0
            AND EXISTS (
                SELECT 1
                FROM Documentos d
                WHERE d.concesion_id = c.id
            )
            ''')
            column_names = [column[0] for column in self.cursor.description]
            return [dict(zip(column_names, row)) for row in self.cursor.fetchall()]

    def crear_emisor(self, nombre_emisor, nombre_vendedor):
        """Crea un nuevo emisor en grantingEmisor"""
        self.cursor.execute('''
            INSERT INTO grantingEmisor (nombre_emisor, nombre_vendedor)
            VALUES (?, ?)
        ''', (nombre_emisor, nombre_vendedor))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def crear_contacto(self, emisor_id, numero, correo):
        """Añade un contacto a un emisor"""
        self.cursor.execute('''
            INSERT INTO Contacto (emisor_id, numero, correo_electronico)
            VALUES (?, ?, ?)
        ''', (emisor_id, numero, correo))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def crear_concesion(self, emisor_id, tipo, folio, fecha_recepcion,fecha_vencimiento=None, dias_validez=None):
        """Crea una nueva concesión con validación de fechas"""
        if tipo not in ('Nota de credito', 'Factura'):
            raise ValueError("Tipo debe ser 'Nota de credito' o 'Factura'")
        
        if sum([fecha_vencimiento is not None, dias_validez is not None]) != 1:
            raise ValueError("Debe proporcionar solo una opción: fecha_vencimiento o dias_validez")
        
        if dias_validez:
            fecha_recepcion = datetime.strptime(fecha_recepcion, '%Y-%m-%d').date()
            fecha_vencimiento = (fecha_recepcion + timedelta(days=dias_validez)).strftime('%Y-%m-%d')
        
        self.cursor.execute('''
            INSERT INTO Concesiones (emisor_id, tipo, folio, fecha_recepcion, fecha_vencimiento)
            VALUES (?, ?, ?, ?, ?)
        ''', (emisor_id, tipo, folio, fecha_recepcion, fecha_vencimiento))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def crear_documento(self, concesion_id, nombre, tipo, archivo_path):
        """Almacena un documento en la base de datos"""
        if tipo not in ('PDF', 'Excel', 'CSV'):
            raise ValueError("Tipo debe ser PDF, Excel o CSV")
        
        with open(archivo_path, 'rb') as f:
            contenido = f.read()
        
        self.cursor.execute('''
            INSERT INTO Documentos (concesion_id, nombre, tipo, contenido)
            VALUES (?, ?, ?, ?)
        ''', (concesion_id, nombre, tipo, contenido))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def obtener_emisores(self):
        """Obtiene todos los emisores registrados"""
        self.cursor.execute('SELECT * FROM grantingEmisor')
        return self.cursor.fetchall()
    
    def obtener_concesiones(self):
        """Obtiene todas las concesiones con su estado actualizado"""
        self.cursor.execute('SELECT * FROM Concesiones')
        column_names = [column[0] for column in self.cursor.description]
        concesiones = []

        prioridad_estados = {
        "Vence pronto": 0,
        "Valido": 1,
        "Vencida": 2
        }

        for row in self.cursor.fetchall():
            # Crear diccionario con nombres de columna
            concesion = dict(zip(column_names, row))
            # Calcular estado
            concesion['status'] = self._calcular_status(concesion['fecha_recepcion'], concesion['fecha_vencimiento'])
            concesiones.append(concesion)
        return sorted(concesiones, 
                key=lambda x: (prioridad_estados[x['status']], x['fecha_vencimiento']))
    

    def _calcular_status(self, fecha_recepcion, fecha_vencimiento):
        """Calcula el estado de la concesión según las nuevas reglas"""
        hoy = datetime.now().date()
        rec = datetime.strptime(fecha_recepcion, '%Y-%m-%d').date()
        venc = datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date()

        if hoy > venc:
            return 'Vencida'
        
        # Si la fecha actual está dentro del rango [recepción, vencimiento]
        dias_restantes = (venc - hoy).days
        return 'Vence pronto' if dias_restantes <= 14 else 'Valido'
    
    def obtener_documentos(self, concesion_id):
        """Obtiene documentos asociados a una concesión"""
        self.cursor.execute('SELECT * FROM Documentos WHERE concesion_id = ?', (concesion_id,))
        return self.cursor.fetchall()
    
    def obtener_contactos(self, emisor_id):
        """Obtiene contactos de un emisor"""
        self.cursor.execute('SELECT * FROM Contacto WHERE emisor_id = ?', (emisor_id,))
        return self.cursor.fetchall()
    
    def crear_producto(self, concesion_id, cantidad, descripcion, isbn, pvp_unitario, precio_neto):
        precio_total = cantidad * precio_neto
        self.cursor.execute('''
        INSERT INTO Productos (concesion_id, cantidad, descripcion, isbn, pvp_unitario, precio_neto, precio_total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (concesion_id, cantidad, descripcion, isbn, pvp_unitario, precio_neto, precio_total))
        self.conn.commit()
        return self.cursor.lastrowid

    def obtener_productos_por_concesion(self, concesion_id):
        self.cursor.execute('SELECT * FROM Productos WHERE concesion_id = ?', (concesion_id,))
        column_names = [column[0] for column in self.cursor.description]
        return [dict(zip(column_names, row)) for row in self.cursor.fetchall()]

    def actualizar_cantidad_vendida(self, producto_id, cantidad_vendida):
        self.cursor.execute('UPDATE Productos SET cantidad_vendida = ? WHERE id = ?', 
                        (cantidad_vendida, producto_id))
        self.conn.commit()

    def crear_reporte_pdf(self, concesion_id, nombre_archivo, contenido):
        """Almacena un reporte PDF en la base de datos"""
        self.cursor.execute('''
            INSERT INTO ReportesPDF (concesion_id, nombre_archivo, contenido)
            VALUES (?, ?, ?)
        ''', (concesion_id, nombre_archivo, contenido))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def obtener_reportes_por_concesion(self, concesion_id):
        """Obtiene todos los reportes PDF de una concesión"""
        self.cursor.execute('''
            SELECT id, nombre_archivo, fecha_creacion 
            FROM ReportesPDF 
            WHERE concesion_id = ?
        ''', (concesion_id,))
        return self.cursor.fetchall()
    
    def obtener_contenido_reporte(self, reporte_id):
        """Obtiene el contenido binario de un reporte"""
        self.cursor.execute('''
            SELECT contenido FROM ReportesPDF WHERE id = ?
        ''', (reporte_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def __del__(self):
        self.conn.close()