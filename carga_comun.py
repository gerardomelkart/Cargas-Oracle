import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "configuracion.local.json"


@dataclass(frozen=True)
class ConfigCarga:
    nombre: str
    esquema: str
    prefijo_tabla: str
    estructura: str
    carpeta_datos: str
    archivos: tuple[str, ...]
    batch_size: int = 1000


def obtener_driver():
    try:
        import oracledb

        return oracledb

    except ImportError as error:
        raise RuntimeError(
            "Falta instalar oracledb. "
            "Ejecuta el archivo .bat correspondiente."
        ) from error


def obtener_periodo_anterior():
    hoy = date.today()

    if hoy.month == 1:
        return hoy.year - 1, 12

    return hoy.year, hoy.month - 1


def obtener_sufijo_periodo():
    anio, mes = obtener_periodo_anterior()

    return f"{anio}{mes:02d}"


def leer_configuracion():
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(
            f"No existe el archivo:\n{CONFIG_PATH}"
        )

    with CONFIG_PATH.open(
        encoding="utf-8"
    ) as archivo:
        configuracion = json.load(archivo)

    campos = (
        "host",
        "port",
        "service",
        "user",
        "password"
    )

    for campo in campos:
        if campo not in configuracion:
            raise ValueError(
                f"Falta '{campo}' en "
                f"{CONFIG_PATH.name}"
            )

        if str(
            configuracion[campo]
        ).strip() == "":
            raise ValueError(
                f"El campo '{campo}' está vacío "
                f"en {CONFIG_PATH.name}"
            )

    return configuracion


def crear_conexion(configuracion):
    oracledb = obtener_driver()

    dsn = oracledb.makedsn(
        configuracion["host"],
        int(configuracion["port"]),
        service_name=configuracion["service"]
    )

    parametros = {
        "user": configuracion["user"],
        "password": configuracion["password"],
        "dsn": dsn
    }

    if configuracion["user"].upper() == "SYS":
        parametros["mode"] = (
            oracledb.AUTH_MODE_SYSDBA
        )

    return oracledb.connect(
        **parametros
    )


def buscar_archivo(
    carpeta,
    nombre
):
    coincidencias = [
        ruta
        for ruta in carpeta.rglob("*")
        if ruta.is_file()
        and ruta.name.casefold()
        == nombre.casefold()
    ]

    if not coincidencias:
        raise FileNotFoundError(
            f"No se encontró {nombre} "
            f"dentro de:\n{carpeta}"
        )

    if len(coincidencias) > 1:
        rutas = "\n".join(
            f"  - {ruta}"
            for ruta in coincidencias
        )

        raise RuntimeError(
            f"Se encontraron varias copias "
            f"de {nombre}:\n{rutas}\n"
            "Deja únicamente la correspondiente "
            "al periodo que vas a cargar."
        )

    return coincidencias[0]


def leer_estructura(ruta):
    columnas = []

    patron = re.compile(
        r"^\s*([A-Z0-9_]+)"
        r"\s+POSITION\s+"
        r"\((\d+):(\d+)\)",
        re.IGNORECASE
    )

    with ruta.open(
        encoding="latin-1"
    ) as archivo:
        for numero_linea, linea in enumerate(
            archivo,
            1
        ):
            coincidencia = patron.search(
                linea
            )

            if not coincidencia:
                raise ValueError(
                    f"Estructura inválida en "
                    f"{ruta.name}, línea "
                    f"{numero_linea}:\n"
                    f"{linea.rstrip()}"
                )

            nombre = coincidencia.group(1)
            inicio = int(
                coincidencia.group(2)
            )
            fin = int(
                coincidencia.group(3)
            )

            if inicio < 1 or fin < inicio:
                raise ValueError(
                    f"Posiciones inválidas para "
                    f"{nombre} en {ruta.name}, "
                    f"línea {numero_linea}"
                )

            columnas.append(
                (
                    nombre,
                    inicio,
                    fin
                )
            )

    if not columnas:
        raise ValueError(
            f"La estructura está vacía: "
            f"{ruta}"
        )

    return columnas


def validar_identificador(valor):
    if not re.fullmatch(
        r"[A-Z][A-Z0-9_$#]*",
        valor,
        re.IGNORECASE
    ):
        raise ValueError(
            f"Identificador Oracle inválido: "
            f"{valor}"
        )

    return valor


