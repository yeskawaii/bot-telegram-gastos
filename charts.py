# charts.py
import os
import tempfile
import matplotlib.pyplot as plt

def grafica_categorias(fecha_label: str, categorias, montos):
    plt.style.use("seaborn-v0_8")
    colores = [
        "#4e79a7", "#f28e2b", "#e15759", "#76b7b2",
        "#59a14f", "#edc949", "#af7aa1", "#ff9da7",
    ]

    plt.figure(figsize=(8, 5))
    plt.bar(
        categorias,
        montos,
        color=colores[:len(categorias)],
        edgecolor="black",
        linewidth=1,
    )
    plt.title(f"Gastos por categoría – {fecha_label}", fontsize=16, fontweight="bold")
    plt.xlabel("Categoría")
    plt.ylabel("Monto")
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        filename = tmp.name
        plt.savefig(filename, dpi=200)

    plt.close()
    return filename


def grafica_linea_fechas(titulo: str, labels, valores):
    plt.style.use("seaborn-v0_8")

    plt.figure(figsize=(8, 5))
    plt.plot(labels, valores, marker="o", linestyle="-", color="#4e79a7")
    plt.title(titulo, fontsize=16, fontweight="bold")
    plt.xlabel("Día")
    plt.ylabel("Monto")
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        filename = tmp.name
        plt.savefig(filename, dpi=200)

    plt.close()
    return filename
