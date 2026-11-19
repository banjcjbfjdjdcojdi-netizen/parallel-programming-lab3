import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv('results/bench_mpi.csv')

sizes = sorted(df['size'].unique())
procs = sorted(df['procs'].unique())

plt.figure(figsize=(10, 6))
for size in sizes:
    subset = df[df['size'] == size]
    plt.plot(subset['procs'], subset['time'], marker='o', label=f'N={size}')

plt.title('Время выполнения MPI-программы от числа процессов')
plt.xlabel('Количество процессов (MPI)')
plt.ylabel('Время выполнения (сек)')
plt.xscale('log', base=2)
plt.yscale('log')
plt.xticks(procs, [str(p) for p in procs])
plt.grid(True, which="both", ls="--", alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('results/mpi_time_vs_procs.png', dpi=150)
plt.close()

plt.figure(figsize=(10, 6))
for size in sizes:
    subset = df[df['size'] == size].sort_values('procs')
    t1 = subset[subset['procs'] == 1]['time'].values[0]
    speedup = t1 / subset['time'].values
    plt.plot(subset['procs'], speedup, marker='s', label=f'N={size}')

plt.plot(procs, procs, 'k--', label='Идеальное ускорение', alpha=0.5)

plt.title('Ускорение MPI-программы (Speedup)')
plt.xlabel('Количество процессов (MPI)')
plt.ylabel('Ускорение (S = T1 / Tp)')
plt.xscale('log', base=2)
plt.xticks(procs, [str(p) for p in procs])
plt.grid(True, which="both", ls="--", alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('results/mpi_speedup.png', dpi=150)
plt.close()

plt.figure(figsize=(10, 6))
for size in sizes:
    subset = df[df['size'] == size].sort_values('procs')
    t1 = subset[subset['procs'] == 1]['time'].values[0]
    speedup = t1 / subset['time'].values
    efficiency = speedup / subset['procs'].values
    plt.plot(subset['procs'], efficiency * 100, marker='^', label=f'N={size}')

plt.title('Эффективность MPI-программы (Efficiency)')
plt.xlabel('Количество процессов (MPI)')
plt.ylabel('Эффективность (%)')
plt.xscale('log', base=2)
plt.xticks(procs, [str(p) for p in procs])
plt.ylim(0, 110)
plt.grid(True, which="both", ls="--", alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('results/mpi_efficiency.png', dpi=150)
plt.close()

print("Графики успешно построены и сохранены в папку results/")