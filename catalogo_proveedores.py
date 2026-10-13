"""
Modulo de catalogo de proveedores.
Carga el catalogo desde el JSON y permite busquedas.
"""
import json
from pathlib import Path
from typing import Optional, List

CATALOG_PATH = Path(__file__).parent / "proveedores_catalogo.json"


class CatalogoProveedores:
    def __init__(self):
        self.proveedores: List[dict] = []
        self.by_rif: dict = {}
        self.by_nombre: dict = {}
        self.load()

    def load(self) -> None:
        if not CATALOG_PATH.exists():
            return
        try:
            data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
            self.proveedores = data.get("proveedores", [])
        except Exception:
            self.proveedores = []
        # Indexar
        for p in self.proveedores:
            self.by_rif[p["rif"].upper()] = p
            self.by_nombre[p["nombre"].upper()] = p

    def buscar_por_nombre(self, query: str) -> List[dict]:
        """Busca proveedores por nombre (case-insensitive, contains)."""
        if not query:
            return []
        q = query.upper()
        return [p for p in self.proveedores if q in p["nombre"].upper()][:20]

    def get_por_rif(self, rif: str) -> Optional[dict]:
        return self.by_rif.get(rif.upper())

    def get_por_nombre_exacto(self, nombre: str) -> Optional[dict]:
        return self.by_nombre.get(nombre.upper())

    def sugerir_match(self, nombre: str, rif: str) -> Optional[dict]:
        """Intenta matchear un proveedor por RIF o nombre."""
        if rif:
            p = self.get_por_rif(rif)
            if p:
                return p
        if nombre:
            p = self.get_por_nombre_exacto(nombre)
            if p:
                return p
        return None

    def get_nombres(self) -> List[str]:
        """Retorna lista de nombres para autocompletar."""
        return [p["nombre"] for p in self.proveedores]


# Instancia global
catalogo = CatalogoProveedores()
