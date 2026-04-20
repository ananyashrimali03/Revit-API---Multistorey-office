import pandas as pd

BASE_PATH = (
    r"C:\Users\anany\OneDrive\Desktop\CMU\S26\Job Apps\KUNZ\kunz_demo\office\\"
)

# ── EMBODIED CARBON FACTORS ──────────────────────────────
# Source: ICE Database + EC3 — kgCO2e per kg, density kg/m3

CARBON_DATA = {
    'Brick, Common': {
        'density': 1800, 'carbon_factor': 0.24
    },
    'Concrete Masonry Units': {
        'density': 2000, 'carbon_factor': 0.11
    },
    'Concrete Masonry Units _High Density': {
        'density': 2200, 'carbon_factor': 0.13
    },
    'Gypsum Wall Board': {
        'density': 800, 'carbon_factor': 0.39
    },
    'Metal Stud Layer': {
        'density': 7800, 'carbon_factor': 2.89
    },
    'Plywood, Sheathing': {
        'density': 540, 'carbon_factor': 0.45
    },
    'Air Infiltration Barrier': {
        'density': 0, 'carbon_factor': 0
    },
    'Air': {
        'density': 0, 'carbon_factor': 0
    },
    'Vapor Retarder': {
        'density': 0, 'carbon_factor': 0
    },
}


def get_density(material: str) -> float:
    for key in CARBON_DATA:
        if key.lower() in str(material).lower():
            return CARBON_DATA[key]['density']
    return 1500.0


def get_carbon_factor(material: str) -> float:
    for key in CARBON_DATA:
        if key.lower() in str(material).lower():
            return CARBON_DATA[key]['carbon_factor']
    return 0.1


def enrich_wall_materials(df: pd.DataFrame) -> pd.DataFrame:
    """Add density, carbon factors, mass, and embodied carbon columns."""
    out = df.copy()
    out['Density_kg_m3'] = out['Material'].apply(get_density)
    out['Carbon_Factor_kgCO2e_kg'] = out['Material'].apply(
        get_carbon_factor
    )
    out['Mass_kg'] = (out['Volume_m3'] * out['Density_kg_m3']).round(2)
    out['Embodied_Carbon_kgCO2e'] = (
        out['Mass_kg'] * out['Carbon_Factor_kgCO2e_kg']
    ).round(2)
    return out


def load_wall_materials_dataframe(
    base_path: str | None = None,
) -> pd.DataFrame:
    """Read ``wall_materials.csv`` and return enriched rows."""
    root = base_path if base_path is not None else BASE_PATH
    path = root + "wall_materials.csv"
    raw = pd.read_csv(path)
    return enrich_wall_materials(raw)


def material_carbon_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate volume, mass, and embodied carbon by material name."""
    return df.groupby('Material', as_index=False).agg(
        Volume_m3=('Volume_m3', 'sum'),
        Mass_kg=('Mass_kg', 'sum'),
        Embodied_Carbon_kgCO2e=('Embodied_Carbon_kgCO2e', 'sum'),
    ).round(2).sort_values(
        'Embodied_Carbon_kgCO2e', ascending=False
    )


def export_processed(df: pd.DataFrame, base_path: str | None = None) -> str:
    """Write enriched table to ``wall_materials_processed.csv``."""
    root = base_path if base_path is not None else BASE_PATH
    out_path = root + "wall_materials_processed.csv"
    df.to_csv(out_path, index=False)
    return out_path


if __name__ == "__main__":
    df = load_wall_materials_dataframe()
    print(f"Total rows: {len(df)}")
    print(df.head())
    print(f"\nUnique materials: {df['Material'].unique()}")

    print("\n--- EMBODIED CARBON SUMMARY ---")
    print(f"Total Volume: {df['Volume_m3'].sum():.2f} m³")
    print(f"Total Mass: {df['Mass_kg'].sum():.0f} kg")
    total_c = df['Embodied_Carbon_kgCO2e'].sum()
    print(f"Total Embodied Carbon: {total_c:.0f} kgCO2e")
    print(f"Total Embodied Carbon: {total_c/1000:.1f} tCO2e")

    print("\nBy Material:")
    print(material_carbon_summary(df))

    export_processed(df)
    print("\nExported successfully")
