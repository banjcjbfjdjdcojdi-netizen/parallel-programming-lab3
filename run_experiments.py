import os
import subprocess
import time

SIZES = [200, 400, 800, 1200, 1600, 2000]
PROCS = [1, 2, 4, 8]

# 1. Генерируем все матрицы, если их нет
print("Проверка наличия матриц...")
for n in SIZES:
    path_a = f"data/a_{n}.txt"
    path_b = f"data/b_{n}.txt"
    if not (os.path.exists(path_a) and os.path.exists(path_b)):
        print(f"Генерация матриц {n}x{n}... (это может занять время)")
        with open(path_a, 'w') as fa, open(path_b, 'w') as fb:
            fa.write(f"{n}\n")
            fb.write(f"{n}\n")
            for i in range(n):
                row_a = " ".join(str((i * j) % 10) for j in range(n))
                row_b = " ".join(str((i + j) % 10) for j in range(n))
                fa.write(row_a + "\n")
                fb.write(row_b + "\n")
    else:
        print(f"Матрицы {n}x{n} уже есть.")

print("\nЗапуск экспериментов через SLURM...")

# 2. Создаем скрипты и отправляем в очередь
job_ids = []
for n in SIZES:
    for p in PROCS:
        job_name = f"mpi_{n}_{p}"
        out_file = f"results/c_{n}_{p}.txt"
        log_file = f"slurm_{n}_{p}.log"
        
        # Создаем SLURM скрипт для конкретного запуска
        slurm_script = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks={p}
#SBATCH --partition=batch
#SBATCH --output={log_file}

module load intel/mpi4
mpirun -np {p} ./matrix_mpi --a data/a_{n}.txt --b data/b_{n}.txt --out {out_file}
"""
        script_name = f"job_{n}_{p}.slurm"
        with open(script_name, "w") as f:
            f.write(slurm_script)
        
        # Отправляем в очередь (исправлено под старый Python)
        res = subprocess.run(["sbatch", script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        if res.returncode == 0:
            job_id = res.stdout.strip().split()[-1]
            job_ids.append(job_id)
            print(f"Отправлено: N={n}, procs={p} (Job ID: {job_id})")
        else:
            print(f"Ошибка при отправке N={n}, procs={p}: {res.stderr}")

print(f"\nВсего отправлено {len(job_ids)} заданий.")

# 3. Ждем завершения всех заданий
print("Ожидание завершения заданий (проверка каждые 10 секунд)...")
while True:
    # Исправлено под старый Python
    res = subprocess.run(["squeue", "-u", os.environ.get("USER")], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    
    # Если в выводе только шапка таблицы (1 строка) — значит очередь пуста
    if len(res.stdout.strip().split("\n")) <= 1: 
        print("\nВсе задания выполнены!")
        break
    time.sleep(10)

# 4. Собираем результаты в CSV
print("\nСбор результатов...")
results = []
for n in SIZES:
    for p in PROCS:
        log_file = f"slurm_{n}_{p}.log"
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                for line in f:
                    if line.startswith("size="):
                        parts = dict(item.split("=") for item in line.strip().split())
                        results.append({
                            "size": int(parts["size"]),
                            "procs": int(parts["procs"]),
                            "time": float(parts["time"]),
                            "ops": int(parts["ops"])
                        })

csv_file = "results/bench_mpi.csv"
with open(csv_file, "w") as f:
    f.write("size,procs,time,ops\n")
    for r in results:
        f.write(f"{r['size']},{r['procs']},{r['time']},{r['ops']}\n")

print(f"Готово! Результаты сохранены в {csv_file}")