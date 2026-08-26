from carga_comun import ConfigCarga, ejecutar_carga


if __name__ == "__main__":
    raise SystemExit(
        ejecutar_carga(
            ConfigCarga(
                nombre="VRYR",
                esquema="CSNISPVRYR",
                prefijo_tabla="Z_PYLOAD_VRYR",
                estructura="ESTRUCTURAS/CNI_VRYR.txt",
                carpeta_datos="DATOS/VRYR",
                archivos=(
                    "CNI_VRYR.dat",
                )
            )
        )
    )