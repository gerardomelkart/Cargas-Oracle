import sys

from cargar_oracle import main


if __name__ == "__main__":
    raise SystemExit(main(["--carga", "rnpsp", *sys.argv[1:]]))
