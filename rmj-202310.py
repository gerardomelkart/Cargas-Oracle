from carga_comun import ConfigCarga, ejecutar_carga


if __name__ == "__main__":
    raise SystemExit(
        ejecutar_carga(
            ConfigCarga(
                nombre="MANDAMIENTOS",
                esquema="CSNISPMANDAMIENTOS",
                prefijo_tabla="Z_PYLOAD_MANDAMIENTOS",
                estructura="ESTRUCTURAS/CNI_MANDAMIENTOS.txt",
                carpeta_datos="DATOS/RMJ",
                archivos=(
                    "CNI_Mandamientos.dat",
                )
            )
        )
    )