def generar_sql_create(
    esquema,
    tabla,
    columnas
):
    definiciones = []

    for nombre, inicio, fin in columnas:
        longitud = min(
            fin - inicio + 1,
            4000
        )

        definiciones.append(
            f"{validar_identificador(nombre)} "
            f"VARCHAR2({longitud} CHAR)"
        )

    definiciones.append(
        "TEXTFILENAME VARCHAR2(200 CHAR)"
    )

    return (
        f"CREATE TABLE "
        f"{validar_identificador(esquema)}."
        f"{validar_identificador(tabla)} "
        f"({', '.join(definiciones)})"
    )


def ajustar_estructura_tabla(
    cursor,
    esquema,
    tabla,
    columnas
):
    esquema = validar_identificador(
        esquema
    )

    tabla = validar_identificador(
        tabla
    )

    cursor.execute(
        """
        SELECT
            COLUMN_NAME,
            DATA_TYPE,
            CHAR_LENGTH,
            CHAR_USED
        FROM ALL_TAB_COLUMNS
        WHERE OWNER = :1
        AND TABLE_NAME = :2
        """,
        [
            esquema.upper(),
            tabla.upper()
        ]
    )

    columnas_actuales = {
        fila[0]: {
            "tipo": fila[1],
            "longitud": fila[2],
            "unidad": fila[3]
        }
        for fila in cursor.fetchall()
    }

    columnas_esperadas = [
        (
            validar_identificador(nombre),
            min(
                fin - inicio + 1,
                4000
            )
        )
        for nombre, inicio, fin in columnas
    ]

    columnas_esperadas.append(
        (
            "TEXTFILENAME",
            200
        )
    )

    for nombre, longitud in columnas_esperadas:
        actual = columnas_actuales.get(
            nombre.upper()
        )

        if actual is None:
            cursor.execute(
                f"ALTER TABLE "
                f"{esquema}.{tabla} "
                f"MODIFY ("
                f"{nombre} "
                f"VARCHAR2("
                f"{nueva_longitud} CHAR"
                f"))"
            )

            print(
                f"Columna agregada: "
                f"{nombre} "
                f"VARCHAR2({longitud} CHAR)"
            )

            continue

        if actual["tipo"] not in (
            "VARCHAR",
            "VARCHAR2",
            "CHAR"
        ):
            raise RuntimeError(
                f"La columna {nombre} tiene "
                f"tipo {actual['tipo']} y no puede "
                f"ajustarse automáticamente."
            )

        longitud_actual = (
            actual["longitud"] or 0
        )

        usa_caracteres = (
            actual["unidad"] == "C"
        )

        if (
            longitud_actual < longitud
            or not usa_caracteres
        ):
            nueva_longitud = max(
                longitud_actual,
                longitud
            )

            cursor.execute(
                f"ALTER TABLE "
                f"{esquema}.{tabla} "
                f"MODIFY ("
                f"{nombre} "
                f"VARCHAR2("
                f"{nueva_longitud} CHAR"
                f")"
            )

            print(
                f"Columna ajustada: "
                f"{nombre} "
                f"VARCHAR2("
                f"{nueva_longitud} CHAR)"
            )

def preparar_tabla(
    conexion,
    esquema,
    tabla,
    columnas
):
    oracledb = obtener_driver()
    cursor = conexion.cursor()

    try:
        sql_create = generar_sql_create(
            esquema,
            tabla,
            columnas
        )

        try:
            cursor.execute(
                sql_create
            )

            print(
                f"Tabla creada: "
                f"{esquema}.{tabla}"
            )

        except oracledb.DatabaseError as error:
            detalle = error.args[0]
            codigo = getattr(
                detalle,
                "code",
                None
            )

            if codigo != 955:
                raise

            print(
                f"La tabla ya existe: "
                f"{esquema}.{tabla}"
            )

        ajustar_estructura_tabla(
            cursor,
            esquema,
            tabla,
            columnas
        )

        cursor.execute(
            f"TRUNCATE TABLE "
            f"{validar_identificador(esquema)}."
            f"{validar_identificador(tabla)}"
        )

        print(
            "Tabla truncada."
        )

    finally:
        cursor.close()


def convertir_fila(
    linea,
    columnas,
    nombre_archivo
):
    linea = linea.rstrip(
        "\r\n"
    )

    valores = [
        linea[inicio - 1:fin].strip()
        for _, inicio, fin in columnas
    ]

    valores.append(
        nombre_archivo
    )

    return tuple(
        valores
    )


