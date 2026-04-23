import time
import multiprocessing
import matplotlib.pyplot as plt

# ==========================================
# WORKLOAD
# ==========================================
def dummy_work(n):
    # Pure CPU loop
    c = 0
    while c < n:
        c += 1
    return c

def map_dummy_work(args):
    return dummy_work(args)

def run_workload(procs, task_size, num_tasks):
    start = time.time()
    with multiprocessing.Pool(processes=procs) as pool:
        pool.map(map_dummy_work, [task_size] * num_tasks)
    return time.time() - start

# ==========================================
# EVALUATION & OUTPUT LOGIC
# ==========================================
def run_module_5():
    processor_counts = [1, 2, 4, 8]
    task_size = 2000000
    num_tasks = 16
    
    print("\n" + "="*75)
    print("MODULE 5: PERFORMANCE EVALUATION ENGINE (AMDAHL'S LAW)".center(75))
    print("Capturing telemetry and rendering visualizations...")
    print("-" * 75)
    
    times = []
    speedups = []
    efficiencies = []
    
    base_time = None
    
    for procs in processor_counts:
        t = run_workload(procs, task_size, num_tasks)
        times.append(t)
        
        if base_time is None:
            base_time = t
            speedup = 1.0
        else:
            speedup = base_time / t
            
        efficiency = (speedup / procs) * 100
        
        speedups.append(speedup)
        efficiencies.append(efficiency)
        
        print(f"Processors: {procs:2d} | Time: {t:.4f}s | Speedup: {speedup:.2f}x | Efficiency: {efficiency:.1f}%")

    print("-" * 75)
    print("Displaying Graph. Close the window to continue.")
    
    # Generate Matplotlib Visualisation
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Module 5: Performance Evaluation Engine (Amdahl's Law)")
    
    # Plot 1: Execution Time
    ax1.plot(processor_counts, times, marker='o', color='tab:green', label='Execution Time')
    if base_time is not None:
        ax1.axhline(y=base_time, color='gray', linestyle='--', label=f'Sequential ({base_time:.2f}s)')
    ax1.set_title('Figure 1: Execution Time vs. Processors')
    ax1.set_xlabel('Number of Processors')
    ax1.set_ylabel('Time (seconds)')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # Plot 2: Speedup
    ax2.plot(processor_counts, speedups, marker='o', color='tab:blue', label='Actual Speedup')
    ax2.plot(processor_counts, processor_counts, linestyle='--', color='gray', label='Linear (Ideal)')
    ax2.set_title('Figure 2: Speedup vs. Processors')
    ax2.set_xlabel('Number of Processors')
    ax2.set_ylabel('Speedup')
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    # Plot 3: Efficiency
    ax3.plot(processor_counts, efficiencies, marker='s', color='tab:red')
    ax3.axhline(y=100, color='gray', linestyle='--', label='Ideal 100%')
    ax3.set_title('Figure 3: Efficiency vs. Processors')
    ax3.set_xlabel('Number of Processors')
    ax3.set_ylabel('Efficiency (%)')
    ax3.legend()
    ax3.set_ylim(0, 110)
    ax3.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    # Bring window to the front
    fig.canvas.manager.window.attributes('-topmost', 1)
    fig.canvas.manager.window.attributes('-topmost', 0)
    plt.show()
    
    print("Module 5 Evaluation Complete!\n")
