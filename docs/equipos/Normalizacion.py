import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================
# SCRIPT DE NORMALIZACIÓN, CORRELACIÓN Y ERROR GLOBAL DE MATRICES (84x84)
# Métodos: SIFT2, LiFE y COMMIT
# =============================================================================

# Ruta directa a la carpeta de matrices en Windows
DATA_DIR = r"C:\Users\Pable\Documents\Maestria en modelacion y optimizacion de procesos\1er Semestre\Laboratorio de resolución de problemas 1\Proyecto MSCAN\Desafio 2026\Matrices"

def cargar_matriz(filepath):
    """
    Carga un archivo CSV o XLSX y extrae la submatriz numérica de 84x84.
    Maneja automáticamente encabezados o índices de fila/columna si existen.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext in ['.xlsx', '.xls']:
        df = pd.read_excel(filepath, header=None)
    else:
        df = pd.read_csv(filepath, header=None)
    
    # Extraer los últimos 84 renglones y 84 columnas
    mat = df.iloc[-84:, -84:].values.astype(float)
    return mat

def calcular_errores_globales(m1, m2, nombre1, nombre2):
    """
    Calcula métricas globales de error y distancia matricial entre dos matrices 84x84.
    """
    mse = np.mean((m1 - m2) ** 2)
    rmse = np.sqrt(mse)
    mae = np.mean(np.abs(m1 - m2))
    frob_diff = np.linalg.norm(m1 - m2, 'fro')
    frob_ref = np.linalg.norm(m1, 'fro')
    error_relativo = (frob_diff / frob_ref) * 100 if frob_ref > 0 else 0.0
    
    return {
        'comparacion': f"{nombre1} vs {nombre2}",
        'rmse': rmse,
        'mae': mae,
        'frob_diff': frob_diff,
        'error_relativo_pct': error_relativo
    }

def main():
    # Nombres de los archivos especificados
    f_sift2  = os.path.join(DATA_DIR, 'Connectome_SIFT2_100k.csv')
    f_life   = os.path.join(DATA_DIR, 'conn_life_full.csv')
    f_commit = os.path.join(DATA_DIR, 'matriz_peso_commit_84x84_corregida.xlsx')

    print(f"Cargando matrices desde:\n{DATA_DIR}\n")
    try:
        mat_sift2  = cargar_matriz(f_sift2)
        mat_life   = cargar_matriz(f_life)
        mat_commit = cargar_matriz(f_commit)
    except Exception as e:
        print(f"Error al cargar archivos: {e}")
        print("Asegúrate de tener instalada la librería 'openpyxl' (pip install openpyxl) para abrir el archivo .xlsx.")
        return

    print(f"✓ Dimensiones SIFT2:  {mat_sift2.shape}")
    print(f"✓ Dimensiones LiFE:   {mat_life.shape}")
    print(f"✓ Dimensiones COMMIT: {mat_commit.shape}\n")

    # -------------------------------------------------------------------------
    # 1. NORMALIZACIÓN MIN-MAX [0, 1] Y POR SUMA TOTAL
    # -------------------------------------------------------------------------
    norm_sift2_minmax  = mat_sift2  / np.max(mat_sift2)  if np.max(mat_sift2) > 0 else mat_sift2
    norm_life_minmax   = mat_life   / np.max(mat_life)   if np.max(mat_life) > 0 else mat_life
    norm_commit_minmax = mat_commit / np.max(mat_commit) if np.max(mat_commit) > 0 else mat_commit

    norm_sift2_sum  = mat_sift2  / np.sum(mat_sift2)  if np.sum(mat_sift2) > 0 else mat_sift2
    norm_life_sum   = mat_life   / np.sum(mat_life)   if np.sum(mat_life) > 0 else mat_life
    norm_commit_sum = mat_commit / np.sum(mat_commit) if np.sum(mat_commit) > 0 else mat_commit

    # -------------------------------------------------------------------------
    # 2. DIAGNÓSTICO DE DISPERSIÓN (% DE CEROS)
    # -------------------------------------------------------------------------
    z_sift2  = np.mean(mat_sift2 == 0) * 100
    z_life   = np.mean(mat_life == 0) * 100
    z_commit = np.mean(mat_commit == 0) * 100

    print("=================================================================")
    print(" 1. DIAGNÓSTICO DE DISPERSIÓN (% DE CONEXIONES NULAS)")
    print("=================================================================")
    print(f"  • SIFT2:  {z_sift2:.2f}% de ceros")
    print(f"  • LiFE:   {z_life:.2f}% de ceros")
    print(f"  • COMMIT: {z_commit:.2f}% de ceros\n")

    # -------------------------------------------------------------------------
    # 3. CORRELACIÓN DE PEARSON (TRIÁNGULO SUPERIOR)
    # -------------------------------------------------------------------------
    triu_idx = np.triu_indices(84, k=1)
    v_sift2  = norm_sift2_minmax[triu_idx]
    v_life   = norm_life_minmax[triu_idx]
    v_commit = norm_commit_minmax[triu_idx]

    r_sift2_life   = np.corrcoef(v_sift2, v_life)[0, 1]
    r_sift2_commit = np.corrcoef(v_sift2, v_commit)[0, 1]
    r_life_commit  = np.corrcoef(v_life, v_commit)[0, 1]

    print("=================================================================")
    print(" 2. CORRELACIÓN DE PEARSON (ENTRE LAS 3,486 CONEXIONES ÚNICAS)")
    print("=================================================================")
    print(f"  • SIFT2 vs LiFE:   r = {r_sift2_life:.4f}")
    print(f"  • SIFT2 vs COMMIT: r = {r_sift2_commit:.4f}")
    print(f"  • LiFE vs COMMIT:  r = {r_life_commit:.4f}\n")

    # -------------------------------------------------------------------------
    # 4. ERROR GLOBAL Y DISCREPANCIA MATRICIAL (84x84)
    # -------------------------------------------------------------------------
    err_sift2_life   = calcular_errores_globales(norm_sift2_minmax, norm_life_minmax, "SIFT2", "LiFE")
    err_sift2_commit = calcular_errores_globales(norm_sift2_minmax, norm_commit_minmax, "SIFT2", "COMMIT")
    err_life_commit  = calcular_errores_globales(norm_life_minmax, norm_commit_minmax, "LiFE", "COMMIT")

    print("=================================================================")
    print(" 3. ERROR GLOBAL Y DISCREPANCIA MATRICIAL (SOBRE REGIONES 84x84)")
    print("=================================================================")
    for err in [err_sift2_life, err_sift2_commit, err_life_commit]:
        print(f"  • {err['comparacion']}:")
        print(f"     - RMSE (Root Mean Squared Error):  {err['rmse']:.6f}")
        print(f"     - MAE  (Mean Absolute Error):       {err['mae']:.6f}")
        print(f"     - Norma de Frobenius (Diferencia): {err['frob_diff']:.6f}")
        print(f"     - Error Relativo Global:           {err['error_relativo_pct']:.2f}%\n")

    # -------------------------------------------------------------------------
    # 5. GUARDAR MATRICES NORMALIZADAS EN LA CARPETA DE MATRICES
    # -------------------------------------------------------------------------
    out_sift2  = os.path.join(DATA_DIR, 'SIFT2_minmax.csv')
    out_life   = os.path.join(DATA_DIR, 'LiFE_minmax.csv')
    out_commit = os.path.join(DATA_DIR, 'COMMIT_minmax.csv')
    
    pd.DataFrame(norm_sift2_minmax).to_csv(out_sift2, index=False, header=False)
    pd.DataFrame(norm_life_minmax).to_csv(out_life, index=False, header=False)
    pd.DataFrame(norm_commit_minmax).to_csv(out_commit, index=False, header=False)
    print("✓ Matrices normalizadas (Min-Max) guardadas en la carpeta Matrices.")

    # -------------------------------------------------------------------------
    # 6. MAPAS DE CALOR COMPARATIVOS (HEATMAPS)
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    im0 = axes[0].imshow(norm_sift2_minmax, cmap='hot', vmin=0, vmax=1)
    axes[0].set_title("SIFT2 (Normalizado Min-Max)")
    axes[0].set_xlabel("Regiones (0-83)")
    axes[0].set_ylabel("Regiones (0-83)")
    plt.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)

    im1 = axes[1].imshow(norm_life_minmax, cmap='hot', vmin=0, vmax=1)
    axes[1].set_title("LiFE (Normalizado Min-Max)")
    axes[1].set_xlabel("Regiones (0-83)")
    plt.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)

    im2 = axes[2].imshow(norm_commit_minmax, cmap='hot', vmin=0, vmax=1)
    axes[2].set_title("COMMIT (Normalizado Min-Max)")
    axes[2].set_xlabel("Regiones (0-83)")
    plt.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)

    plt.suptitle("Comparativa de Matrices de Conectividad ESTRUCTURAL (84x84)", fontsize=16, y=1.02)
    plt.tight_layout()
    
    out_plot = os.path.join(DATA_DIR, 'heatmaps_comparativos.png')
    plt.savefig(out_plot, dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Gráfico 'heatmaps_comparativos.png' guardado exitosamente.\n")

if __name__ == '__main__':
    main()