def cargar_archivos(
    conexion,
    configuracion,
    tabla,
    columnas,
    archivos
):
    esquema = validar_identificador(
        configuracion.esquema
    )

    tabla = validar_identificador(
        tabla
    )

    nombres_columnas = [
        validar_identificador(
            nombre
        )
        for nombre, _, _ in columnas
    ]

    nombres_columnas.append(
        "TEXTFILENAME"
    )

    lista_columnas = ", ".join(
        nombres_columnas
    )

    cantidad_valores = len(
        nombres_columnas
    )

    marcadores = ", ".join(
        f":{numero}"
        for numero in range(
            1,
            cantidad_valores + 1
        )
    )

    sql_insert = (
        f"INSERT INTO "
        f"{esquema}.{tabla} "
        f"({lista_columnas}) "
        f"VALUES ({marcadores})"
    )

    cursor = conexion.cursor()
    total = 0

    try:
        for ruta in archivos:
            lote = []
            procesadas = 0
            siguiente_reporte = 10000

            print(
                f"Procesando: {ruta}"
            )

            with ruta.open(
                encoding="latin-1"
            ) as archivo:
                for linea in archivo:
                    lote.append(
                        convertir_fila(
                            linea,
                            columnas,
                            ruta.name
                        )
                    )

                    if len(lote) >= (
                        configuracion.batch_size
                    ):
                        cantidad_lote = len(
                            lote
                        )

                        cursor.executemany(
                            sql_insert,
                            lote
                        )

                        conexion.commit()

                        procesadas += cantidad_lote

                        lote.clear()

                        if procesadas >= siguiente_reporte:
                            print(
                                f"Avance: "
                                f"{procesadas:,} filas "
                                f"insertadas..."
                            )

                            while (
                                siguiente_reporte
                                <= procesadas
                            ):
                                siguiente_reporte += 10000

                if lote:
                    cursor.executemany(
                        sql_insert,
                        lote
                    )

                    conexion.commit()

                    procesadas += len(
                        lote
                    )

            total += procesadas

            print(
                f"Filas cargadas desde "
                f"{ruta.name}: "
                f"{procesadas:,}"
            )

    finally:
        cursor.close()

    return total


def ejecutar_carga(
    configuracion
):
    try:
        sufijo = obtener_sufijo_periodo()

        estructura_path = (
            BASE_DIR
            / configuracion.estructura
        ).resolve()

        datos_path = (
            BASE_DIR
            / configuracion.carpeta_datos
        ).resolve()

        if not estructura_path.is_file():
            raise FileNotFoundError(
                f"No existe la estructura:\n"
                f"{estructura_path}"
            )

        if not datos_path.is_dir():
            raise FileNotFoundError(
                f"No existe la carpeta de datos:\n"
                f"{datos_path}"
            )

        columnas = leer_estructura(
            estructura_path
        )
        
        archivos = sorted(
            ruta
            for ruta in datos_path.rglob("*")
            if ruta.is_file()
            and ruta.suffix.casefold() == ".dat"
        )

        cantidad_esperada = len(
            configuracion.archivos
        )

        if not archivos:
            raise FileNotFoundError(
                f"No se encontraron archivos .dat "
                f"dentro de:\n{datos_path}"
            )

        if len(archivos) != cantidad_esperada:
            raise RuntimeError(
                f"Se esperaban {cantidad_esperada} "
                f"archivo(s) .dat dentro de:\n"
                f"{datos_path}\n"
                f"Se encontraron: {len(archivos)}"
            )

        tabla = (
            f"{configuracion.prefijo_tabla}_"
            f"{sufijo}"
        )

        generar_sql_create(
            configuracion.esquema,
            tabla,
            columnas
        )

        print(
            "========================================"
        )

        print(
            f"CARGA: {configuracion.nombre}"
        )

        print(
            f"PERIODO: {sufijo}"
        )

        print(
            f"TABLA: "
            f"{configuracion.esquema}."
            f"{tabla}"
        )

        print(
            f"ARCHIVOS: {len(archivos)}"
        )

        print(
            "========================================"
        )

        print(
            "Todos los archivos y la estructura "
            "fueron validados."
        )

        configuracion_oracle = (
            leer_configuracion()
        )

        print(
            "Conectando a Oracle..."
        )

        conexion = crear_conexion(
            configuracion_oracle
        )

        print(
            "Conexión correcta."
        )

        try:
            preparar_tabla(
                conexion,
                configuracion.esquema,
                tabla,
                columnas
            )

            total = cargar_archivos(
                conexion,
                configuracion,
                tabla,
                columnas,
                archivos
            )

        finally:
            conexion.close()

        print(
            "========================================"
        )

        print(
            "CARGA TERMINADA CORRECTAMENTE"
        )

        print(
            f"TOTAL: {total:,} filas"
        )

        print(
            "========================================"
        )

        return 0

    except Exception as error:
        print(
            "========================================",
            file=sys.stderr
        )

        print(
            f"ERROR: {error}",
            file=sys.stderr
        )

        print(
            "========================================",
            file=sys.stderr
        )

        return 1