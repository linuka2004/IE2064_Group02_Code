import time
import multiprocessing
import threading
import concurrent.futures
import matplotlib.pyplot as plt 

# ==========================================
# CORE TASK: PRIME NUMBER CALCULATION
# (A pure Python CPU-bound task that respects the GIL)
# ==========================================
def compute_heavy_task(n):
    """Calculates prime numbers up to n. Highly CPU intensive."""
    count = 0
    for num in range(2, n):
        is_prime = True
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                is_prime = False
                break
        if is_prime:
            count += 1
    return count

# Wrapper needed for the multiprocessing/threading map function
def compute_wrapper(n):
    compute_heavy_task(n) 

# ==========================================
# EXECUTION MODELS
# ==========================================
def run_sequential(task_size, num_tasks):
    start_time = time.time()
    for _ in range(num_tasks):
        compute_heavy_task(task_size)
    return time.time() - start_time

def run_threading(task_size, num_tasks, num_threads):
    """
    Fixed: Uses ThreadPoolExecutor to properly distribute the 16 tasks 
    across the available threads, ensuring the total workload is equal to sequential.
    """
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        # list() is used to force the executor to actually run the mapped functions
        list(executor.map(compute_wrapper, [task_size] * num_tasks))
    return time.time() - start_time

def run_multiprocessing(task_size, num_tasks, num_processes):
    start_time = time.time()
    # Use a multiprocessing Pool to map the task across true CPU cores
    with multiprocessing.Pool(processes=num_processes) as pool:
        pool.map(compute_wrapper, [task_size] * num_tasks)
    return time.time() - start_time

# ==========================================
# EVALUATION & OUTPUT LOGIC
# ==========================================
def run_module_1():
    task_size = 300000  
    num_tasks = 16      # Total operations to perform
    processor_counts = [1, 2, 4, 8]

    print("\n" + "="*75)
    print("MODULE 1: PARALLELISM BENCHMARK".center(75))
    print("Starting Performance Evaluation...")
    print("Please wait, this will take about 20-40 seconds to crunch the heavy numbers...")
    print("-" * 75)
    print(f"{'Configuration':<15} | {'Sequential Time':<17} | {'Threading Time':<17} | {'Multiprocess Time':<17}")
    print("-" * 75)

    # 1. Get the baseline Sequential Time
    seq_time = run_sequential(task_size, num_tasks)
    
    thread_times = []
    mp_times = []
    
    thread_speedups = []
    mp_speedups = []
    
    thread_efficiencies = []
    mp_efficiencies = []

    # 2. Loop through the required processor configurations
    for procs in processor_counts:
        t_time = run_threading(task_size, num_tasks, procs)
        mp_time = run_multiprocessing(task_size, num_tasks, procs)
        
        thread_times.append(t_time)
        mp_times.append(mp_time)
        
        # Calculate Speedup and Efficiency
        t_speedup = seq_time / t_time
        mp_speedup = seq_time / mp_time
        
        t_eff = (t_speedup / procs) * 100
        mp_eff = (mp_speedup / procs) * 100
        
        thread_speedups.append(t_speedup)
        mp_speedups.append(mp_speedup)
        
        thread_efficiencies.append(t_eff)
        mp_efficiencies.append(mp_eff)
        
        config_label = f"{procs} Worker{'s' if procs > 1 else ' '}"
        print(f"{config_label:<15} | {seq_time:>13.4f} sec | {t_time:>13.4f} sec | {mp_time:>13.4f} sec")
        
    print("-" * 75)
    print("Graphing results... Close the window to continue.")
    
    # Generate Matplotlib Visualization
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Module 1: Threading vs. Multiprocessing - CPU Bound Task (GIL Demonstration)")
    
    # Plot 1: Execution Time
    ax1.plot(processor_counts, thread_times, marker='o', color='tab:red', label='Threading (GIL Bound)')
    ax1.plot(processor_counts, mp_times, marker='s', color='tab:blue', label='Multiprocessing')
    ax1.axhline(y=seq_time, color='gray', linestyle='--', label=f'Sequential ({seq_time:.2f}s)')
    ax1.set_title('Figure 1: Execution Time vs. Workers')
    ax1.set_xlabel('Number of Workers')
    ax1.set_ylabel('Time (seconds)')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # Plot 2: Speedup
    ax2.plot(processor_counts, thread_speedups, marker='o', color='tab:red', label='Threading')
    ax2.plot(processor_counts, mp_speedups, marker='s', color='tab:blue', label='Multiprocessing')
    ax2.plot(processor_counts, processor_counts, linestyle='--', color='green', label='Ideal Speedup')
    ax2.set_title('Figure 2: Speedup vs. Workers')
    ax2.set_xlabel('Number of Workers')
    ax2.set_ylabel('Speedup')
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    # Plot 3: Efficiency
    ax3.plot(processor_counts, thread_efficiencies, marker='o', color='tab:red', label='Threading')
    ax3.plot(processor_counts, mp_efficiencies, marker='s', color='tab:blue', label='Multiprocessing')
    ax3.axhline(y=100, color='gray', linestyle='--', label='Ideal 100%')
    ax3.set_title('Figure 3: Efficiency vs. Workers')
    ax3.set_xlabel('Number of Workers')
    ax3.set_ylabel('Efficiency (%)')
    ax3.legend()
    ax3.set_ylim(-5, 110)
    ax3.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    # Bring window to front
    try:
        fig.canvas.manager.window.attributes('-topmost', 1)
        fig.canvas.manager.window.attributes('-topmost', 0)
    except:
        pass # In case the backend doesn't support these attributes
        
    plt.show()

    print("Module 1 Evaluation Complete!\n")

if __name__ == '__main__':
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    run_module_1()