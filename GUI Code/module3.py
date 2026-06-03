import time
import multiprocessing
import matplotlib.pyplot as plt
# ==========================================
# SHARED BUS SIMULATION
# ==========================================
def worker_bus(bus_lock, accesses):
    """Simulates a processor continually requesting access to a shared bus."""
    for _ in range(accesses):
        # Arbitration: Aquiring the lock
        with bus_lock:
            # Simulate slight delay representing data transfer over the bus
            pass

def run_bus_simulation(num_processors, total_accesses):
    bus_lock = multiprocessing.Lock()
    
    # Divide total bus transactions evenly among processors
    accesses_per_proc = total_accesses // num_processors
    
    processes = []
    start_time = time.time()
    for _ in range(num_processors):
        p = multiprocessing.Process(target=worker_bus, args=(bus_lock, accesses_per_proc))
        processes.append(p)
        p.start()
        
    for p in processes:
        p.join()
        
    return time.time() - start_time

# ==========================================
# EVALUATION & OUTPUT LOGIC
# ==========================================
def run_module_3():
    total_accesses = 200000 # Total number of bus accesses simulating a large payload
    processor_counts = [1, 2, 4, 8]

    print("\n" + "="*75)
    print("MODULE 3: BUS CONTENTION & ARBITRATION".center(75))
    print("Simulating shared bus constraints using Multiprocessing Locks...")
    print("-" * 75)
    print(f"{'Processors':<15} | {'Total Time':<15} | {'Observation'}")
    print("-" * 75)

    base_time = None
    times = []
    overheads = []
    speedups = []

    for procs in processor_counts:
        sim_time = run_bus_simulation(procs, total_accesses)
        times.append(sim_time)
        
        if base_time is None:
            base_time = sim_time
            obs = "Baseline (No Contention)"
            ratio = 1.0
            speedup = 1.0
        else:
            ratio = sim_time / base_time
            # Speedup for bus simulation (should be near 1, ideally wouldn't slowdown)
            speedup = base_time / sim_time
            if ratio > 1.2:
                obs = f"Contention Overhead! ({ratio:.2f}x slower)"
            else:
                obs = "Minimal Contention"
                
        overheads.append(ratio)
        speedups.append(speedup)
        
        print(f"{procs:<15} | {sim_time:>10.4f} sec  | {obs}")
        
    print("-" * 75)
    print("Insight: Shared bus architectures suffer from severe bottlenecking")
    print("as processor count scales, validating the need for Crossbar Switches.")
    print("Graphing results... Close the window to continue.")
    
    # Generate Matplotlib Visualization
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Module 3: Bus Contention & Arbitration")
    
    # Plot 1: Execution Time
    ax1.plot(processor_counts, times, marker='o', color='tab:red', label='Bus Contention Time')
    ax1.axhline(y=base_time, color='gray', linestyle='--', label=f'Baseline ({base_time:.4f}s)')
    ax1.set_title('Figure 1: Execution Time vs. Processors')
    ax1.set_xlabel('Number of Processors')
    ax1.set_ylabel('Time (seconds)')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # Plot 2: Speedup (Actually Expected to Drop)
    ax2.plot(processor_counts, speedups, marker='s', color='tab:blue', label='Actual "Speedup"')
    ax2.axhline(y=1.0, color='gray', linestyle='--', label='Ideal (No Contention)')
    ax2.set_title('Figure 2: Performance Scalability')
    ax2.set_xlabel('Number of Processors')
    ax2.set_ylabel('Speedup (Base Time / Sim Time)')
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    # Plot 3: Contention Overhead
    ax3.plot(processor_counts, overheads, marker='^', color='tab:orange', label='Overhead Factor')
    ax3.axhline(y=1.0, color='gray', linestyle='--', label='1.0x (No Overhead)')
    ax3.set_title('Figure 3: Contention Overhead vs. Processors')
    ax3.set_xlabel('Number of Processors')
    ax3.set_ylabel('Overhead Factor (Sim Time / Base Time)')
    ax3.legend()
    ax3.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    fig.canvas.manager.window.attributes('-topmost', 1)
    fig.canvas.manager.window.attributes('-topmost', 0)
    plt.show()
    
    print("Module 3 Evaluation Complete!\n")
