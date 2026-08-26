import sys

from cargar_oracle import main


if __name__ == "__main__":
    raise SystemExit(main(["--carga", "rmj", *sys.argv[1:]]))
