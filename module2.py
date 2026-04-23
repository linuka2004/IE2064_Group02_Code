import time
import multiprocessing
import random
import matplotlib.pyplot as plt
# ==========================================
# WORKLOAD GENERATION
# ==========================================
# Simulating a heterogeneous "bursty" workload
# Some tasks fall quickly, others take a bit longer
def get_heterogeneous_tasks(num_tasks):
    # Fixed seed for reproducibility so both methods process the same tasks
    random.seed(42)  
    tasks = []
    for _ in range(num_tasks):
        # Heavy tasks are 10x slower than light tasks
        if random.random() < 0.2:
            tasks.append(4000000) # Heavy
        else:
            tasks.append(400000)  # Light
    return tasks

def process_task(task_weight):
    # A simple loop to simulate work
    count = 0
    while count < task_weight:
        count += 1
    return count

# ==========================================
# STATIC LOAD BALANCING
# ==========================================
def worker_static(task_chunk):
    for task in task_chunk:
        process_task(task)

def run_static_scheduling(tasks, num_workers):
    start_time = time.time()
    
    # Division of tasks upfront (Static)
    chunks = [[] for _ in range(num_workers)]
    for i, task in enumerate(tasks):
        chunks[i % num_workers].append(task)
        
    processes = []
    for chunk in chunks:
        p = multiprocessing.Process(target=worker_static, args=(chunk,))
        processes.append(p)
        p.start()
        
    for p in processes:
        p.join()
        
    return time.time() - start_time

# ==========================================
# DYNAMIC LOAD BALANCING
# ==========================================
def worker_dynamic(task_queue):
    while True:
        task = task_queue.get()
        if task is None: # Poison pill to stop
            break
        process_task(task)

def run_dynamic_scheduling(tasks, num_workers):
    start_time = time.time()
    
    # Shared queue for on-demand pulling (Dynamic)
    task_queue = multiprocessing.Queue()
    for task in tasks:
        task_queue.put(task)
        
    # Put poison pills at the end
    for _ in range(num_workers):
        task_queue.put(None)
        
    processes = []
    for _ in range(num_workers):
        p = multiprocessing.Process(target=worker_dynamic, args=(task_queue,))
        processes.append(p)
        p.start()
        
    for p in processes:
        p.join()
        
    return time.time() - start_time

# ==========================================
# EVALUATION & OUTPUT LOGIC
# ==========================================
def run_module_2():
    num_tasks = 40
    processor_counts = [1, 2, 4, 8]
    tasks = get_heterogeneous_tasks(num_tasks)

    print("\n" + "="*75)
    print("MODULE 2: PROCESSOR SCHEDULING (STATIC vs DYNAMIC)".center(75))
    print(f"Total Tasks: {num_tasks} (20% Heavy Burst)")
    print("Simulating computation, please wait...")
    print("-" * 75)
    
    print(f"{'Workers':<10} | {'Static Time':<15} | {'Dynamic Time':<15} | {'Improvement%':<15}")
    print("-" * 75)
    
    static_times = []
    dynamic_times = []
    
    # We will use the 1-worker static time as our 'sequential baseline' for speedup
    base_time = run_static_scheduling(tasks, 1)
    
    static_speedups = []
    dynamic_speedups = []
    static_efficiencies = []
    dynamic_efficiencies = []

    for num_workers in processor_counts:
        # Time measurement
        if num_workers == 1:
            st_time = base_time
        else:
            st_time = run_static_scheduling(tasks, num_workers)
            
        dy_time = run_dynamic_scheduling(tasks, num_workers)
        
        static_times.append(st_time)
        dynamic_times.append(dy_time)
        
        # Speedup relative to 1 static worker
        st_speedup = base_time / st_time
        dy_speedup = base_time / dy_time
        
        static_speedups.append(st_speedup)
        dynamic_speedups.append(dy_speedup)
        
        # Efficiency
        st_eff = (st_speedup / num_workers) * 100
        dy_eff = (dy_speedup / num_workers) * 100
        
        static_efficiencies.append(st_eff)
        dynamic_efficiencies.append(dy_eff)
        
        improvement = ((st_time - dy_time) / st_time) * 100
        print(f"{num_workers:<10} | {st_time:>10.4f} sec  | {dy_time:>10.4f} sec  | {improvement:>10.1f}%")
        
    print("-" * 75)
    print("Insight: Dynamic queue adapts better to heterogeneous workload.")
    print("Graphing results... Close the window to continue.")
    
    # Generate Matplotlib Visualization
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Module 2: Static vs. Dynamic Load Balancing - Heterogeneous Tasks")
    
    # Plot 1: Execution Time
    ax1.plot(processor_counts, static_times, marker='o', color='tab:red', label='Static Scheduling')
    ax1.plot(processor_counts, dynamic_times, marker='s', color='tab:blue', label='Dynamic Scheduling')
    ax1.set_title('Figure 1: Execution Time vs. Workers')
    ax1.set_xlabel('Number of Workers')
    ax1.set_ylabel('Time (seconds)')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # Plot 2: Speedup
    ax2.plot(processor_counts, static_speedups, marker='o', color='tab:red', label='Static Speedup')
    ax2.plot(processor_counts, dynamic_speedups, marker='s', color='tab:blue', label='Dynamic Speedup')
    ax2.plot(processor_counts, processor_counts, linestyle='--', color='green', label='Ideal')
    ax2.set_title('Figure 2: Speedup vs. Workers')
    ax2.set_xlabel('Number of Workers')
    ax2.set_ylabel('Speedup')
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    # Plot 3: Efficiency
    ax3.plot(processor_counts, static_efficiencies, marker='o', color='tab:red', label='Static Efficiency')
    ax3.plot(processor_counts, dynamic_efficiencies, marker='s', color='tab:blue', label='Dynamic Efficiency')
    ax3.axhline(y=100, color='gray', linestyle='--', label='Ideal 100%')
    ax3.set_title('Figure 3: Efficiency vs. Workers')
    ax3.set_xlabel('Number of Workers')
    ax3.set_ylabel('Efficiency (%)')
    ax3.legend()
    ax3.set_ylim(-5, 110)
    ax3.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    fig.canvas.manager.window.attributes('-topmost', 1)
    fig.canvas.manager.window.attributes('-topmost', 0)
    plt.show()

    print("Module 2 Evaluation Complete!\n")
